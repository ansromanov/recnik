"""
Configuration settings for Recnik
Simple configuration without overengineering
"""

from datetime import timedelta
import os

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vocab_user:vocab_pass@localhost:5432/serbian_vocabulary",
)

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

# reCAPTCHA Configuration
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

# CORS Configuration
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "https://localhost:443,https://localhost:3000,http://localhost:3000,http://localhost:3001",
).split(",")

# Application Settings
APP_PORT = int(os.getenv("PORT", 3001))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Rate Limiting
UNSPLASH_RATE_LIMIT = 50  # requests per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# Queue Settings
QUEUE_POPULATION_INTERVAL = 30  # minutes
IMAGE_QUEUE_KEY = "image_queue"
CACHE_PREFIX = "word_image:"

# Database Pool Settings
DB_POOL_SIZE = 20
DB_POOL_RECYCLE = 3600
DB_POOL_PRE_PING = True

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Monitoring
METRICS_PATH = "/metrics"
METRICS_PREFIX = "flask"

# Text Processing
MAX_WORDS_PER_REQUEST = 50
OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_TEMPERATURE = 0.3
OPENAI_MAX_TOKENS = 150

# Image Processing
IMAGE_CACHE_TTL = 86400 * 7  # 7 days in seconds
MAX_IMAGE_SIZE = 1024 * 1024  # 1MB

# Background Services
CACHE_UPDATE_INTERVAL = 300  # 5 minutes
HEALTH_CHECK_TIMEOUT = 10  # seconds
