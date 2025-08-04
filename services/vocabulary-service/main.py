#!/usr/bin/env python3
"""
Vocabulary Service
Handles vocabulary management, words, categories, and text processing.
"""

import os

from controllers.text_processor_controller import TextProcessorController
from controllers.vocabulary_controller import VocabularyController
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import get_jwt_identity, jwt_required
from health import health_bp
from metrics import metrics_bp
from prometheus_flask_exporter import PrometheusMetrics
from utils.logger import setup_logger

from models.database import db

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure CORS
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:3001"],
            "allow_headers": [
                "Content-Type",
                "Authorization",
                "Access-Control-Allow-Credentials",
            ],
            "expose_headers": ["Content-Range", "X-Content-Range"],
            "supports_credentials": True,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "send_wildcard": False,
            "always_send": True,
        }
    },
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}

# JWT configuration
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "vocabulary-service-secret-key")

# Initialize database
db.init_app(app)

# Setup logging
logger = setup_logger("vocabulary-service")

# Setup Prometheus metrics
metrics = PrometheusMetrics(app)
metrics.info("vocabulary_service_info", "Vocabulary Service", version="1.0.0")

# Initialize controllers
vocabulary_controller = VocabularyController(logger)
text_processor_controller = TextProcessorController(logger)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(metrics_bp)


# Category routes
@app.route("/api/categories")
@jwt_required(optional=True)
def get_categories():
    user_id = get_jwt_identity()
    logger.info(
        "Get categories",
        extra={
            "endpoint": "/api/categories",
            "user_id": user_id,
        },
    )
    return vocabulary_controller.get_categories(user_id)


# Word routes
@app.route("/api/words")
@jwt_required()
def get_words():
    user_id = get_jwt_identity()
    logger.info(
        "Get words",
        extra={
            "endpoint": "/api/words",
            "user_id": user_id,
            "category_id": request.args.get("category_id"),
        },
    )
    return vocabulary_controller.get_words(user_id, request)


@app.route("/api/words", methods=["POST"])
@jwt_required()
def add_words():
    user_id = get_jwt_identity()
    logger.info(
        "Add words",
        extra={
            "endpoint": "/api/words",
            "method": "POST",
            "user_id": user_id,
        },
    )
    return vocabulary_controller.add_words(user_id, request)


# Text processing routes
@app.route("/api/process-text", methods=["POST"])
@jwt_required()
def process_text():
    user_id = get_jwt_identity()
    logger.info(
        "Process text",
        extra={
            "endpoint": "/api/process-text",
            "method": "POST",
            "user_id": user_id,
        },
    )
    return text_processor_controller.process_text(user_id, request)


# Top 100 words routes
@app.route("/api/top100/categories/<int:category_id>")
@jwt_required()
def get_top_100_words_by_category(category_id):
    user_id = get_jwt_identity()
    logger.info(
        "Get top 100 words by category",
        extra={
            "endpoint": f"/api/top100/categories/{category_id}",
            "user_id": user_id,
            "category_id": category_id,
        },
    )
    return vocabulary_controller.get_top_100_words_by_category(user_id, category_id)


@app.route("/api/top100/add", methods=["POST"])
@jwt_required()
def add_top_100_words_to_vocabulary():
    user_id = get_jwt_identity()
    logger.info(
        "Add top 100 words to vocabulary",
        extra={
            "endpoint": "/api/top100/add",
            "method": "POST",
            "user_id": user_id,
        },
    )
    return vocabulary_controller.add_top_100_words_to_vocabulary(user_id, request)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3003))
    logger.info(
        "Starting Vocabulary Service",
        extra={"port": port, "environment": os.getenv("ENVIRONMENT", "development")},
    )

    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
