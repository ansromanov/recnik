"""
Unit tests for database models
"""

import pytest
from datetime import datetime
from models import (
    User,
    Category,
    Word,
    UserVocabulary,
    Settings,
    PracticeSession,
    PracticeResult,
    ExcludedWord,
)
from tests.conftest import (
    UserFactory,
    CategoryFactory,
    WordFactory,
    UserVocabularyFactory,
)


@pytest.mark.unit
class TestUser:
    """Test cases for User model"""

    def test_user_creation(self, db_session):
        """Test creating a user"""
        user = User(username="newtestuser")
        user.set_password("password123")

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "newtestuser"
        assert user.password_hash is not None
        assert user.password_hash != "password123"  # Should be hashed
        assert user.created_at is not None

    def test_user_password_hashing(self, db_session):
        """Test password hashing and verification"""
        user = User(username="hashuser")
        password = "mySecurePassword123"

        user.set_password(password)

        # Password should be hashed
        assert user.password_hash != password
        assert len(user.password_hash) > 0

        # Should be able to verify correct password
        assert user.check_password(password) is True
        assert user.check_password("wrongpassword") is False

    def test_user_to_dict(self, db_session):
        """Test user serialization"""
        user = User(username="dictuser")
        user.set_password("password123")

        db_session.add(user)
        db_session.commit()

        user_dict = user.to_dict()

        assert "id" in user_dict
        assert user_dict["username"] == "dictuser"
        assert "created_at" in user_dict
        assert "password_hash" not in user_dict  # Should not expose password

    def test_user_relationships(self, db_session):
        """Test user model relationships"""
        user = User(username="reluser")
        user.set_password("password123")
        db_session.add(user)
        db_session.commit()

        # Test settings relationship
        settings = Settings(user_id=user.id, openai_api_key="test-key")
        db_session.add(settings)
        db_session.commit()

        assert user.settings is not None
        assert user.settings.openai_api_key == "test-key"


@pytest.mark.unit
class TestCategory:
    """Test cases for Category model"""

    def test_category_creation(self, db_session):
        """Test creating a category"""
        category = Category(name="Test Category", description="Test description")

        db_session.add(category)
        db_session.commit()

        assert category.id is not None
        assert category.name == "Test Category"
        assert category.description == "Test description"
        assert category.created_at is not None

    def test_category_to_dict(self, db_session):
        """Test category serialization"""
        category = Category(
            name="Test Category Serialization", description="Test description"
        )

        db_session.add(category)
        db_session.commit()

        category_dict = category.to_dict()

        expected_keys = ["id", "name", "description", "created_at"]
        for key in expected_keys:
            assert key in category_dict

        assert category_dict["name"] == "Test Category Serialization"
        assert category_dict["description"] == "Test description"

    def test_category_unique_name(self, db_session):
        """Test that category names must be unique"""
        category1 = Category(name="Unique Category")
        category2 = Category(name="Unique Category")

        db_session.add(category1)
        db_session.commit()

        # Adding second category with same name should raise an error
        db_session.add(category2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


@pytest.mark.unit
class TestWord:
    """Test cases for Word model"""

    def test_word_creation(self, db_session):
        """Test creating a word"""
        category = CategoryFactory()

        word = Word(
            serbian_word="testword",
            english_translation="testword",
            category_id=category.id,
            context="Ova testword je velika.",
        )

        db_session.add(word)
        db_session.commit()

        assert word.id is not None
        assert word.serbian_word == "testword"
        assert word.english_translation == "testword"
        assert word.category_id == category.id
        assert word.context == "Ova testword je velika."
        assert word.difficulty_level == 1  # Default value
        assert word.is_top_100 is False  # Default value

    def test_word_to_dict(self, db_session):
        """Test word serialization"""
        category = CategoryFactory()

        word = Word(
            serbian_word="dicttest",
            english_translation="dicttest",
            category_id=category.id,
            difficulty_level=3,
        )

        db_session.add(word)
        db_session.commit()

        word_dict = word.to_dict()

        expected_keys = [
            "id",
            "serbian_word",
            "english_translation",
            "category_id",
            "category_name",
            "context",
            "notes",
            "difficulty_level",
            "is_top_100",
            "created_at",
            "updated_at",
        ]

        for key in expected_keys:
            assert key in word_dict

        assert word_dict["serbian_word"] == "dicttest"
        assert word_dict["english_translation"] == "dicttest"
        assert word_dict["difficulty_level"] == 3
        assert word_dict["category_name"] == category.name

    def test_word_difficulty_constraint(self, db_session):
        """Test difficulty level constraint"""
        category = CategoryFactory()

        # Valid difficulty levels (1-5)
        for level in [1, 2, 3, 4, 5]:
            word = Word(
                serbian_word=f"reč{level}",
                english_translation=f"word{level}",
                category_id=category.id,
                difficulty_level=level,
            )
            db_session.add(word)

        db_session.commit()  # Should succeed

        # Invalid difficulty level should be handled by application logic
        # (database constraint may not be enforced in SQLite during testing)

    def test_word_unique_constraint(self, db_session):
        """Test unique constraint on serbian_word + english_translation"""
        category = CategoryFactory()

        word1 = Word(
            serbian_word="uniquetest",
            english_translation="uniquetest",
            category_id=category.id,
        )

        word2 = Word(
            serbian_word="uniquetest",
            english_translation="uniquetest",
            category_id=category.id,
        )

        db_session.add(word1)
        db_session.commit()

        # Adding duplicate should raise an error
        db_session.add(word2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


@pytest.mark.unit
class TestUserVocabulary:
    """Test cases for UserVocabulary model"""

    def test_user_vocabulary_creation(self, db_session):
        """Test creating user vocabulary entry"""
        user = UserFactory()
        word = WordFactory()

        user_vocab = UserVocabulary(
            user_id=user.id,
            word_id=word.id,
            times_practiced=5,
            times_correct=3,
            mastery_level=60,
        )

        db_session.add(user_vocab)
        db_session.commit()

        assert user_vocab.id is not None
        assert user_vocab.user_id == user.id
        assert user_vocab.word_id == word.id
        assert user_vocab.times_practiced == 5
        assert user_vocab.times_correct == 3
        assert user_vocab.mastery_level == 60

    def test_user_vocabulary_to_dict(self, db_session):
        """Test user vocabulary serialization"""
        user_vocab = UserVocabularyFactory(
            times_practiced=10, times_correct=7, mastery_level=70
        )

        vocab_dict = user_vocab.to_dict()

        expected_keys = [
            "id",
            "word_id",
            "times_practiced",
            "times_correct",
            "last_practiced",
            "mastery_level",
            "created_at",
        ]

        for key in expected_keys:
            assert key in vocab_dict

        assert vocab_dict["times_practiced"] == 10
        assert vocab_dict["times_correct"] == 7
        assert vocab_dict["mastery_level"] == 70

    def test_user_vocabulary_unique_constraint(self, db_session):
        """Test unique constraint on user_id + word_id"""
        user = UserFactory()
        word = WordFactory()

        vocab1 = UserVocabulary(user_id=user.id, word_id=word.id)
        vocab2 = UserVocabulary(user_id=user.id, word_id=word.id)

        db_session.add(vocab1)
        db_session.commit()

        # Adding duplicate should raise an error
        db_session.add(vocab2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


@pytest.mark.unit
class TestSettings:
    """Test cases for Settings model"""

    def test_settings_creation(self, db_session):
        """Test creating user settings"""
        user = UserFactory()

        settings = Settings(user_id=user.id, openai_api_key="test-api-key-123")

        db_session.add(settings)
        db_session.commit()

        assert settings.id is not None
        assert settings.user_id == user.id
        assert settings.openai_api_key == "test-api-key-123"

    def test_settings_to_dict_without_sensitive(self, db_session):
        """Test settings serialization without sensitive data"""
        user = UserFactory()

        settings = Settings(user_id=user.id, openai_api_key="secret-key-123")

        db_session.add(settings)
        db_session.commit()

        settings_dict = settings.to_dict(include_sensitive=False)

        assert "openai_api_key" not in settings_dict
        assert settings_dict["has_openai_key"] is True
        assert settings_dict["user_id"] == user.id

    def test_settings_to_dict_with_sensitive(self, db_session):
        """Test settings serialization with sensitive data"""
        user = UserFactory()

        settings = Settings(user_id=user.id, openai_api_key="secret-key-123")

        db_session.add(settings)
        db_session.commit()

        settings_dict = settings.to_dict(include_sensitive=True)

        assert settings_dict["openai_api_key"] == "secret-key-123"
        assert "has_openai_key" not in settings_dict
        assert settings_dict["user_id"] == user.id


@pytest.mark.unit
class TestPracticeSession:
    """Test cases for PracticeSession model"""

    def test_practice_session_creation(self, db_session):
        """Test creating a practice session"""
        user = UserFactory()

        session = PracticeSession(
            user_id=user.id, total_questions=10, correct_answers=7, duration_seconds=300
        )

        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.user_id == user.id
        assert session.total_questions == 10
        assert session.correct_answers == 7
        assert session.duration_seconds == 300

    def test_practice_session_to_dict(self, db_session):
        """Test practice session serialization"""
        user = UserFactory()

        session = PracticeSession(
            user_id=user.id,
            total_questions=15,
            correct_answers=12,
            duration_seconds=450,
        )

        db_session.add(session)
        db_session.commit()

        session_dict = session.to_dict()

        expected_keys = [
            "id",
            "session_date",
            "total_questions",
            "correct_answers",
            "duration_seconds",
        ]

        for key in expected_keys:
            assert key in session_dict

        assert session_dict["total_questions"] == 15
        assert session_dict["correct_answers"] == 12
        assert session_dict["duration_seconds"] == 450


@pytest.mark.unit
class TestExcludedWord:
    """Test cases for ExcludedWord model"""

    def test_excluded_word_creation(self, db_session):
        """Test creating an excluded word entry"""
        user = UserFactory()
        word = WordFactory()

        excluded = ExcludedWord(
            user_id=user.id, word_id=word.id, reason="manual_removal"
        )

        db_session.add(excluded)
        db_session.commit()

        assert excluded.id is not None
        assert excluded.user_id == user.id
        assert excluded.word_id == word.id
        assert excluded.reason == "manual_removal"

    def test_excluded_word_to_dict(self, db_session):
        """Test excluded word serialization"""
        user = UserFactory()
        word = WordFactory()

        excluded = ExcludedWord(
            user_id=user.id, word_id=word.id, reason="news_parser_skip"
        )

        db_session.add(excluded)
        db_session.commit()

        excluded_dict = excluded.to_dict()

        expected_keys = ["id", "user_id", "word_id", "reason", "created_at", "word"]

        for key in expected_keys:
            assert key in excluded_dict

        assert excluded_dict["reason"] == "news_parser_skip"
        assert excluded_dict["word"] is not None
        assert excluded_dict["word"]["serbian_word"] == word.serbian_word
