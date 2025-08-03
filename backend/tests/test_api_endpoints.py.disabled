"""
Tests for main API endpoints
"""

import pytest
import json
from unittest.mock import patch, Mock
from models import db, User, Word, UserVocabulary, Category, Settings


class TestAuthenticationEndpoints:
    """Test authentication API endpoints"""

    def test_register_success(self, client, db_session):
        """Test successful user registration"""
        user_data = {"username": "newuser", "password": "password123"}

        response = client.post(
            "/api/auth/register",
            data=json.dumps(user_data),
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["message"] == "User registered successfully"
        assert "access_token" in data
        assert "user" in data

        # Verify user was created in database
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.check_password("password123")

    def test_register_duplicate_username(self, client, db_session):
        """Test registration with existing username"""
        # Create existing user
        existing_user = User(username="existing")
        existing_user.set_password("password")
        db_session.add(existing_user)
        db_session.commit()

        user_data = {"username": "existing", "password": "newpassword"}

        response = client.post(
            "/api/auth/register",
            data=json.dumps(user_data),
            content_type="application/json",
        )

        assert response.status_code == 409
        data = json.loads(response.data)
        assert "already exists" in data["error"].lower()

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        # Missing password
        response = client.post(
            "/api/auth/register",
            data=json.dumps({"username": "test"}),
            content_type="application/json",
        )

        assert response.status_code == 400

        # Missing username
        response = client.post(
            "/api/auth/register",
            data=json.dumps({"password": "test"}),
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_login_success(self, client, db_session):
        """Test successful login"""
        # Create test user
        user = User(username="loginuser")
        user.set_password("password123")
        db_session.add(user)
        db_session.commit()

        login_data = {"username": "loginuser", "password": "password123"}

        response = client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "access_token" in data
        assert "user" in data

    def test_login_invalid_credentials(self, client, db_session):
        """Test login with invalid credentials"""
        # Create test user
        user = User(username="loginuser")
        user.set_password("password123")
        db_session.add(user)
        db_session.commit()

        # Wrong password
        login_data = {"username": "loginuser", "password": "wrongpassword"}

        response = client.post(
            "/api/auth/login",
            data=json.dumps(login_data),
            content_type="application/json",
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "invalid" in data["error"].lower()

    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "user" in data
        assert data["user"]["username"] == "testuser"


class TestVocabularyEndpoints:
    """Test vocabulary management endpoints"""

    def test_get_categories(self, client, auth_headers):
        """Test getting categories"""
        response = client.get("/api/categories", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0

        # Check category structure
        category = data[0]
        assert "id" in category
        assert "name" in category
        assert "top_100_count" in category

    def test_search_words_existing(self, client, auth_headers, db_session):
        """Test searching for existing words"""
        # Create test word
        category = Category.query.first()
        word = Word(
            serbian_word="тест", english_translation="test", category_id=category.id
        )
        db_session.add(word)
        db_session.commit()

        response = client.get("/api/words/search?q=тест", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["has_results"] is True
        assert len(data["all_results"]) > 0
        assert data["all_results"][0]["serbian_word"] == "тест"

    def test_search_words_not_found(self, client, auth_headers):
        """Test searching for non-existent words"""
        response = client.get(
            "/api/words/search?q=nonexistentword", headers=auth_headers
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["has_results"] is False
        assert "suggestion" in data

    def test_add_words_success(self, client, auth_headers):
        """Test successfully adding words"""
        words_data = {
            "words": [
                {
                    "serbian_word": "нови",
                    "english_translation": "new",
                    "category_id": 1,
                },
                {
                    "serbian_word": "стари",
                    "english_translation": "old",
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

    def test_add_words_validation(self, client, auth_headers):
        """Test word addition validation"""
        # Empty words array
        response = client.post(
            "/api/words",
            data=json.dumps({"words": []}),
            content_type="application/json",
            headers=auth_headers,
        )
        assert response.status_code == 400

        # Missing required fields
        words_data = {
            "words": [
                {
                    "serbian_word": "тест"
                    # Missing english_translation
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
        # Word should be skipped due to missing translation
        assert data["inserted"] == 0

    def test_add_suggested_word(self, client, auth_headers):
        """Test adding a suggested word"""
        word_data = {
            "serbian_word": "предлог",
            "english_translation": "suggestion",
            "category_id": 1,
            "context": "Test context",
        }

        response = client.post(
            "/api/words/add-suggested",
            data=json.dumps(word_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["word"]["serbian_word"] == "предлог"

    def test_get_user_words(self, client, auth_headers, db_session):
        """Test getting user's vocabulary words"""
        # Add word to user's vocabulary
        user = User.query.filter_by(username="testuser").first()
        category = Category.query.first()
        word = Word(
            serbian_word="кориснички",
            english_translation="user",
            category_id=category.id,
        )
        db_session.add(word)
        db_session.flush()

        user_vocab = UserVocabulary(user_id=user.id, word_id=word.id)
        db_session.add(user_vocab)
        db_session.commit()

        response = client.get("/api/words", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

        # Find our word
        user_word = next((w for w in data if w["serbian_word"] == "кориснички"), None)
        assert user_word is not None
        assert user_word["is_in_vocabulary"] is True


class TestPracticeEndpoints:
    """Test practice session endpoints"""

    def test_get_practice_words(self, client, auth_headers, db_session):
        """Test getting words for practice"""
        # Add some words to user's vocabulary
        user = User.query.filter_by(username="testuser").first()
        category = Category.query.first()

        for i in range(3):
            word = Word(
                serbian_word=f"реч{i}",
                english_translation=f"word{i}",
                category_id=category.id,
            )
            db_session.add(word)
            db_session.flush()

            user_vocab = UserVocabulary(user_id=user.id, word_id=word.id)
            db_session.add(user_vocab)

        db_session.commit()

        response = client.get("/api/practice/words?limit=5", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0

        # Check practice word structure
        practice_word = data[0]
        assert "question" in practice_word
        assert "options" in practice_word
        assert "correct_answer" in practice_word
        assert "game_mode" in practice_word

    def test_start_practice_session(self, client, auth_headers):
        """Test starting a practice session"""
        response = client.post("/api/practice/start", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "id" in data
        assert "session_date" in data

    @patch("services.sentence_cache.SentenceCacheService.get_random_sentence")
    def test_generate_example_sentence(self, mock_get_sentence, client, auth_headers):
        """Test generating example sentences"""
        # Mock cached sentence
        mock_get_sentence.return_value = {
            "serbian": "Ovo je primer rečenice.",
            "english": "This is an example sentence.",
        }

        sentence_data = {"serbian_word": "пример", "english_translation": "example"}

        response = client.post(
            "/api/practice/example-sentence",
            data=json.dumps(sentence_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "sentence" in data
        assert data["from_cache"] is True

    def test_submit_practice_result(self, client, auth_headers, db_session):
        """Test submitting practice results"""
        # Create practice session
        from models import PracticeSession

        user = User.query.filter_by(username="testuser").first()
        session = PracticeSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        # Create word for practice
        category = Category.query.first()
        word = Word(
            serbian_word="резултат",
            english_translation="result",
            category_id=category.id,
        )
        db_session.add(word)
        db_session.flush()

        user_vocab = UserVocabulary(user_id=user.id, word_id=word.id)
        db_session.add(user_vocab)
        db_session.commit()

        # Submit result
        result_data = {
            "session_id": session.id,
            "word_id": word.id,
            "was_correct": True,
            "response_time_seconds": 5.2,
        }

        response = client.post(
            "/api/practice/submit",
            data=json.dumps(result_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True


class TestSettingsEndpoints:
    """Test user settings endpoints"""

    def test_get_settings(self, client, auth_headers, db_session):
        """Test getting user settings"""
        # Create settings for test user
        user = User.query.filter_by(username="testuser").first()
        settings = Settings(
            user_id=user.id,
            openai_api_key="test-key",
            auto_advance_enabled=True,
            mastery_threshold=5,
        )
        db_session.add(settings)
        db_session.commit()

        response = client.get("/api/settings", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "settings" in data
        settings_data = data["settings"]
        assert settings_data["auto_advance_enabled"] is True
        assert settings_data["mastery_threshold"] == 5

    def test_update_settings(self, client, auth_headers, db_session):
        """Test updating user settings"""
        settings_data = {
            "auto_advance_enabled": False,
            "auto_advance_timeout": 3,
            "mastery_threshold": 7,
            "practice_round_count": 15,
        }

        response = client.put(
            "/api/settings",
            data=json.dumps(settings_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["message"] == "Settings updated successfully"

        # Verify settings were updated
        user = User.query.filter_by(username="testuser").first()
        settings = user.settings
        assert settings.auto_advance_enabled is False
        assert settings.auto_advance_timeout == 3
        assert settings.mastery_threshold == 7
        assert settings.practice_round_count == 15

    def test_update_settings_validation(self, client, auth_headers):
        """Test settings update validation"""
        # Invalid mastery threshold
        settings_data = {
            "mastery_threshold": 15  # Too high (max is 10)
        }

        response = client.put(
            "/api/settings",
            data=json.dumps(settings_data),
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "mastery threshold" in data["error"].lower()


class TestStatsEndpoints:
    """Test statistics endpoints"""

    def test_get_user_stats(self, client, auth_headers, db_session):
        """Test getting user statistics"""
        response = client.get("/api/stats", headers=auth_headers)

        assert response.status_code == 200
        data = json.loads(response.data)

        assert "total_words" in data
        assert "user_vocabulary_count" in data
        assert "learned_words" in data
        assert "mastered_words" in data
        assert "recent_sessions" in data

        # All should be non-negative integers
        assert data["total_words"] >= 0
        assert data["user_vocabulary_count"] >= 0
        assert data["learned_words"] >= 0
        assert data["mastered_words"] >= 0
        assert isinstance(data["recent_sessions"], list)


class TestErrorHandling:
    """Test API error handling"""

    def test_unauthorized_access(self, client):
        """Test accessing protected endpoints without authentication"""
        protected_endpoints = [
            "/api/words",
            "/api/practice/words",
            "/api/settings",
            "/api/stats",
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_invalid_json(self, client, auth_headers):
        """Test sending invalid JSON"""
        response = client.post(
            "/api/words",
            data="invalid json",
            content_type="application/json",
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_missing_content_type(self, client, auth_headers):
        """Test missing content type header"""
        response = client.post(
            "/api/words", data=json.dumps({"words": []}), headers=auth_headers
        )

        # Should still work as Flask can parse JSON without explicit content-type
        assert response.status_code in [200, 400]  # Either works or fails validation

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"
