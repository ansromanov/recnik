import os
import json
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
import openai
from dotenv import load_dotenv
import requests
from html.parser import HTMLParser
import re
import redis

# Import configuration
import config

# Import our models
from models import (
    db,
    Category,
    Word,
    UserVocabulary,
    PracticeSession,
    PracticeResult,
    User,
    Settings,
    ExcludedWord,
)

# Import image service client (lightweight version that communicates with separate service)
from image_service_client import ImageServiceClient

# Import CAPTCHA service
from services.captcha_service import captcha_service

# Import optimized text processing service
from services.optimized_text_processor import OptimizedSerbianTextProcessor

# Import translation caching service
from services.translation_cache import TranslationCache

# Try to import feedparser, but don't crash if not available
try:
    import feedparser

    RSS_PARSER_AVAILABLE = True
except ImportError:
    print("feedparser not installed. News feature will use fallback articles.")
    RSS_PARSER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Prometheus metrics
from prometheus_flask_exporter import PrometheusMetrics

# Configure metrics with proper endpoint tracking
metrics = PrometheusMetrics(
    app,
    defaults_prefix="flask",
    group_by_endpoint=True,  # This ensures metrics are grouped by endpoint
    path="/metrics",
    static_labels={"service": "vocabulary-backend"},  # Add service label
)

# Configure application info metric
metrics.info("app_info", "Application info", version="1.0")


# Don't track static files
@metrics.do_not_track()
def skip_static():
    """Don't track static files"""
    return request.endpoint == "static"


# Configure CORS properly
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": config.CORS_ORIGINS,
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
app.config["SQLALCHEMY_DATABASE_URI"] = config.DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_size": config.DB_POOL_SIZE,
    "pool_recycle": config.DB_POOL_RECYCLE,
    "pool_pre_ping": config.DB_POOL_PRE_PING,
}

# Redis configuration
redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

# JWT configuration
app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = config.JWT_ACCESS_TOKEN_EXPIRES
jwt = JWTManager(app)

# Initialize database with app
db.init_app(app)

# OpenAI configuration - will be loaded from database per user
# openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize ImageServiceClient (lightweight client for separate image sync service)
image_service = ImageServiceClient(redis_client)

# Test database connection
with app.app_context():
    try:
        from sqlalchemy import text

        db.session.execute(text("SELECT 1"))
        print("Connected to PostgreSQL database using SQLAlchemy")
    except Exception as e:
        print(f"Error connecting to database: {e}")


# Helper function to get user's OpenAI API key
def get_user_openai_key(user_id):
    """Get OpenAI API key from user's settings"""
    user = User.query.get(user_id)
    if user and user.settings and user.settings.openai_api_key:
        return user.settings.openai_api_key
    return None


# Helper function to generate word suggestions using LLM
def generate_word_suggestion(query_term, api_key):
    """
    Generate word suggestion with proper translation and normalization using LLM

    Args:
        query_term: The search term that wasn't found
        api_key: OpenAI API key

    Returns:
        Dictionary with word suggestion data
    """
    try:
        # Determine if the query is likely Serbian or English
        serbian_chars = any(c in query_term.lower() for c in ["č", "ć", "š", "ž", "đ"])

        # Create system prompt for word suggestion
        system_prompt = """You are an expert Serbian-English translator and linguist. Your task is to analyze a word and provide proper translation and normalization.

CRITICAL REQUIREMENTS:
1. If input is Serbian: convert to proper infinitive/base form, then translate to English
2. If input is English: translate to Serbian in proper infinitive/base form
3. Always normalize Serbian words to their dictionary forms:
   - Verbs: convert to infinitive (-ti, -ći, -ši endings)
   - Nouns: convert to nominative singular
   - Adjectives: convert to masculine nominative singular

EXAMPLES:
Serbian input "radim" → "raditi" (to work)
Serbian input "kuće" → "kuća" (house)  
English input "working" → "raditi" (to work)
English input "houses" → "kuća" (house)

OUTPUT FORMAT (JSON):
{
  "suggested_serbian": "properly normalized Serbian word",
  "suggested_english": "English translation",
  "confidence": "high/medium/low",
  "word_type": "verb/noun/adjective/other",
  "message": "explanatory message for user"
}"""

        # Determine the direction of translation
        if serbian_chars:
            user_prompt = f"Analyze this Serbian word and normalize it to proper dictionary form, then translate to English: '{query_term}'"
        else:
            user_prompt = f"Translate this English word to Serbian in proper dictionary form (infinitive for verbs, nominative singular for nouns): '{query_term}'"

        # Call OpenAI API
        completion = openai.ChatCompletion.create(
            api_key=api_key,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=300,
        )

        response = completion.choices[0].message["content"].strip()

        try:
            # Parse JSON response
            suggestion_data = json.loads(response)

            # Add metadata
            suggestion_data.update(
                {
                    "search_term": query_term,
                    "needs_openai_key": False,
                    "llm_processed": True,
                }
            )

            return suggestion_data

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            print(f"Failed to parse LLM response: {response}")
            return {
                "search_term": query_term,
                "suggested_serbian": query_term if serbian_chars else "",
                "suggested_english": "" if serbian_chars else query_term,
                "confidence": "low",
                "word_type": "unknown",
                "message": f"Word '{query_term}' not found. LLM processing failed, but you can still add it manually.",
                "needs_openai_key": False,
                "llm_processed": False,
            }

    except Exception as e:
        print(f"Error in generate_word_suggestion: {e}")
        # Fallback to heuristic approach
        serbian_chars = any(c in query_term.lower() for c in ["č", "ć", "š", "ž", "đ"])

        return {
            "search_term": query_term,
            "suggested_serbian": query_term if serbian_chars else "",
            "suggested_english": "" if serbian_chars else query_term,
            "confidence": "low",
            "word_type": "unknown",
            "message": f"Word '{query_term}' not found. Translation service unavailable, but you can add it manually.",
            "needs_openai_key": False,
            "llm_processed": False,
            "error": str(e),
        }


# Routes
@app.route("/api/health")
def health_check():
    return jsonify(
        {"status": "ok", "message": "Serbian Vocabulary API is running with ORM"}
    )


@app.route("/api/captcha/site-key")
def get_captcha_site_key():
    """Get reCAPTCHA site key for frontend"""
    return jsonify(
        {
            "site_key": config.RECAPTCHA_SITE_KEY,
            "captcha_enabled": bool(
                config.RECAPTCHA_SITE_KEY and config.RECAPTCHA_SECRET_KEY
            ),
        }
    )


# Authentication endpoints
@app.route("/api/auth/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        captcha_response = data.get("captcha_response")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Verify CAPTCHA
        if config.RECAPTCHA_SECRET_KEY:  # Only verify if CAPTCHA is configured
            captcha_result = captcha_service.verify_captcha(
                captcha_response, request.remote_addr
            )
            if not captcha_result["success"]:
                return jsonify({"error": captcha_result["error"]}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        # Create new user
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create default settings for the user
        settings = Settings(user_id=user.id)
        db.session.add(settings)
        db.session.commit()

        # Create access token
        access_token = create_access_token(identity=str(user.id))

        return jsonify(
            {
                "message": "User registered successfully",
                "access_token": access_token,
                "user": user.to_dict(),
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        print(f"Error registering user: {e}")
        return jsonify({"error": "Failed to register user"}), 500


@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")
        captcha_response = data.get("captcha_response")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Verify CAPTCHA
        if config.RECAPTCHA_SECRET_KEY:  # Only verify if CAPTCHA is configured
            captcha_result = captcha_service.verify_captcha(
                captcha_response, request.remote_addr
            )
            if not captcha_result["success"]:
                return jsonify({"error": captcha_result["error"]}), 400

        # Find user
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "Invalid username or password"}), 401

        # Create access token
        access_token = create_access_token(identity=str(user.id))

        return jsonify({"access_token": access_token, "user": user.to_dict()})

    except Exception as e:
        print(f"Error logging in: {e}")
        return jsonify({"error": "Failed to login"}), 500


@app.route("/api/auth/me")
@jwt_required()
def get_current_user():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user.to_dict()})
    except Exception as e:
        print(f"Error getting current user: {e}")
        return jsonify({"error": "Failed to get user info"}), 500


# Settings endpoints
@app.route("/api/settings")
@jwt_required()
def get_settings():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))

        if not user or not user.settings:
            return jsonify({"error": "Settings not found"}), 404

        return jsonify({"settings": user.settings.to_dict(include_sensitive=True)})
    except Exception as e:
        print(f"Error getting settings: {e}")
        return jsonify({"error": "Failed to get settings"}), 500


@app.route("/api/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(int(user_id))

        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json()

        # Create settings if they don't exist
        if not user.settings:
            user.settings = Settings(user_id=user.id)
            db.session.add(user.settings)

        # Update OpenAI API key if provided
        if "openai_api_key" in data:
            user.settings.openai_api_key = data["openai_api_key"]

        # Update auto-advance settings if provided
        if "auto_advance_enabled" in data:
            user.settings.auto_advance_enabled = bool(data["auto_advance_enabled"])

        if "auto_advance_timeout" in data:
            timeout = int(data["auto_advance_timeout"])
            # Validate timeout range (1-10 seconds)
            if 1 <= timeout <= 10:
                user.settings.auto_advance_timeout = timeout
            else:
                return jsonify(
                    {"error": "Auto-advance timeout must be between 1 and 10 seconds"}
                ), 400

        db.session.commit()

        return jsonify(
            {
                "message": "Settings updated successfully",
                "settings": user.settings.to_dict(include_sensitive=True),
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error updating settings: {e}")
        return jsonify({"error": "Failed to update settings"}), 500


@app.route("/api/categories")
@jwt_required(optional=True)
def get_categories():
    try:
        user_id = get_jwt_identity()
        categories = Category.query.order_by(Category.name).all()

        result = []
        for cat in categories:
            cat_dict = cat.to_dict()

            # Count top 100 words in this category
            top_100_count = Word.query.filter_by(
                category_id=cat.id, is_top_100=True
            ).count()
            cat_dict["top_100_count"] = top_100_count

            # If user is logged in, count how many top 100 words they've added
            if user_id:
                user_id = int(user_id)
                added_count = (
                    db.session.query(Word)
                    .join(UserVocabulary)
                    .filter(
                        Word.category_id == cat.id,
                        Word.is_top_100 == True,
                        UserVocabulary.user_id == user_id,
                    )
                    .count()
                )
                cat_dict["user_added_count"] = added_count
            else:
                cat_dict["user_added_count"] = 0

            result.append(cat_dict)

        return jsonify(result)
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return jsonify({"error": "Failed to fetch categories"}), 500


@app.route("/api/words")
@jwt_required()
def get_words():
    try:
        user_id = int(get_jwt_identity())
        category_id = request.args.get("category_id")

        # Build the query with eager loading of relationships
        query = Word.query.options(joinedload(Word.category))

        if category_id:
            query = query.filter(Word.category_id == category_id)

        words = query.order_by(Word.serbian_word).all()

        # Convert to dict with user-specific data
        words_data = []
        for word in words:
            word_dict = word.to_dict()

            # Get user-specific vocabulary data
            user_vocab = UserVocabulary.query.filter_by(
                user_id=user_id, word_id=word.id
            ).first()

            if user_vocab:
                word_dict["mastery_level"] = user_vocab.mastery_level
                word_dict["times_practiced"] = user_vocab.times_practiced
                word_dict["last_practiced"] = (
                    user_vocab.last_practiced.isoformat()
                    if user_vocab.last_practiced
                    else None
                )
                word_dict["is_in_vocabulary"] = True
            else:
                word_dict["mastery_level"] = 0
                word_dict["times_practiced"] = 0
                word_dict["last_practiced"] = None
                word_dict["is_in_vocabulary"] = False

            words_data.append(word_dict)

        return jsonify(words_data)
    except Exception as e:
        print(f"Error fetching words: {e}")
        return jsonify({"error": "Failed to fetch words"}), 500


@app.route("/api/words/search")
@jwt_required()
def search_words():
    """Search for words in both Serbian and English, proposing to add if not found"""
    try:
        user_id = int(get_jwt_identity())
        query_term = request.args.get("q", "").strip()

        if not query_term:
            return jsonify({"error": "Search query is required"}), 400

        # Search in user's vocabulary and all words
        search_term = query_term.lower()

        # Get user's vocabulary word IDs for filtering
        user_word_ids = set(
            uv.word_id for uv in UserVocabulary.query.filter_by(user_id=user_id).all()
        )

        # Search in both Serbian and English words
        vocabulary_results = []
        all_results = []

        # Search in user's vocabulary first
        if user_word_ids:
            vocab_words = (
                Word.query.filter(Word.id.in_(user_word_ids))
                .filter(
                    or_(
                        Word.serbian_word.ilike(f"%{search_term}%"),
                        Word.english_translation.ilike(f"%{search_term}%"),
                    )
                )
                .options(joinedload(Word.category))
                .order_by(Word.serbian_word)
                .all()
            )

            for word in vocab_words:
                word_dict = word.to_dict()
                user_vocab = UserVocabulary.query.filter_by(
                    user_id=user_id, word_id=word.id
                ).first()

                if user_vocab:
                    word_dict["mastery_level"] = user_vocab.mastery_level
                    word_dict["times_practiced"] = user_vocab.times_practiced
                    word_dict["last_practiced"] = (
                        user_vocab.last_practiced.isoformat()
                        if user_vocab.last_practiced
                        else None
                    )
                    word_dict["is_in_vocabulary"] = True
                    vocabulary_results.append(word_dict)

        # Search in all words (including those not in user's vocabulary)
        all_words = (
            Word.query.filter(
                or_(
                    Word.serbian_word.ilike(f"%{search_term}%"),
                    Word.english_translation.ilike(f"%{search_term}%"),
                )
            )
            .options(joinedload(Word.category))
            .order_by(Word.serbian_word)
            .limit(20)  # Limit results for performance
            .all()
        )

        for word in all_words:
            word_dict = word.to_dict()
            word_dict["is_in_vocabulary"] = word.id in user_word_ids

            if word.id in user_word_ids:
                user_vocab = UserVocabulary.query.filter_by(
                    user_id=user_id, word_id=word.id
                ).first()
                if user_vocab:
                    word_dict["mastery_level"] = user_vocab.mastery_level
                    word_dict["times_practiced"] = user_vocab.times_practiced
                    word_dict["last_practiced"] = (
                        user_vocab.last_practiced.isoformat()
                        if user_vocab.last_practiced
                        else None
                    )
            else:
                word_dict["mastery_level"] = 0
                word_dict["times_practiced"] = 0
                word_dict["last_practiced"] = None

            all_results.append(word_dict)

        # Check if we have any results
        has_results = len(vocabulary_results) > 0 or len(all_results) > 0

        # If no results found, suggest adding the word with LLM assistance
        suggestion = None
        if not has_results:
            # Get user's OpenAI API key for translation
            api_key = get_user_openai_key(user_id)

            if api_key:
                # Use LLM to translate and normalize the word
                suggestion = generate_word_suggestion(query_term, api_key)
            else:
                # Fallback to simple heuristics if no API key
                is_likely_serbian = any(
                    c in query_term.lower() for c in ["č", "ć", "š", "ž", "đ"]
                )

                suggestion = {
                    "search_term": query_term,
                    "suggested_serbian": query_term if is_likely_serbian else "",
                    "suggested_english": "" if is_likely_serbian else query_term,
                    "message": f"No words found for '{query_term}'. Would you like to add it to your vocabulary?",
                    "needs_openai_key": True,
                }

        return jsonify(
            {
                "query": query_term,
                "vocabulary_results": vocabulary_results,
                "all_results": all_results,
                "has_results": has_results,
                "suggestion": suggestion,
                "counts": {
                    "vocabulary": len(vocabulary_results),
                    "all_words": len(all_results),
                },
            }
        )

    except Exception as e:
        print(f"Error searching words: {e}")
        return jsonify({"error": "Failed to search words"}), 500


@app.route("/api/words/add-suggested", methods=["POST"])
@jwt_required()
def add_suggested_word():
    """Add a suggested word to vocabulary and queue for image processing"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()

        serbian_word = data.get("serbian_word", "").strip()
        english_translation = data.get("english_translation", "").strip()
        category_id = data.get("category_id", 1)  # Default to first category
        context = data.get("context", "")
        notes = data.get("notes", "")

        if not serbian_word or not english_translation:
            return jsonify(
                {"error": "Both Serbian word and English translation are required"}
            ), 400

        # Check if word already exists
        existing_word = Word.query.filter_by(
            serbian_word=serbian_word, english_translation=english_translation
        ).first()

        if existing_word:
            # Check if already in user's vocabulary
            existing_vocab = UserVocabulary.query.filter_by(
                user_id=user_id, word_id=existing_word.id
            ).first()

            if existing_vocab:
                return jsonify(
                    {
                        "error": "Word already exists in your vocabulary",
                        "word": existing_word.to_dict(),
                    }
                ), 409
            else:
                # Add existing word to user's vocabulary
                user_vocab = UserVocabulary(user_id=user_id, word_id=existing_word.id)
                db.session.add(user_vocab)
                db.session.commit()

                # Queue for image processing
                image_service.populate_images_for_words(
                    [
                        {
                            "serbian_word": serbian_word,
                            "english_translation": english_translation,
                        }
                    ],
                    priority=True,
                )

                word_dict = existing_word.to_dict()
                word_dict["is_in_vocabulary"] = True
                word_dict["mastery_level"] = 0
                word_dict["times_practiced"] = 0
                word_dict["last_practiced"] = None

                return jsonify(
                    {
                        "success": True,
                        "message": f"Added existing word '{serbian_word}' to your vocabulary",
                        "word": word_dict,
                        "queued_for_image": True,
                    }
                )

        # Create new word
        new_word = Word(
            serbian_word=serbian_word,
            english_translation=english_translation,
            category_id=category_id,
            context=context,
            notes=notes,
        )
        db.session.add(new_word)
        db.session.flush()  # Get the ID

        # Add to user's vocabulary
        user_vocab = UserVocabulary(user_id=user_id, word_id=new_word.id)
        db.session.add(user_vocab)
        db.session.commit()

        # Queue for image processing with high priority
        image_service.populate_images_for_words(
            [
                {
                    "serbian_word": serbian_word,
                    "english_translation": english_translation,
                }
            ],
            priority=True,
        )

        word_dict = new_word.to_dict()
        word_dict["is_in_vocabulary"] = True
        word_dict["mastery_level"] = 0
        word_dict["times_practiced"] = 0
        word_dict["last_practiced"] = None

        return jsonify(
            {
                "success": True,
                "message": f"Successfully added '{serbian_word}' to your vocabulary",
                "word": word_dict,
                "queued_for_image": True,
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error adding suggested word: {e}")
        return jsonify({"error": "Failed to add word"}), 500


@app.route("/api/process-text", methods=["POST", "OPTIONS"])
@jwt_required()
def process_text():
    if request.method == "OPTIONS":
        return "", 200
    try:
        # Get user's OpenAI API key
        user_id = get_jwt_identity()
        api_key = get_user_openai_key(int(user_id))

        if not api_key:
            return jsonify(
                {"error": "Please configure your OpenAI API key in settings"}
            ), 400

        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Text is required"}), 400

        # Get available categories
        categories = Category.query.all()
        categories_list = [{"id": cat.id, "name": cat.name} for cat in categories]

        # Get user's excluded words to filter them out
        user_id_int = int(user_id)
        excluded_word_ids = set(
            ew.word_id for ew in ExcludedWord.query.filter_by(user_id=user_id_int).all()
        )

        # Get the excluded word strings
        if excluded_word_ids:
            excluded_words_objs = Word.query.filter(
                Word.id.in_(excluded_word_ids)
            ).all()
            excluded_words = set(
                word.serbian_word.lower() for word in excluded_words_objs
            )
        else:
            excluded_words = set()

        # Create optimized text processor
        try:
            processor = OptimizedSerbianTextProcessor(
                openai_api_key=api_key,
                redis_client=redis_client,
                model=config.OPENAI_MODEL,
            )

            # Process text with optimization features
            result = processor.process_text_optimized(
                text=text,
                categories=categories_list,
                max_words=20,
                temperature=config.OPENAI_TEMPERATURE,
                use_cache=True,
                excluded_words=excluded_words,
            )

            # Return the result in the expected format
            return jsonify(result)

        except Exception as processor_error:
            print(f"Optimized processor error: {processor_error}")
            # Fallback to basic processing if optimized processor fails
            return jsonify(
                {"error": f"Text processing error: {str(processor_error)}"}
            ), 500

    except Exception as e:
        print(f"Error processing text: {e}")
        return jsonify({"error": "Failed to process text"}), 500


@app.route("/api/words", methods=["POST"])
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

        for word_data in words:
            try:
                # Always create a new word for each user - no sharing between users
                # This ensures complete isolation of vocabulary between users
                new_word = Word(
                    serbian_word=word_data["serbian_word"],
                    english_translation=word_data["english_translation"],
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
                print(f'Error processing word "{word_data["serbian_word"]}": {e}')

        db.session.commit()

        return jsonify(
            {
                "inserted": len(inserted_words),
                "words": inserted_words,
                "added_to_vocabulary": len(added_to_vocabulary),
                "vocabulary_words": added_to_vocabulary,
            }
        )
    except Exception as e:
        db.session.rollback()
        print(f"Error adding words: {e}")
        return jsonify({"error": "Failed to add words"}), 500


@app.route("/api/practice/words")
@jwt_required()
def get_practice_words():
    try:
        user_id = int(get_jwt_identity())
        limit = int(request.args.get("limit", 10))
        difficulty = request.args.get("difficulty")

        # First, let's check if the user has any vocabulary at all
        user_vocab_count = UserVocabulary.query.filter_by(user_id=user_id).count()
        print(f"User {user_id} has {user_vocab_count} words in vocabulary")

        # Get user's excluded word IDs to filter them out from practice
        excluded_word_ids = set(
            ew.word_id for ew in ExcludedWord.query.filter_by(user_id=user_id).all()
        )

        # Build query for user's words - include all words in user's vocabulary for practice
        # Exclude words that are in the excluded list
        query = (
            db.session.query(Word)
            .join(UserVocabulary)
            .filter(
                UserVocabulary.user_id == user_id,
                ~Word.id.in_(excluded_word_ids) if excluded_word_ids else True,
            )
            .options(joinedload(Word.category))
        )

        if difficulty:
            query = query.filter(Word.difficulty_level == difficulty)

        # Order by last practiced (oldest first) and mastery level
        # This ensures unpracticed words (NULL last_practiced) come first
        query = query.order_by(
            func.coalesce(UserVocabulary.last_practiced, datetime(1900, 1, 1)).asc(),
            UserVocabulary.mastery_level.asc(),
        ).limit(limit)

        words = query.all()
        print(f"Query returned {len(words)} words for practice")

        # For each word, get 3 random incorrect options
        practice_words = []
        for word in words:
            # Get user-specific vocabulary data
            user_vocab = UserVocabulary.query.filter_by(
                user_id=user_id, word_id=word.id
            ).first()

            # Get random incorrect options
            incorrect_words = (
                Word.query.filter(Word.id != word.id)
                .order_by(func.random())
                .limit(3)
                .all()
            )

            incorrect_options = [w.english_translation for w in incorrect_words]
            all_options = [word.english_translation] + incorrect_options

            # Shuffle options
            random.shuffle(all_options)

            word_dict = word.to_dict()
            if user_vocab:
                word_dict["mastery_level"] = user_vocab.mastery_level
                word_dict["times_practiced"] = user_vocab.times_practiced

            word_dict.update(
                {"options": all_options, "correct_answer": word.english_translation}
            )

            practice_words.append(word_dict)

        return jsonify(practice_words)
    except Exception as e:
        print(f"Error fetching practice words: {e}")
        return jsonify({"error": "Failed to fetch practice words"}), 500


@app.route("/api/practice/example-sentence", methods=["POST"])
@jwt_required()
def generate_example_sentence():
    try:
        # Get user's OpenAI API key
        user_id = get_jwt_identity()
        api_key = get_user_openai_key(int(user_id))

        if not api_key:
            return jsonify(
                {"error": "Please configure your OpenAI API key in settings"}
            ), 400

        data = request.get_json()
        serbian_word = data.get("serbian_word")
        english_translation = data.get("english_translation")

        completion = openai.ChatCompletion.create(
            api_key=api_key,
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a Serbian language teacher. Create a simple Serbian sentence using the given word. The sentence should be easy to understand and help reinforce the word's meaning.",
                },
                {
                    "role": "user",
                    "content": f'Create a Serbian sentence using the word "{serbian_word}" ({english_translation}). Keep it simple and educational.',
                },
            ],
            temperature=0.7,
            max_tokens=100,
        )

        sentence = completion.choices[0].message["content"].strip()
        return jsonify({"sentence": sentence})
    except Exception as e:
        print(f"Error generating example sentence: {e}")
        return jsonify({"error": "Failed to generate example sentence"}), 500


@app.route("/api/practice/start", methods=["POST"])
@jwt_required()
def start_practice_session():
    try:
        user_id = int(get_jwt_identity())
        session = PracticeSession(user_id=user_id)
        db.session.add(session)
        db.session.commit()
        return jsonify(session.to_dict())
    except Exception as e:
        db.session.rollback()
        print(f"Error starting practice session: {e}")
        return jsonify({"error": "Failed to start practice session"}), 500


@app.route("/api/practice/submit", methods=["POST"])
@jwt_required()
def submit_practice_result():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        session_id = data.get("session_id")
        word_id = data.get("word_id")
        was_correct = data.get("was_correct")
        response_time_seconds = data.get("response_time_seconds")

        # Verify session belongs to user
        session = PracticeSession.query.filter_by(
            id=session_id, user_id=user_id
        ).first()

        if not session:
            return jsonify({"error": "Invalid session"}), 403

        # Record the result
        result = PracticeResult(
            session_id=session_id,
            word_id=word_id,
            was_correct=was_correct,
            response_time_seconds=response_time_seconds,
        )
        db.session.add(result)

        # Update user vocabulary stats
        user_vocab = UserVocabulary.query.filter_by(
            user_id=user_id, word_id=word_id
        ).first()

        if user_vocab:
            user_vocab.times_practiced += 1
            user_vocab.last_practiced = datetime.utcnow()

            if was_correct:
                user_vocab.times_correct += 1
                user_vocab.mastery_level = min(user_vocab.mastery_level + 10, 100)
            else:
                user_vocab.mastery_level = max(user_vocab.mastery_level - 5, 0)

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        print(f"Error submitting practice result: {e}")
        return jsonify({"error": "Failed to submit practice result"}), 500


@app.route("/api/practice/complete", methods=["POST"])
@jwt_required()
def complete_practice_session():
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        session_id = data.get("session_id")
        duration_seconds = data.get("duration_seconds")

        # Get session and verify it belongs to user
        session = PracticeSession.query.filter_by(
            id=session_id, user_id=user_id
        ).first()

        if not session:
            return jsonify({"error": "Session not found"}), 404

        # Get session statistics
        results = session.practice_results.all()
        total_questions = len(results)
        correct_answers = sum(1 for r in results if r.was_correct)

        # Update session
        session.total_questions = total_questions
        session.correct_answers = correct_answers
        session.duration_seconds = duration_seconds

        db.session.commit()

        return jsonify(
            {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "accuracy": round((correct_answers / total_questions) * 100)
                if total_questions > 0
                else 0,
            }
        )
    except Exception as e:
        db.session.rollback()
        print(f"Error completing practice session: {e}")
        return jsonify({"error": "Failed to complete practice session"}), 500


@app.route("/api/stats")
@jwt_required()
def get_user_stats():
    try:
        user_id = int(get_jwt_identity())

        # Total words in the system
        total_words = Word.query.count()

        # User's vocabulary words
        user_vocabulary_count = UserVocabulary.query.filter_by(user_id=user_id).count()

        # User's learned words (practiced at least once)
        learned_words = UserVocabulary.query.filter(
            UserVocabulary.user_id == user_id, UserVocabulary.times_practiced > 0
        ).count()

        # User's mastered words
        mastered_words = UserVocabulary.query.filter(
            UserVocabulary.user_id == user_id, UserVocabulary.mastery_level >= 80
        ).count()

        # User's recent sessions
        recent_sessions = (
            PracticeSession.query.filter(
                PracticeSession.user_id == user_id, PracticeSession.total_questions > 0
            )
            .order_by(PracticeSession.session_date.desc())
            .limit(10)
            .all()
        )

        return jsonify(
            {
                "total_words": total_words,
                "user_vocabulary_count": user_vocabulary_count,
                "learned_words": learned_words,
                "mastered_words": mastered_words,
                "recent_sessions": [session.to_dict() for session in recent_sessions],
            }
        )
    except Exception as e:
        print(f"Error fetching statistics: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500


# Helper function to clean HTML content
def clean_html_content(html_content):
    """Remove HTML tags and clean up content"""
    # Remove script and style elements
    html_content = re.sub(
        r"<script\b[^<]*(?:(?!</script>)<[^<]*)*</script>",
        "",
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    html_content = re.sub(
        r"<style\b[^<]*(?:(?!</style>)<[^<]*)*</style>",
        "",
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove all HTML tags
    html_content = re.sub(r"<[^>]+>", "", html_content)

    # Decode HTML entities
    html_content = html_content.replace("&nbsp;", " ")
    html_content = html_content.replace("&quot;", '"')
    html_content = html_content.replace("&#39;", "'")
    html_content = html_content.replace("&amp;", "&")
    html_content = html_content.replace("&lt;", "<")
    html_content = html_content.replace("&gt;", ">")

    # Clean up whitespace
    html_content = re.sub(r"\s+", " ", html_content)
    html_content = re.sub(r"\n\s*\n\s*\n", "\n\n", html_content)

    return html_content.strip()


# Helper function to fetch full article content
def fetch_full_article(url):
    """Fetch and extract article content from URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "sr,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Ensure UTF-8 encoding
        response.encoding = "utf-8"

        html = response.text
        content = ""

        # N1 Info specific patterns
        patterns = [
            r'<div[^>]*class="[^"]*rich-text[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r'<div[^>]*class="[^"]*article__text[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r'<div[^>]*class="[^"]*text-editor[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r'<div[^>]*class="[^"]*entry-content[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
            r"<article[^>]*>([\s\S]*?)</article>",
            r'<div[^>]*class="[^"]*content[^"]*"[^>]*>([\s\S]*?)(?=</div>(?:\s*<div|$))',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, html, re.IGNORECASE)
            for match in matches:
                if match.group(1):
                    paragraphs = re.findall(
                        r"<p[^>]*>([\s\S]*?)</p>", match.group(1), re.IGNORECASE
                    )
                    if paragraphs:
                        extracted_content = "\n\n".join(
                            [
                                clean_html_content(p)
                                for p in paragraphs
                                if len(clean_html_content(p)) > 20
                            ]
                        )
                        if len(extracted_content) > len(content):
                            content = extracted_content

        # If no content found with specific patterns, try general approach
        if not content or len(content) < 200:
            all_paragraphs = re.findall(r"<p[^>]*>[\s\S]*?</p>", html, re.IGNORECASE)
            paragraph_texts = []
            for p in all_paragraphs:
                text = clean_html_content(p)
                if (
                    len(text) > 50
                    and "Cookie" not in text
                    and "cookie" not in text
                    and "Prihvati" not in text
                    and "Saglasnost" not in text
                    and "©" not in text
                ):
                    paragraph_texts.append(text)

            if len(paragraph_texts) > 3:
                content = "\n\n".join(paragraph_texts[:-2])

        return content if len(content) > 300 else None
    except Exception as e:
        print(f"Error fetching full article: {e}")
        return None


@app.route("/api/news/sources")
def get_news_sources():
    sources = {
        "all": {"name": "All Sources", "value": ""},
        "n1info": {
            "name": "N1 Info",
            "value": "n1info",
            "categories": [
                "all",
                "vesti",
                "biznis",
                "sport",
                "kultura",
                "sci-tech",
                "region",
            ],
        },
        "blic": {
            "name": "Blic",
            "value": "blic",
            "categories": ["all", "vesti", "sport", "zabava", "kultura"],
        },
        "b92": {
            "name": "B92",
            "value": "b92",
            "categories": ["all", "vesti", "sport", "biz", "tehnopolis"],
        },
    }

    categories = {
        "all": "All Categories",
        "vesti": "News",
        "sport": "Sports",
        "kultura": "Culture",
        "biznis": "Business",
        "sci-tech": "Science & Tech",
        "region": "Region",
        "zabava": "Entertainment",
        "biz": "Business",
        "tehnopolis": "Technology",
    }

    return jsonify({"sources": sources, "categories": categories})


@app.route("/api/top100/categories/<int:category_id>")
@jwt_required()
def get_top_100_words_by_category(category_id):
    """Get top 100 words for a specific category"""
    try:
        user_id = int(get_jwt_identity())

        # Get category
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": "Category not found"}), 404

        # Get top 100 words for this category
        words = (
            Word.query.filter_by(category_id=category_id, is_top_100=True)
            .order_by(Word.serbian_word)
            .all()
        )

        # Get user's vocabulary word IDs for quick lookup
        user_word_ids = set(
            uv.word_id for uv in UserVocabulary.query.filter_by(user_id=user_id).all()
        )

        # Build response with user-specific data
        words_data = []
        for word in words:
            word_dict = word.to_dict()
            word_dict["is_in_vocabulary"] = word.id in user_word_ids

            # Get user-specific vocabulary data if the word is in their vocabulary
            if word.id in user_word_ids:
                user_vocab = UserVocabulary.query.filter_by(
                    user_id=user_id, word_id=word.id
                ).first()
                if user_vocab:
                    word_dict["mastery_level"] = user_vocab.mastery_level
                    word_dict["times_practiced"] = user_vocab.times_practiced
                    word_dict["last_practiced"] = (
                        user_vocab.last_practiced.isoformat()
                        if user_vocab.last_practiced
                        else None
                    )
            else:
                word_dict["mastery_level"] = 0
                word_dict["times_practiced"] = 0
                word_dict["last_practiced"] = None

            words_data.append(word_dict)

        return jsonify(
            {
                "category": category.to_dict(),
                "words": words_data,
                "total": len(words_data),
                "added_count": len([w for w in words_data if w["is_in_vocabulary"]]),
            }
        )
    except Exception as e:
        print(f"Error fetching top 100 words: {e}")
        return jsonify({"error": "Failed to fetch top 100 words"}), 500


@app.route("/api/top100/add", methods=["POST"])
@jwt_required()
def add_top_100_words_to_vocabulary():
    """Add selected top 100 words to user's vocabulary"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        word_ids = data.get("word_ids", [])

        if not word_ids or not isinstance(word_ids, list):
            return jsonify({"error": "word_ids array is required"}), 400

        added_words = []
        already_in_vocabulary = []

        for word_id in word_ids:
            # Check if word exists and is a top 100 word
            word = Word.query.filter_by(id=word_id, is_top_100=True).first()
            if not word:
                continue

            # Check if already in user's vocabulary
            existing = UserVocabulary.query.filter_by(
                user_id=user_id, word_id=word_id
            ).first()

            if existing:
                already_in_vocabulary.append(word.to_dict())
            else:
                # Add to user's vocabulary
                user_vocab = UserVocabulary(user_id=user_id, word_id=word_id)
                db.session.add(user_vocab)
                added_words.append(word.to_dict())

        db.session.commit()

        return jsonify(
            {
                "added": len(added_words),
                "already_in_vocabulary": len(already_in_vocabulary),
                "added_words": added_words,
                "skipped_words": already_in_vocabulary,
            }
        )
    except Exception as e:
        db.session.rollback()
        print(f"Error adding top 100 words: {e}")
        return jsonify({"error": "Failed to add words"}), 500


@app.route("/api/news")
def get_news():
    try:
        source = request.args.get("source", "all")
        category = request.args.get("category", "all")

        # Try to get from Redis cache first
        try:
            # Construct cache key
            if source and source != "all":
                cache_key = f"news:{source}:{category if category else 'all'}"
            else:
                cache_key = "news:all:all"

            # Check if we have cached articles
            cached_articles = redis_client.get(cache_key)
            if cached_articles:
                articles = json.loads(cached_articles)

                # Filter by category if needed and not already filtered
                if category and category != "all" and source == "all":
                    articles = [a for a in articles if a.get("category") == category]

                # Get last update time
                last_update = redis_client.get("news:last_update")

                return jsonify(
                    {
                        "articles": articles[:20],  # Return top 20 articles
                        "from_cache": True,
                        "last_update": last_update,
                    }
                )
        except Exception as redis_error:
            print(f"Redis error, falling back to RSS feeds: {redis_error}")

        # If no cache or Redis error, try to fetch from RSS feed
        if RSS_PARSER_AVAILABLE:
            try:
                # Define available RSS feeds with categories
                all_rss_feeds = {
                    "n1info": {
                        "url": "https://n1info.rs/feed/",
                        "name": "N1 Info",
                        "categories": {
                            "all": "https://n1info.rs/feed/",
                            "vesti": "https://n1info.rs/vesti/feed/",
                            "biznis": "https://n1info.rs/biznis/feed/",
                            "sport": "https://n1info.rs/sport/feed/",
                            "kultura": "https://n1info.rs/kultura/feed/",
                            "sci-tech": "https://n1info.rs/sci-tech/feed/",
                            "region": "https://n1info.rs/region/feed/",
                        },
                    },
                    "blic": {
                        "url": "https://www.blic.rs/rss/danasnje-vesti",
                        "name": "Blic",
                        "categories": {
                            "all": "https://www.blic.rs/rss/danasnje-vesti",
                            "vesti": "https://www.blic.rs/rss/vesti",
                            "sport": "https://www.blic.rs/rss/sport",
                            "zabava": "https://www.blic.rs/rss/zabava",
                            "kultura": "https://www.blic.rs/rss/kultura",
                        },
                    },
                    "b92": {
                        "url": "https://www.b92.net/info/rss/danas.xml",
                        "name": "B92",
                        "categories": {
                            "all": "https://www.b92.net/info/rss/danas.xml",
                            "vesti": "https://www.b92.net/info/rss/vesti.xml",
                            "sport": "https://www.b92.net/info/rss/sport.xml",
                            "biz": "https://www.b92.net/info/rss/biz.xml",
                            "tehnopolis": "https://www.b92.net/info/rss/tehnopolis.xml",
                        },
                    },
                }

                # Determine which feeds to use
                feeds_to_use = []
                if source and source in all_rss_feeds:
                    source_feed = all_rss_feeds[source]
                    category_url = source_feed["categories"].get(
                        category, source_feed["categories"]["all"]
                    )
                    feeds_to_use = [{"url": category_url, "name": source_feed["name"]}]
                else:
                    for key, feed in all_rss_feeds.items():
                        category_url = feed["categories"].get(
                            category, feed["categories"]["all"]
                        )
                        feeds_to_use.append({"url": category_url, "name": feed["name"]})

                articles = []

                for feed_info in feeds_to_use:
                    try:
                        # Set up headers to request UTF-8 encoding
                        headers = {
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept-Charset": "utf-8",
                            "Accept-Encoding": "gzip, deflate",
                        }

                        # Parse the feed with proper encoding handling
                        feed = feedparser.parse(
                            feed_info["url"], request_headers=headers
                        )

                        # Ensure proper encoding
                        if hasattr(feed, "encoding"):
                            if feed.encoding and feed.encoding.lower() not in [
                                "utf-8",
                                "utf8",
                            ]:
                                # Re-parse with explicit UTF-8 encoding
                                try:
                                    response = requests.get(
                                        feed_info["url"], headers=headers, timeout=10
                                    )
                                    response.encoding = "utf-8"
                                    feed = feedparser.parse(response.text)
                                except:
                                    pass  # Continue with original feed if re-parsing fails

                        # Transform RSS items to our article format
                        for item in feed.entries[:5]:
                            # Get content from various possible fields
                            content = ""
                            if hasattr(item, "content") and item.content:
                                content = (
                                    item.content[0].value
                                    if isinstance(item.content, list)
                                    else item.content
                                )
                            elif hasattr(item, "description"):
                                content = item.description
                            elif hasattr(item, "summary"):
                                content = item.summary

                            # Clean the content
                            content = clean_html_content(content)

                            article_link = (
                                item.link
                                if hasattr(item, "link")
                                else item.get("guid", "")
                            )

                            articles.append(
                                {
                                    "title": item.title
                                    if hasattr(item, "title")
                                    else "Bez naslova",
                                    "content": content or "Sadržaj nije dostupan.",
                                    "source": feed_info["name"],
                                    "date": datetime(
                                        *item.published_parsed[:6]
                                    ).strftime("%d.%m.%Y")
                                    if hasattr(item, "published_parsed")
                                    else datetime.now().strftime("%d.%m.%Y"),
                                    "category": item.categories[0].term
                                    if hasattr(item, "categories") and item.categories
                                    else "Vesti",
                                    "link": article_link,
                                    "needsFullContent": len(content) < 400,
                                }
                            )

                        if len(articles) >= 10:
                            break

                    except Exception as feed_error:
                        print(f"Error fetching feed {feed_info['url']}: {feed_error}")
                        continue

                # If we got some articles from RSS
                if articles:
                    articles = articles[:10]

                    # Try to fetch full content for articles that need it
                    for i, article in enumerate(articles):
                        if article["needsFullContent"] and article["link"]:
                            full_content = fetch_full_article(article["link"])
                            if full_content and len(full_content) > len(
                                article["content"]
                            ):
                                articles[i]["content"] = full_content
                                articles[i]["fullContentFetched"] = True
                                articles[i]["needsFullContent"] = False

                    return jsonify({"articles": articles})
            except Exception as rss_error:
                print(f"RSS feed error, falling back to sample articles: {rss_error}")
        else:
            print("RSS parser not available, using sample articles")

        # Fallback to sample articles
        articles = [
            {
                "title": "Novi most preko Dunava uskoro završen",
                "content": "Radovi na izgradnji novog mosta preko Dunava ulaze u završnu fazu. Gradonačelnik je izjavio da će most biti otvoren za saobraćaj do kraja godine. Ovaj projekat predstavlja jednu od najvećih investicija u infrastrukturu u poslednjih deset godina. Most će značajno poboljšati saobraćajnu povezanost između dva dela grada i smanjiti gužve na postojećim mostovima. Ukupna vrednost investicije iznosi preko 100 miliona evra. Novi most će imati šest traka za vozila, kao i posebne staze za bicikliste i pešake. Očekuje se da će preko mosta dnevno prelaziti više od 50.000 vozila.",
                "source": "Dnevne novosti",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "category": "Infrastruktura",
            },
            {
                "title": "Otvorena nova biblioteka u centru grada",
                "content": "Danas je svečano otvorena nova gradska biblioteka koja se nalazi u samom centru grada. Biblioteka raspolaže sa preko 100.000 knjiga i modernom čitaonicom. Posebna pažnja posvećena je dečjem odeljenju koje ima interaktivne sadržaje za najmlađe čitaoce. U biblioteci se nalazi i multimedijalna sala za predavanja i kulturne događaje. Radno vreme biblioteke je od 8 do 20 časova svakog dana osim nedelje. Članarina je besplatna za učenike i studente. Direktorka biblioteke istakla je da će ustanova organizovati brojne književne večeri i radionice za decu.",
                "source": "Kulturni pregled",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "category": "Kultura",
            },
            {
                "title": "Uspešna žetva pšenice ove godine",
                "content": "Poljoprivrednici širom zemlje izveštavaju o uspešnoj žetvi pšenice. Prinosi su iznad proseka zahvaljujući povoljnim vremenskim uslovima tokom proleća. Ministarstvo poljoprivrede saopštilo je da će otkupna cena pšenice biti stabilna. Očekuje se da će ukupan prinos premašiti prošlogodišnji za oko 15 procenata. Kvalitet pšenice je izuzetan, što će omogućiti značajan izvoz. Mnogi poljoprivrednici su zadovoljni ovogodišnjom žetvom i planiraju da prošire zasejane površine sledeće godine. Država je obećala subvencije za nabavku nove mehanizacije.",
                "source": "Poljoprivredni glasnik",
                "date": datetime.now().strftime("%d.%m.%Y"),
                "category": "Poljoprivreda",
            },
        ]

        return jsonify({"articles": articles})
    except Exception as e:
        print(f"Error fetching news: {e}")
        return jsonify({"error": "Failed to fetch news articles"}), 500


# Image service endpoints
@app.route("/api/words/<int:word_id>/image")
@jwt_required()
def get_word_image(word_id):
    """Get image for a specific word"""
    try:
        user_id = int(get_jwt_identity())

        # Verify the word belongs to the user's vocabulary
        user_vocab = UserVocabulary.query.filter_by(
            user_id=user_id, word_id=word_id
        ).first()

        if not user_vocab:
            return jsonify({"error": "Word not found in your vocabulary"}), 404

        # Get the word details
        word = Word.query.get(word_id)
        if not word:
            return jsonify({"error": "Word not found"}), 404

        # Get image from service
        image_data = image_service.get_word_image(
            word.serbian_word, word.english_translation
        )

        if image_data and "error" not in image_data:
            return jsonify({"success": True, "image": image_data})
        else:
            return jsonify(
                {
                    "success": False,
                    "error": image_data.get("error", "No image found")
                    if image_data
                    else "No image found",
                }
            )

    except Exception as e:
        print(f"Error getting word image: {e}")
        return jsonify({"error": "Failed to get word image"}), 500


@app.route("/api/images/search", methods=["POST"])
@jwt_required()
def search_image():
    """Search for an image by word"""
    try:
        data = request.get_json()
        serbian_word = data.get("serbian_word")
        english_translation = data.get("english_translation")

        if not serbian_word:
            return jsonify({"error": "Serbian word is required"}), 400

        # Get image from service
        image_data = image_service.get_word_image(serbian_word, english_translation)

        if image_data and "error" not in image_data:
            return jsonify({"success": True, "image": image_data})
        else:
            return jsonify(
                {
                    "success": False,
                    "error": image_data.get("error", "No image found")
                    if image_data
                    else "No image found",
                }
            )

    except Exception as e:
        print(f"Error searching for image: {e}")
        return jsonify({"error": "Failed to search for image"}), 500


@app.route("/api/images/cache/clear", methods=["POST"])
@jwt_required()
def clear_image_cache():
    """Clear image cache for a specific word"""
    try:
        data = request.get_json()
        serbian_word = data.get("serbian_word")

        if not serbian_word:
            return jsonify({"error": "Serbian word is required"}), 400

        success = image_service.clear_word_image_cache(serbian_word)

        return jsonify(
            {
                "success": success,
                "message": f"Cache cleared for word '{serbian_word}'"
                if success
                else "Failed to clear cache",
            }
        )

    except Exception as e:
        print(f"Error clearing image cache: {e}")
        return jsonify({"error": "Failed to clear image cache"}), 500


@app.route("/api/images/cache/stats")
@jwt_required()
def get_image_cache_stats():
    """Get image cache statistics"""
    try:
        stats = image_service.get_cache_stats()
        return jsonify({"stats": stats})

    except Exception as e:
        print(f"Error getting cache stats: {e}")
        return jsonify({"error": "Failed to get cache stats"}), 500


@app.route("/api/images/background/status")
@jwt_required()
def get_background_status():
    """Get background image processing status"""
    try:
        status = image_service.get_background_status()
        return jsonify({"status": status})

    except Exception as e:
        print(f"Error getting background status: {e}")
        return jsonify({"error": "Failed to get background status"}), 500


@app.route("/api/images/background/populate", methods=["POST"])
@jwt_required()
def populate_images():
    """Populate images for user's vocabulary words in background"""
    try:
        user_id = int(get_jwt_identity())

        # Get user's vocabulary words that don't have images
        user_words = (
            db.session.query(Word)
            .join(UserVocabulary)
            .filter(UserVocabulary.user_id == user_id)
            .all()
        )

        # Convert to format expected by image service
        words_list = [
            {
                "serbian_word": word.serbian_word,
                "english_translation": word.english_translation,
            }
            for word in user_words
        ]

        added_count = image_service.populate_images_for_words(words_list)

        return jsonify(
            {
                "message": f"Added {added_count} words to background processing queue",
                "total_vocabulary_words": len(user_words),
                "queued_for_processing": added_count,
            }
        )

    except Exception as e:
        print(f"Error populating images: {e}")
        return jsonify({"error": "Failed to populate images"}), 500


@app.route("/api/images/immediate", methods=["POST"])
@jwt_required()
def get_image_immediate():
    """Get image immediately (for testing/admin) - respects rate limits"""
    try:
        data = request.get_json()
        serbian_word = data.get("serbian_word")
        english_translation = data.get("english_translation")

        if not serbian_word:
            return jsonify({"error": "Serbian word is required"}), 400

        # Use immediate processing method
        image_data = image_service.get_word_image_immediate(
            serbian_word, english_translation
        )

        if image_data and "error" not in image_data:
            return jsonify({"success": True, "image": image_data})
        else:
            return jsonify(
                {
                    "success": False,
                    "error": image_data.get("error", "No image found")
                    if image_data
                    else "No image found",
                }
            )

    except Exception as e:
        print(f"Error getting immediate image: {e}")
        return jsonify({"error": "Failed to get immediate image"}), 500


@app.route("/api/images/populate-queue", methods=["POST"])
@jwt_required()
def populate_image_queue():
    """Trigger population of image queue with vocabulary and top 100 words"""
    try:
        from image_queue_populator import ImageQueuePopulator

        populator = ImageQueuePopulator()

        # Run population cycle
        data = request.get_json() or {}
        population_type = data.get("type", "all")  # all, top100, vocabulary, recent

        if population_type == "top100":
            added_count = populator.populate_top_100_words()
        elif population_type == "vocabulary":
            added_count = populator.populate_user_vocabulary_words()
        elif population_type == "recent":
            days = data.get("days", 7)
            added_count = populator.populate_recent_words(days)
        else:  # all
            # Get initial status
            initial_status = populator.get_queue_status()

            # Run full population cycle
            total_added = 0
            total_added += populator.populate_top_100_words()
            total_added += populator.populate_user_vocabulary_words()
            total_added += populator.populate_recent_words(days=7)
            added_count = total_added

        # Get final status
        final_status = populator.get_queue_status()

        return jsonify(
            {
                "success": True,
                "message": f"Added {added_count} words to image processing queue",
                "added_count": added_count,
                "queue_status": final_status,
            }
        )

    except Exception as e:
        print(f"Error populating image queue: {e}")
        return jsonify({"error": "Failed to populate image queue"}), 500


# Excluded words endpoints
@app.route("/api/excluded-words")
@jwt_required()
def get_excluded_words():
    """Get user's excluded words"""
    try:
        user_id = int(get_jwt_identity())

        excluded_words = (
            db.session.query(ExcludedWord)
            .filter_by(user_id=user_id)
            .options(joinedload(ExcludedWord.word).joinedload(Word.category))
            .order_by(ExcludedWord.created_at.desc())
            .all()
        )

        excluded_words_data = []
        for excluded in excluded_words:
            excluded_dict = excluded.to_dict()
            excluded_words_data.append(excluded_dict)

        return jsonify(excluded_words_data)

    except Exception as e:
        print(f"Error fetching excluded words: {e}")
        return jsonify({"error": "Failed to fetch excluded words"}), 500


@app.route("/api/words/<int:word_id>/exclude", methods=["POST"])
@jwt_required()
def exclude_word_from_vocabulary(word_id):
    """Remove word from vocabulary and add to excluded words"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json() or {}
        reason = data.get("reason", "manual_removal")

        # Check if word exists in user's vocabulary
        user_vocab = UserVocabulary.query.filter_by(
            user_id=user_id, word_id=word_id
        ).first()

        if not user_vocab:
            return jsonify({"error": "Word not found in your vocabulary"}), 404

        # Get the word
        word = Word.query.get(word_id)
        if not word:
            return jsonify({"error": "Word not found"}), 404

        # Check if already excluded
        existing_excluded = ExcludedWord.query.filter_by(
            user_id=user_id, word_id=word_id
        ).first()

        if existing_excluded:
            return jsonify({"error": "Word is already excluded"}), 400

        # Remove from vocabulary
        db.session.delete(user_vocab)

        # Add to excluded words
        excluded_word = ExcludedWord(user_id=user_id, word_id=word_id, reason=reason)
        db.session.add(excluded_word)

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Word '{word.serbian_word}' removed from vocabulary and excluded",
                "excluded_word": excluded_word.to_dict(),
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error excluding word: {e}")
        return jsonify({"error": "Failed to exclude word"}), 500


@app.route("/api/excluded-words/<int:excluded_word_id>", methods=["DELETE"])
@jwt_required()
def remove_from_excluded_words(excluded_word_id):
    """Remove word from excluded list (allows it to be added back to vocabulary)"""
    try:
        user_id = int(get_jwt_identity())

        excluded_word = ExcludedWord.query.filter_by(
            id=excluded_word_id, user_id=user_id
        ).first()

        if not excluded_word:
            return jsonify({"error": "Excluded word not found"}), 404

        word = excluded_word.word
        db.session.delete(excluded_word)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Word '{word.serbian_word}' removed from excluded list",
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error removing from excluded words: {e}")
        return jsonify({"error": "Failed to remove from excluded words"}), 500


@app.route("/api/excluded-words/bulk", methods=["POST"])
@jwt_required()
def bulk_exclude_words():
    """Add multiple words to excluded list (used by news parser)"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        words_data = data.get("words", [])
        reason = data.get("reason", "news_parser_skip")

        if not words_data or not isinstance(words_data, list):
            return jsonify({"error": "Words array is required"}), 400

        excluded_count = 0
        already_excluded = 0

        for word_data in words_data:
            serbian_word = word_data.get("serbian_word")
            english_translation = word_data.get("english_translation")

            if not serbian_word or not english_translation:
                continue

            # Find or create the word
            word = Word.query.filter_by(
                serbian_word=serbian_word, english_translation=english_translation
            ).first()

            if not word:
                # Create the word if it doesn't exist
                word = Word(
                    serbian_word=serbian_word,
                    english_translation=english_translation,
                    category_id=word_data.get("category_id", 1),
                )
                db.session.add(word)
                db.session.flush()

            # Check if already excluded
            existing_excluded = ExcludedWord.query.filter_by(
                user_id=user_id, word_id=word.id
            ).first()

            if existing_excluded:
                already_excluded += 1
                continue

            # Add to excluded words
            excluded_word = ExcludedWord(
                user_id=user_id, word_id=word.id, reason=reason
            )
            db.session.add(excluded_word)
            excluded_count += 1

        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": f"Added {excluded_count} words to excluded list",
                "excluded_count": excluded_count,
                "already_excluded": already_excluded,
            }
        )

    except Exception as e:
        db.session.rollback()
        print(f"Error bulk excluding words: {e}")
        return jsonify({"error": "Failed to bulk exclude words"}), 500


# Text processing performance and cache endpoints
@app.route("/api/text-processing/stats")
@jwt_required()
def get_text_processing_stats():
    """Get text processing performance statistics"""
    try:
        user_id = get_jwt_identity()
        api_key = get_user_openai_key(int(user_id))

        if not api_key:
            return jsonify(
                {"error": "Please configure your OpenAI API key in settings"}
            ), 400

        # Create processor to get stats
        processor = OptimizedSerbianTextProcessor(
            openai_api_key=api_key,
            redis_client=redis_client,
            model=config.OPENAI_MODEL,
        )

        stats = processor.get_processing_stats()
        return jsonify(stats)

    except Exception as e:
        print(f"Error getting text processing stats: {e}")
        return jsonify({"error": "Failed to get processing stats"}), 500


@app.route("/api/text-processing/cache/clear", methods=["POST"])
@jwt_required()
def clear_text_processing_cache():
    """Clear text processing cache"""
    try:
        user_id = get_jwt_identity()
        api_key = get_user_openai_key(int(user_id))

        if not api_key:
            return jsonify(
                {"error": "Please configure your OpenAI API key in settings"}
            ), 400

        # Create processor to clear cache
        processor = OptimizedSerbianTextProcessor(
            openai_api_key=api_key,
            redis_client=redis_client,
            model=config.OPENAI_MODEL,
        )

        cleared_count = processor.clear_processing_cache()
        return jsonify(
            {
                "success": True,
                "message": f"Cleared {cleared_count} cache entries",
                "cleared_count": cleared_count,
            }
        )

    except Exception as e:
        print(f"Error clearing text processing cache: {e}")
        return jsonify({"error": "Failed to clear processing cache"}), 500


@app.route("/api/text-processing/cache/warm", methods=["POST"])
@jwt_required()
def warm_text_processing_cache():
    """Warm cache with user's vocabulary words"""
    try:
        user_id = get_jwt_identity()
        user_id_int = int(user_id)
        api_key = get_user_openai_key(user_id_int)

        if not api_key:
            return jsonify(
                {"error": "Please configure your OpenAI API key in settings"}
            ), 400

        # Get user's vocabulary words
        user_words = (
            db.session.query(Word)
            .join(UserVocabulary)
            .filter(UserVocabulary.user_id == user_id_int)
            .all()
        )

        vocabulary_data = []
        for word in user_words:
            vocabulary_data.append(
                {
                    "serbian_word": word.serbian_word,
                    "english_translation": word.english_translation,
                    "category_id": word.category_id,
                    "category_name": word.category.name
                    if word.category
                    else "Common Words",
                }
            )

        # Create processor and warm cache
        processor = OptimizedSerbianTextProcessor(
            openai_api_key=api_key,
            redis_client=redis_client,
            model=config.OPENAI_MODEL,
        )

        warmed_count = processor.warm_cache_with_vocabulary(vocabulary_data)
        return jsonify(
            {
                "success": True,
                "message": f"Cache warmed with {warmed_count} vocabulary words",
                "warmed_count": warmed_count,
                "total_vocabulary": len(vocabulary_data),
            }
        )

    except Exception as e:
        print(f"Error warming text processing cache: {e}")
        return jsonify({"error": "Failed to warm processing cache"}), 500


@app.route("/api/text-processing/analyze", methods=["POST"])
@jwt_required()
def analyze_text_patterns():
    """Analyze text patterns for optimization insights"""
    try:
        user_id = get_jwt_identity()
        api_key = get_user_openai_key(int(user_id))

        if not api_key:
            return jsonify(
                {"error": "Please configure your OpenAI API key in settings"}
            ), 400

        data = request.get_json()
        texts = data.get("texts", [])

        if not texts or not isinstance(texts, list):
            return jsonify({"error": "texts array is required"}), 400

        # Create processor and analyze patterns
        processor = OptimizedSerbianTextProcessor(
            openai_api_key=api_key,
            redis_client=redis_client,
            model=config.OPENAI_MODEL,
        )

        analysis = processor.analyze_text_patterns(texts)
        return jsonify(analysis)

    except Exception as e:
        print(f"Error analyzing text patterns: {e}")
        return jsonify({"error": "Failed to analyze text patterns"}), 500


@app.route("/api/translation-cache/stats")
@jwt_required()
def get_translation_cache_stats():
    """Get translation cache statistics"""
    try:
        # Create translation cache instance
        cache = TranslationCache(redis_client)
        stats = cache.get_stats()
        return jsonify(stats)

    except Exception as e:
        print(f"Error getting translation cache stats: {e}")
        return jsonify({"error": "Failed to get cache stats"}), 500


@app.route("/api/translation-cache/clear", methods=["POST"])
@jwt_required()
def clear_translation_cache():
    """Clear translation cache"""
    try:
        # Create translation cache instance
        cache = TranslationCache(redis_client)
        cleared_count = cache.clear_cache()
        return jsonify(
            {
                "success": True,
                "message": f"Cleared {cleared_count} translation cache entries",
                "cleared_count": cleared_count,
            }
        )

    except Exception as e:
        print(f"Error clearing translation cache: {e}")
        return jsonify({"error": "Failed to clear translation cache"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.APP_PORT, debug=config.DEBUG)
