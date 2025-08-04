"""
Vocabulary models for vocabulary service
"""

from datetime import datetime

from sqlalchemy import event

from .database import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to words
    words = db.relationship("Word", back_populates="category")

    def to_dict(self):
        """Convert category to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Word(db.Model):
    __tablename__ = "words"

    id = db.Column(db.Integer, primary_key=True)
    serbian_word = db.Column(db.String(200), nullable=False)
    english_translation = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    context = db.Column(db.Text)
    notes = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20), default="beginner")
    is_top_100 = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship("Category", back_populates="words")
    user_vocabulary = db.relationship("UserVocabulary", back_populates="word")

    def to_dict(self, include_user_data=False):
        """Convert word to dictionary for JSON serialization"""
        result = {
            "id": self.id,
            "serbian_word": self.serbian_word,
            "english_translation": self.english_translation,
            "category_id": self.category_id,
            "context": self.context,
            "notes": self.notes,
            "difficulty_level": self.difficulty_level,
            "is_top_100": self.is_top_100,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        if hasattr(self, "category") and self.category:
            result["category_name"] = self.category.name

        return result


class UserVocabulary(db.Model):
    __tablename__ = "user_vocabulary"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # References users.id from auth service
    word_id = db.Column(db.Integer, db.ForeignKey("words.id"), nullable=False)
    mastery_level = db.Column(db.Integer, default=0)  # 0-100
    times_practiced = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    last_practiced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to word
    word = db.relationship("Word", back_populates="user_vocabulary")

    # Unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint("user_id", "word_id", name="uq_user_word"),)

    def to_dict(self):
        """Convert user vocabulary to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "word_id": self.word_id,
            "mastery_level": self.mastery_level,
            "times_practiced": self.times_practiced,
            "times_correct": self.times_correct,
            "last_practiced": (self.last_practiced.isoformat() if self.last_practiced else None),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Event listener to update word timestamps
@event.listens_for(Word, "before_update")
def update_word_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()


@event.listens_for(UserVocabulary, "before_update")
def update_user_vocabulary_timestamp(mapper, connection, target):
    target.updated_at = datetime.utcnow()
