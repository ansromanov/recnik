from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    settings = db.relationship(
        "Settings", backref="user", uselist=False, cascade="all, delete-orphan"
    )
    vocabulary = db.relationship(
        "UserVocabulary", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    practice_sessions = db.relationship(
        "PracticeSession", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    openai_api_key = db.Column(db.String(255))
    auto_advance_enabled = db.Column(db.Boolean, default=False, nullable=False)
    auto_advance_timeout = db.Column(db.Integer, default=3, nullable=False)  # seconds
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self, include_sensitive=False):
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "auto_advance_enabled": self.auto_advance_enabled,
            "auto_advance_timeout": self.auto_advance_timeout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            result["openai_api_key"] = self.openai_api_key
        else:
            result["has_openai_key"] = bool(self.openai_api_key)
        return result


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    words = db.relationship("Word", backref="category", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Word(db.Model):
    __tablename__ = "words"

    id = db.Column(db.Integer, primary_key=True)
    serbian_word = db.Column(db.String(255), nullable=False)
    english_translation = db.Column(db.String(255), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL")
    )
    context = db.Column(db.Text)
    notes = db.Column(db.Text)
    difficulty_level = db.Column(db.Integer, default=1, nullable=False)
    is_top_100 = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user_vocabulary = db.relationship(
        "UserVocabulary", backref="word", lazy="dynamic", cascade="all, delete-orphan"
    )
    practice_results = db.relationship(
        "PracticeResult", backref="word", lazy="dynamic", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "serbian_word", "english_translation", name="_serbian_english_uc"
        ),
        db.CheckConstraint(
            "difficulty_level >= 1 AND difficulty_level <= 5",
            name="_difficulty_level_check",
        ),
    )

    def to_dict(self, include_user_data=False):
        result = {
            "id": self.id,
            "serbian_word": self.serbian_word,
            "english_translation": self.english_translation,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "context": self.context,
            "notes": self.notes,
            "difficulty_level": self.difficulty_level,
            "is_top_100": self.is_top_100,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_user_data:
            user_vocab = self.user_vocabulary.first()
            if user_vocab:
                result["mastery_level"] = user_vocab.mastery_level
                result["times_practiced"] = user_vocab.times_practiced
            else:
                result["mastery_level"] = None
                result["times_practiced"] = None

        return result


class UserVocabulary(db.Model):
    __tablename__ = "user_vocabulary"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    word_id = db.Column(
        db.Integer,
        db.ForeignKey("words.id", ondelete="CASCADE"),
        nullable=False,
    )
    times_practiced = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    mastery_level = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "word_id", name="user_vocabulary_user_word_unique"
        ),
        db.CheckConstraint(
            "mastery_level >= 0 AND mastery_level <= 100", name="_mastery_level_check"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "word_id": self.word_id,
            "times_practiced": self.times_practiced,
            "times_correct": self.times_correct,
            "last_practiced": self.last_practiced.isoformat()
            if self.last_practiced
            else None,
            "mastery_level": self.mastery_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PracticeSession(db.Model):
    __tablename__ = "practice_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    duration_seconds = db.Column(db.Integer)

    # Relationships
    practice_results = db.relationship(
        "PracticeResult",
        backref="session",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "session_date": self.session_date.isoformat()
            if self.session_date
            else None,
            "total_questions": self.total_questions,
            "correct_answers": self.correct_answers,
            "duration_seconds": self.duration_seconds,
        }


class PracticeResult(db.Model):
    __tablename__ = "practice_results"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("practice_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    word_id = db.Column(
        db.Integer, db.ForeignKey("words.id", ondelete="CASCADE"), nullable=False
    )
    was_correct = db.Column(db.Boolean, nullable=False)
    response_time_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "word_id": self.word_id,
            "was_correct": self.was_correct,
            "response_time_seconds": self.response_time_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ExcludedWord(db.Model):
    __tablename__ = "excluded_words"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    word_id = db.Column(
        db.Integer,
        db.ForeignKey("words.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason = db.Column(db.String(255))  # "manual_removal", "news_parser_skip", etc.
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    word = db.relationship("Word", backref="excluded_by_users")
    user = db.relationship("User", backref="excluded_words")

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "word_id", name="excluded_words_user_word_unique"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "word_id": self.word_id,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "word": self.word.to_dict() if self.word else None,
        }


# Event listener to update the updated_at timestamp
@event.listens_for(Word, "before_update")
def update_word_timestamp(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
