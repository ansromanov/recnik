import os

from controllers.content_controller import ContentController

# Import our controllers
from controllers.news_controller import NewsController
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
import redis

# Import utilities
from utils.logger import setup_logger

# Import models
from models.database import init_db

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=["http://localhost:3000", "http://localhost:80"])

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "postgresql://user:password@localhost/vocabulary_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Redis configuration
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Initialize database
db = init_db(app)

# Initialize logger
logger = setup_logger(__name__)

# Initialize controllers
news_controller = NewsController(redis_client, db, logger)
content_controller = ContentController(redis_client, db, logger)


@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "news-service"})


@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return jsonify({"service": "news-service", "status": "active"})


# News endpoints
@app.route("/api/news/sources")
def get_news_sources():
    """Get available news sources and categories"""
    return news_controller.get_sources()


@app.route("/api/news")
def get_news():
    """Get news articles with improved formatting"""
    source = request.args.get("source", "all")
    category = request.args.get("category", "all")
    content_type = request.args.get("type", "all")  # articles, dialogues, summaries
    limit = int(request.args.get("limit", 20))

    return news_controller.get_formatted_news(source, category, content_type, limit)


@app.route("/api/news/article/<int:article_id>")
def get_article_detail(article_id):
    """Get detailed article with enhanced formatting"""
    return news_controller.get_article_detail(article_id)


@app.route("/api/news/refresh", methods=["POST"])
def refresh_news():
    """Manually refresh news cache"""
    return news_controller.refresh_news_cache()


# Content generation endpoints
@app.route("/api/content/dialogue", methods=["POST"])
def generate_dialogue():
    """Generate dialogue from news topic using LLM"""
    data = request.get_json()
    topic = data.get("topic")
    difficulty = data.get("difficulty", "intermediate")
    word_count = data.get("word_count", 200)

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    return content_controller.generate_dialogue(topic, difficulty, word_count)


@app.route("/api/content/summary", methods=["POST"])
def generate_summary():
    """Generate summary from article using LLM"""
    data = request.get_json()
    article_text = data.get("article_text")
    summary_type = data.get("type", "brief")  # brief, detailed, vocabulary_focused

    if not article_text:
        return jsonify({"error": "Article text is required"}), 400

    return content_controller.generate_summary(article_text, summary_type)


@app.route("/api/content/vocabulary-context", methods=["POST"])
def generate_vocabulary_context():
    """Generate vocabulary-focused content from topic"""
    data = request.get_json()
    topic = data.get("topic")
    target_words = data.get("target_words", [])
    content_type = data.get("content_type", "story")  # story, dialogue, article

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    return content_controller.generate_vocabulary_context(
        topic, target_words, content_type
    )


@app.route("/api/content/types")
def get_content_types():
    """Get available content types"""
    return content_controller.get_content_types()


@app.route("/api/content/recent")
def get_recent_content():
    """Get recently generated content"""
    content_type = request.args.get("type", "all")
    limit = int(request.args.get("limit", 10))

    return content_controller.get_recent_content(content_type, limit)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.getenv("PORT", 5002))
    app.run(
        host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true"
    )
