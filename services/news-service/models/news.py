from datetime import datetime
from models.database import db


class NewsArticle(db.Model):
    """Enhanced news article model with proper formatting support"""

    __tablename__ = "news_articles"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    formatted_content = db.Column(
        db.Text
    )  # Properly formatted content with line breaks
    summary = db.Column(db.Text)  # Auto-generated summary
    source = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.String(1000))
    category = db.Column(db.String(100), nullable=False)
    publish_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Content metadata
    word_count = db.Column(db.Integer)
    reading_time_minutes = db.Column(db.Integer)
    difficulty_level = db.Column(db.String(20))  # beginner, intermediate, advanced

    # Processing flags
    is_formatted = db.Column(db.Boolean, default=False)
    has_full_content = db.Column(db.Boolean, default=False)
    needs_processing = db.Column(db.Boolean, default=True)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.formatted_content or self.content,
            "raw_content": self.content,
            "summary": self.summary,
            "source": self.source,
            "source_url": self.source_url,
            "category": self.category,
            "publish_date": self.publish_date.isoformat()
            if self.publish_date
            else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "word_count": self.word_count,
            "reading_time_minutes": self.reading_time_minutes,
            "difficulty_level": self.difficulty_level,
            "is_formatted": self.is_formatted,
            "has_full_content": self.has_full_content,
            "content_type": "article",
        }


class ContentItem(db.Model):
    """Model for LLM-generated content (dialogues, summaries, etc.)"""

    __tablename__ = "content_items"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(
        db.String(50), nullable=False
    )  # dialogue, summary, story, etc.
    topic = db.Column(db.String(200))
    difficulty_level = db.Column(db.String(20))  # beginner, intermediate, advanced
    target_words = db.Column(db.JSON)  # Array of words this content focuses on

    # Generation metadata
    generated_by = db.Column(db.String(50), default="gpt-3.5-turbo")
    generation_prompt = db.Column(db.Text)
    word_count = db.Column(db.Integer)
    reading_time_minutes = db.Column(db.Integer)

    # Source information (if based on an article)
    source_article_id = db.Column(db.Integer, db.ForeignKey("news_articles.id"))
    source_article = db.relationship("NewsArticle", backref="generated_content")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "content_type": self.content_type,
            "topic": self.topic,
            "difficulty_level": self.difficulty_level,
            "target_words": self.target_words,
            "generated_by": self.generated_by,
            "word_count": self.word_count,
            "reading_time_minutes": self.reading_time_minutes,
            "source_article_id": self.source_article_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "source": "Generated Content",
            "category": self.content_type.title(),
        }


class ContentTemplate(db.Model):
    """Templates for generating different types of content"""

    __tablename__ = "content_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    prompt_template = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    difficulty_level = db.Column(db.String(20))
    target_word_count = db.Column(db.Integer)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "content_type": self.content_type,
            "description": self.description,
            "difficulty_level": self.difficulty_level,
            "target_word_count": self.target_word_count,
            "is_active": self.is_active,
        }
