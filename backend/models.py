from datetime import datetime, timezone, date
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
    avatar_url = db.Column(db.String(500))  # URL to avatar image
    avatar_type = db.Column(
        db.String(20), default="ai_generated"
    )  # 'ai_generated', 'uploaded', 'default'
    avatar_seed = db.Column(db.String(100))  # Seed for AI avatar generation
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
            "avatar_url": self.avatar_url,
            "avatar_type": self.avatar_type,
            "avatar_seed": self.avatar_seed,
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
    mastery_threshold = db.Column(
        db.Integer, default=5, nullable=False
    )  # correct answers needed for mastery
    practice_round_count = db.Column(
        db.Integer, default=10, nullable=False
    )  # words per practice session
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
            "mastery_threshold": self.mastery_threshold,
            "practice_round_count": self.practice_round_count,
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


class UserStreak(db.Model):
    __tablename__ = "user_streaks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    streak_type = db.Column(
        db.String(20), nullable=False
    )  # 'daily', 'weekly', 'monthly'
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)
    last_activity_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "streak_type", name="user_streaks_user_type_unique"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "streak_type": self.streak_type,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "last_activity_date": self.last_activity_date.isoformat()
            if self.last_activity_date
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class StreakActivity(db.Model):
    __tablename__ = "streak_activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_date = db.Column(db.Date, nullable=False)
    activity_type = db.Column(
        db.String(50), nullable=False
    )  # 'practice_session', 'vocabulary_added', 'login'
    activity_count = db.Column(db.Integer, default=1, nullable=False)
    streak_qualifying = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "user_id", "activity_date", name="streak_activities_user_date_unique"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_date": self.activity_date.isoformat()
            if self.activity_date
            else None,
            "activity_type": self.activity_type,
            "activity_count": self.activity_count,
            "streak_qualifying": self.streak_qualifying,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserXP(db.Model):
    __tablename__ = "user_xp"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    current_xp = db.Column(db.Integer, default=0, nullable=False)
    total_xp = db.Column(db.Integer, default=0, nullable=False)
    current_level = db.Column(db.Integer, default=1, nullable=False)
    xp_to_next_level = db.Column(db.Integer, default=100, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "current_xp": self.current_xp,
            "total_xp": self.total_xp,
            "current_level": self.current_level,
            "xp_to_next_level": self.xp_to_next_level,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class XPActivity(db.Model):
    __tablename__ = "xp_activities"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    activity_type = db.Column(db.String(50), nullable=False)
    xp_earned = db.Column(db.Integer, default=0, nullable=False)
    activity_date = db.Column(
        db.Date, default=lambda: datetime.now(timezone.utc).date()
    )
    activity_details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "activity_type": self.activity_type,
            "xp_earned": self.xp_earned,
            "activity_date": self.activity_date.isoformat()
            if self.activity_date
            else None,
            "activity_details": self.activity_details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    achievement_key = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    badge_icon = db.Column(db.String(10))
    badge_color = db.Column(db.String(20), default="#3498db")
    category = db.Column(db.String(50), default="general")
    xp_reward = db.Column(db.Integer, default=0)
    unlock_criteria = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user_achievements = db.relationship(
        "UserAchievement",
        backref="achievement",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "achievement_key": self.achievement_key,
            "name": self.name,
            "description": self.description,
            "badge_icon": self.badge_icon,
            "badge_color": self.badge_color,
            "category": self.category,
            "xp_reward": self.xp_reward,
            "unlock_criteria": self.unlock_criteria,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    achievement_id = db.Column(
        db.Integer,
        db.ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
    )
    earned_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    progress_data = db.Column(db.JSON)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "achievement_id",
            name="user_achievements_user_achievement_unique",
        ),
    )

    def to_dict(self):
        achievement_dict = self.achievement.to_dict() if self.achievement else None
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement_id": self.achievement_id,
            "earned_at": self.earned_at.isoformat() if self.earned_at else None,
            "progress_data": self.progress_data,
            "achievement": achievement_dict,
        }


# Add relationships to User model
User.streaks = db.relationship(
    "UserStreak", backref="user", lazy="dynamic", cascade="all, delete-orphan"
)
User.streak_activities = db.relationship(
    "StreakActivity", backref="user", lazy="dynamic", cascade="all, delete-orphan"
)
User.xp = db.relationship(
    "UserXP", backref="user", uselist=False, cascade="all, delete-orphan"
)
User.xp_activities = db.relationship(
    "XPActivity", backref="user", lazy="dynamic", cascade="all, delete-orphan"
)
User.achievements = db.relationship(
    "UserAchievement", backref="user", lazy="dynamic", cascade="all, delete-orphan"
)


# Event listener to update the updated_at timestamp
@event.listens_for(Word, "before_update")
def update_word_timestamp(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(UserStreak, "before_update")
def update_streak_timestamp(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(UserXP, "before_update")
def update_xp_timestamp(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)
