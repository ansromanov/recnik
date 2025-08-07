"""
Test configuration and fixtures for Recnik
"""

from unittest.mock import Mock

import factory
import fakeredis
import pytest

# Import application components
from models import Category, ExcludedWord, Settings, User, UserVocabulary, Word, db
from services.text_processor import SerbianTextProcessor
from services.translation_cache import TranslationCache


@pytest.fixture(scope="session")
def app():
    """Create and configure a test Flask application"""
    from flask import Flask, jsonify, request
    from flask_jwt_extended import (
        JWTManager,
        get_jwt_identity,
        jwt_required,
    )

    from models import db

    # Create a fresh Flask app for testing
    flask_app = Flask(__name__)

    # Configure for testing
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    flask_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret-key"
    flask_app.config["JWT_SECRET_KEY"] = "test-jwt-secret"
    flask_app.config["WTF_CSRF_ENABLED"] = False

    # Initialize extensions
    db.init_app(flask_app)
    jwt = JWTManager(flask_app)

    # Add essential routes for tests
    @flask_app.route("/api/words", methods=["POST"])
    @jwt_required()
    def add_words():
        try:
            user_id = int(get_jwt_identity())
            data = request.get_json()
            words = data.get("words", [])

            if not words or not isinstance(words, list):
                return jsonify({"error": "Words array is required"}), 400

            inserted_words = []
            added_to_vocabulary = []
            skipped_words = []

            for word_data in words:
                try:
                    serbian_word = word_data.get("serbian_word", "").strip()
                    english_translation = word_data.get("english_translation", "").strip()

                    if not serbian_word or not english_translation:
                        continue

                    # Check if word already exists
                    existing_word = Word.query.filter_by(
                        serbian_word=serbian_word,
                        english_translation=english_translation,
                    ).first()

                    if existing_word:
                        # Check if already in user's vocabulary
                        existing_vocab = UserVocabulary.query.filter_by(
                            user_id=user_id, word_id=existing_word.id
                        ).first()

                        if existing_vocab:
                            skipped_words.append(
                                {
                                    "word": existing_word.to_dict(),
                                    "reason": "already_in_vocabulary",
                                }
                            )
                            continue
                        else:
                            # Add existing word to user's vocabulary
                            user_vocab = UserVocabulary(user_id=user_id, word_id=existing_word.id)
                            db.session.add(user_vocab)
                            added_to_vocabulary.append(existing_word.to_dict())
                            continue

                    # Create new word
                    new_word = Word(
                        serbian_word=serbian_word,
                        english_translation=english_translation,
                        category_id=word_data.get("category_id", 1),
                        context=word_data.get("context"),
                        notes=word_data.get("notes"),
                    )
                    db.session.add(new_word)
                    db.session.flush()  # Get the ID without committing

                    # Add to user vocabulary
                    user_vocab = UserVocabulary(user_id=user_id, word_id=new_word.id)
                    db.session.add(user_vocab)

                    inserted_words.append(new_word.to_dict())
                    added_to_vocabulary.append(new_word.to_dict())

                except Exception as e:
                    print(
                        f'Error processing word "{word_data.get("serbian_word", "unknown")}": {e}'
                    )
                    skipped_words.append({"word": word_data, "reason": f"processing_error: {e!s}"})
                    continue

            # Commit all changes at once
            db.session.commit()

            return jsonify(
                {
                    "success": True,
                    "inserted": len(inserted_words),
                    "words": inserted_words,
                    "added_to_vocabulary": len(added_to_vocabulary),
                    "vocabulary_words": added_to_vocabulary,
                    "skipped": len(skipped_words),
                    "skipped_words": skipped_words,
                }
            )
        except Exception as e:
            db.session.rollback()
            print(f"Error adding words: {e}")
            return jsonify({"error": f"Failed to add words: {e!s}"}), 500

    with flask_app.app_context():
        # Create all tables
        db.create_all()
        # Seed test data
        _seed_test_data()
        yield flask_app
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


@pytest.fixture(autouse=True)
def db_session(app_context):
    """Provide a database session for tests with proper cleanup"""
    yield db.session

    # Clean up all data added during the test, but keep the seeded data
    # Delete in reverse dependency order to avoid foreign key constraint issues
    try:
        # Get the test user ID
        test_user = User.query.filter_by(username="testuser").first()
        if test_user:
            test_user_id = test_user.id

            # Clean up user vocabulary entries for the test user that might have been added during tests
            db.session.query(UserVocabulary).filter(UserVocabulary.user_id == test_user_id).delete()

            # Clean up any additional users created during tests (keep test user)
            db.session.query(User).filter(User.id != test_user_id).delete()

        # Clean up any words added during tests that are not from our seed data
        seeded_words = ["pas", "raditi", "velik", "čovek", "ići"]
        db.session.query(Word).filter(~Word.serbian_word.in_(seeded_words)).delete()

        db.session.commit()
    except Exception as e:
        print(f"Error during test cleanup: {e}")
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
    # Check if data already exists to avoid duplicates
    existing_user = User.query.filter_by(username="testuser").first()
    if existing_user:
        return  # Data already seeded

    # Create test categories without explicit IDs (let database auto-increment)
    categories_data = [
        {"name": "Common Words", "description": "Frequently used words"},
        {"name": "Verbs", "description": "Action words"},
        {"name": "Nouns", "description": "Objects and concepts"},
        {"name": "Adjectives", "description": "Descriptive words"},
    ]

    categories = []
    for cat_data in categories_data:
        # Check if category already exists
        existing_cat = Category.query.filter_by(name=cat_data["name"]).first()
        if existing_cat:
            categories.append(existing_cat)
        else:
            category = Category(name=cat_data["name"], description=cat_data["description"])
            db.session.add(category)
            db.session.flush()  # Flush to get the ID
            categories.append(category)

    # Create test words without explicit IDs
    words_data = [
        {
            "serbian_word": "pas",
            "english_translation": "dog",
            "category_idx": 2,
        },  # Nouns
        {
            "serbian_word": "raditi",
            "english_translation": "to work",
            "category_idx": 1,
        },  # Verbs
        {
            "serbian_word": "velik",
            "english_translation": "big",
            "category_idx": 3,
        },  # Adjectives
        {
            "serbian_word": "čovek",
            "english_translation": "man",
            "category_idx": 2,
        },  # Nouns
        {
            "serbian_word": "ići",
            "english_translation": "to go",
            "category_idx": 1,
        },  # Verbs
    ]

    for word_data in words_data:
        # Check if word already exists
        existing_word = Word.query.filter_by(
            serbian_word=word_data["serbian_word"],
            english_translation=word_data["english_translation"],
        ).first()
        if not existing_word:
            word = Word(
                serbian_word=word_data["serbian_word"],
                english_translation=word_data["english_translation"],
                category_id=categories[word_data["category_idx"]].id,
            )
            db.session.add(word)

    # Create test user without explicit ID
    user = User(username="testuser")
    user.set_password("testpassword")
    db.session.add(user)
    db.session.flush()  # Flush to get the user ID

    # Create user settings without explicit ID
    settings = Settings(user_id=user.id, openai_api_key="test-key")
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
    user_id = factory.LazyAttribute(
        lambda obj: User.query.filter_by(username="testuser").first().id
    )
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
    user_id = factory.LazyAttribute(
        lambda obj: User.query.filter_by(username="testuser").first().id
    )
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
