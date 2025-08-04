"""
Essential tests for core functionality
"""

import json
from unittest.mock import MagicMock, patch

from flask_jwt_extended import create_access_token
import pytest

from models import Category, User, UserVocabulary, Word, db


@pytest.fixture
def auth_headers(app):
    """Create authentication headers for test user"""
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        if not user:
            # Create test user if it doesn't exist
            user = User(username="testuser")
            user.set_password("testpassword")
            db.session.add(user)
            db.session.commit()
        access_token = create_access_token(identity=str(user.id))
        return {"Authorization": f"Bearer {access_token}"}


class TestModels:
    """Essential model tests"""

    def test_user_password_hashing(self, db_session):
        """Test password hashing and verification"""
        user = User(username="testuser")
        password = "testpass123"

        user.set_password(password)

        assert user.password_hash != password
        assert user.check_password(password) is True
        assert user.check_password("wrongpass") is False

    def test_word_creation_and_serialization(self, db_session):
        """Test word creation and to_dict method"""
        category = Category(name="Test Category")
        db_session.add(category)
        db_session.flush()

        word = Word(
            serbian_word="testword",
            english_translation="testword",
            category_id=category.id,
        )
        db_session.add(word)
        db_session.commit()

        assert word.id is not None

        word_dict = word.to_dict()
        assert word_dict["serbian_word"] == "testword"
        assert word_dict["english_translation"] == "testword"
        assert word_dict["category_name"] == "Test Category"

    def test_user_vocabulary_relationship(self, db_session):
        """Test user vocabulary relationships"""
        user = User(username="vocabuser")
        user.set_password("pass")
        db_session.add(user)

        category = Category(name="Test")
        db_session.add(category)
        db_session.flush()

        word = Word(serbian_word="test", english_translation="test", category_id=category.id)
        db_session.add(word)
        db_session.flush()

        vocab = UserVocabulary(user_id=user.id, word_id=word.id)
        db_session.add(vocab)
        db_session.commit()

        assert vocab.user_id == user.id
        assert vocab.word_id == word.id


class TestAddWords:
    """Essential add words tests"""

    def test_add_words_success(self, app, client, auth_headers):
        """Test successful addition of new words"""
        words_data = {
            "words": [
                {
                    "serbian_word": "kuća",
                    "english_translation": "house",
                    "category_id": 1,
                },
                {
                    "serbian_word": "auto",
                    "english_translation": "car",
                    "category_id": 1,
                },
            ]
        }

        response = client.post(
            "/api/words",
            data=json.dumps(words_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["inserted"] == 2
        assert data["added_to_vocabulary"] == 2
        assert len(data["words"]) == 2

    def test_add_words_duplicate_handling(self, app, client, auth_headers):
        """Test handling of duplicate words"""
        with app.app_context():
            word = Word(serbian_word="kuća", english_translation="house", category_id=1)
            db.session.add(word)
            db.session.commit()

        words_data = {
            "words": [
                {
                    "serbian_word": "kuća",
                    "english_translation": "house",
                    "category_id": 1,
                }
            ]
        }

        response = client.post(
            "/api/words",
            data=json.dumps(words_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)

        assert data["success"] is True
        assert data["inserted"] == 0  # No new words created
        assert data["added_to_vocabulary"] == 1  # Existing word added to vocabulary

    def test_add_words_validation(self, client, auth_headers):
        """Test input validation"""
        # Test empty words array
        response = client.post(
            "/api/words",
            data=json.dumps({"words": []}),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 400

        # Test missing authentication
        response = client.post(
            "/api/words",
            data=json.dumps({"words": [{"serbian_word": "test", "english_translation": "test"}]}),
            content_type="application/json",
        )
        assert response.status_code == 401


class TestTextProcessor:
    """Essential text processor tests"""

    @patch("services.text_processor.openai")
    def test_process_text_success(self, mock_openai, text_processor, sample_categories):
        """Test successful text processing"""
        mock_response = {
            "processed_words": [
                {
                    "serbian_word": "raditi",
                    "english_translation": "to work",
                    "category": "Verbs",
                    "original_form": "radim",
                }
            ],
            "filtering_summary": {"total_raw_words": 5, "processed_words": 1},
        }

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message = {"content": json.dumps(mock_response)}
        mock_openai.ChatCompletion.create.return_value = mock_completion

        result = text_processor.process_text("Radim u kući.", sample_categories)

        assert result["total_words"] == 5
        assert result["new_words"] == 1
        assert len(result["translations"]) == 1
        assert result["translations"][0]["serbian_word"] == "raditi"

    def test_process_text_empty_input(self, text_processor, sample_categories):
        """Test processing empty text"""
        result = text_processor.process_text("", sample_categories)

        assert result["processed_words"] == []
        assert result["filtering_summary"]["total_raw_words"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
