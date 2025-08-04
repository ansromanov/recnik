"""
Test models in isolation without requiring full Flask app
"""

from flask import Flask
from flask_jwt_extended import JWTManager

from models import Category, Settings, User, UserVocabulary, Word, db


def test_basic_model_functionality():
    """Test basic model functionality"""
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    app.config["JWT_SECRET_KEY"] = "test-jwt-secret"

    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # Test category creation
        category = Category(name="Test Category", description="Test description")
        db.session.add(category)
        db.session.commit()

        assert category.id is not None
        assert category.name == "Test Category"

        # Test user creation
        user = User(username="testuser")
        user.set_password("testpass")
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == "testuser"
        assert user.check_password("testpass")

        # Test word creation
        word = Word(
            serbian_word="test", english_translation="test", category_id=category.id
        )
        db.session.add(word)
        db.session.commit()

        assert word.id is not None
        assert word.serbian_word == "test"
        assert word.category_id == category.id

        # Test user vocabulary creation
        user_vocab = UserVocabulary(user_id=user.id, word_id=word.id)
        db.session.add(user_vocab)
        db.session.commit()

        assert user_vocab.id is not None
        assert user_vocab.user_id == user.id
        assert user_vocab.word_id == word.id

        # Test settings creation
        settings = Settings(user_id=user.id, openai_api_key="test-key")
        db.session.add(settings)
        db.session.commit()

        assert settings.id is not None
        assert settings.user_id == user.id
        assert settings.openai_api_key == "test-key"


def test_user_password_functionality():
    """Test user password hashing and verification"""
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # Test user password functionality
        user = User(username="passwordtest")
        user.set_password("mysecretpassword")

        # Password should be hashed, not stored in plain text
        assert user.password_hash != "mysecretpassword"
        assert len(user.password_hash) > 20  # Hashed passwords are longer

        # Should be able to verify correct password
        assert user.check_password("mysecretpassword") == True

        # Should reject incorrect password
        assert user.check_password("wrongpassword") == False
        assert user.check_password("") == False


def test_word_serialization():
    """Test word to_dict serialization"""
    # Create a minimal Flask app for testing
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["TESTING"] = True

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()

        # Create test data
        category = Category(name="Test Category")
        db.session.add(category)
        db.session.flush()

        word = Word(
            serbian_word="kuća",
            english_translation="house",
            category_id=category.id,
            difficulty_level=2,
        )
        db.session.add(word)
        db.session.commit()

        # Test serialization
        word_dict = word.to_dict()

        assert word_dict["serbian_word"] == "kuća"
        assert word_dict["english_translation"] == "house"
        assert word_dict["category_id"] == category.id
        assert word_dict["difficulty_level"] == 2
        assert "id" in word_dict
        assert "created_at" in word_dict
