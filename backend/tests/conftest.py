"""
Test configuration and fixtures for Serbian Vocabulary Application
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, MagicMock
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
import fakeredis
import factory

# Import application components
from models import db, User, Category, Word, UserVocabulary, Settings, ExcludedWord
from services.translation_cache import TranslationCache
from services.text_processor import SerbianTextProcessor


@pytest.fixture(scope="session")
def app():
    """Create and configure a test Flask application"""
    app = Flask(__name__)

    # Use in-memory SQLite for testing
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["JWT_SECRET_KEY"] = "test-jwt-secret"

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # Seed test data
        _seed_test_data()

        yield app

        # Cleanup
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client"""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Provide application context for tests"""
    with app.app_context():
        yield app


@pytest.fixture
def db_session(app_context):
    """Provide a database session for tests"""
    yield db.session
    # Rollback any uncommitted changes after each test
    db.session.rollback()


@pytest.fixture
def fake_redis():
    """Provide a fake Redis client for testing"""
    return fakeredis.FakeRedis()


@pytest.fixture
def translation_cache(fake_redis):
    """Provide a TranslationCache instance with fake Redis"""
    return TranslationCache(fake_redis, ttl=3600)  # 1 hour TTL for tests


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    mock_client = Mock()
    mock_completion = Mock()
    mock_completion.choices = [Mock()]
    mock_completion.choices[0].message = {
        "content": '{"processed_words": [], "filtering_summary": {"total_raw_words": 0}}'
    }
    mock_client.ChatCompletion.create.return_value = mock_completion
    return mock_client


@pytest.fixture
def text_processor(mock_openai_client):
    """Provide a SerbianTextProcessor instance with mocked OpenAI"""
    from unittest.mock import patch

    with patch("openai.ChatCompletion", mock_openai_client.ChatCompletion):
        processor = SerbianTextProcessor("test-api-key")
        return processor


def _seed_test_data():
    """Seed the test database with initial data"""
    # Create test categories
    categories = [
        Category(id=1, name="Common Words", description="Frequently used words"),
        Category(id=2, name="Verbs", description="Action words"),
        Category(id=3, name="Nouns", description="Objects and concepts"),
        Category(id=4, name="Adjectives", description="Descriptive words"),
    ]

    for category in categories:
        db.session.add(category)

    # Create test words
    words = [
        Word(id=1, serbian_word="kuća", english_translation="house", category_id=3),
        Word(id=2, serbian_word="raditi", english_translation="to work", category_id=2),
        Word(id=3, serbian_word="velik", english_translation="big", category_id=4),
        Word(id=4, serbian_word="čovek", english_translation="man", category_id=3),
        Word(id=5, serbian_word="ići", english_translation="to go", category_id=2),
    ]

    for word in words:
        db.session.add(word)

    # Create test user
    user = User(id=1, username="testuser")
    user.set_password("testpassword")
    db.session.add(user)

    # Create user settings
    settings = Settings(id=1, user_id=1, openai_api_key="test-key")
    db.session.add(settings)

    db.session.commit()


# Factory classes for creating test data
class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 100)  # Start from 101 to avoid conflicts
    username = factory.Sequence(lambda n: f"user{n + 100}")
    password_hash = factory.LazyAttribute(lambda obj: f"hash_{obj.username}")


class CategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Category
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 100)  # Start from 101 to avoid conflicts
    name = factory.Sequence(lambda n: f"Category {n + 100}")
    description = factory.LazyAttribute(lambda obj: f"Description for {obj.name}")


class WordFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Word
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 100)  # Start from 101 to avoid conflicts
    serbian_word = factory.Sequence(lambda n: f"reč{n + 100}")
    english_translation = factory.Sequence(lambda n: f"word{n + 100}")
    category_id = 1
    difficulty_level = 1


class UserVocabularyFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = UserVocabulary
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 100)  # Start from 101 to avoid conflicts
    user_id = 1
    word_id = factory.Sequence(lambda n: n + 100)
    times_practiced = 0
    times_correct = 0
    mastery_level = 0


class ExcludedWordFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = ExcludedWord
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"

    id = factory.Sequence(lambda n: n + 100)  # Start from 101 to avoid conflicts
    user_id = 1
    word_id = factory.Sequence(lambda n: n + 100)
    reason = "test_exclusion"


@pytest.fixture
def sample_serbian_text():
    """Provide sample Serbian text for testing"""
    return """
    Jutros sam ustao rano i pošao u grad. Kupovao sam hranu na pijaci.
    Prodavci su bili ljubazni. Video sam prijatelje na kafi.
    Razgovarali smo o filmu koji smo gledali sinoć.
    Vratió sam se kući autobusom koji vozi svakoga dana.
    """


@pytest.fixture
def sample_categories():
    """Provide sample categories for testing"""
    return [
        {"id": 1, "name": "Common Words"},
        {"id": 2, "name": "Verbs"},
        {"id": 3, "name": "Nouns"},
        {"id": 4, "name": "Adjectives"},
    ]


@pytest.fixture
def sample_translation_data():
    """Provide sample translation data for testing"""
    return {
        "serbian_word": "raditi",
        "english_translation": "to work",
        "category_id": 2,
        "category_name": "Verbs",
        "original_form": "radim",
    }


# Mock environment variables for testing
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock environment variables for all tests"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
