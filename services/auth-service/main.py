#!/usr/bin/env python3
"""
Authentication Service
Handles user authentication, registration, and JWT token management.
"""

from datetime import timedelta
import os

from controllers.auth_controller import AuthController
from dotenv import load_dotenv
from flask import Flask, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    get_jwt_identity,
    jwt_required,
)
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
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "auth-service-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=24)
jwt = JWTManager(app)

# Initialize database
db.init_app(app)

# Setup logging
logger = setup_logger("auth-service")

# Setup Prometheus metrics
metrics = PrometheusMetrics(app)
metrics.info("auth_service_info", "Authentication Service", version="1.0.0")

# Initialize controller
auth_controller = AuthController(logger)

# Register blueprints
app.register_blueprint(health_bp)
app.register_blueprint(metrics_bp)


# Authentication routes
@app.route("/api/auth/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return "", 200

    logger.info(
        "Registration attempt",
        extra={
            "endpoint": "/api/auth/register",
            "method": "POST",
            "ip": request.remote_addr,
        },
    )

    return auth_controller.register(request)


@app.route("/api/auth/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200

    logger.info(
        "Login attempt",
        extra={
            "endpoint": "/api/auth/login",
            "method": "POST",
            "ip": request.remote_addr,
        },
    )

    return auth_controller.login(request)


@app.route("/api/auth/me")
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    logger.info("Get current user", extra={"endpoint": "/api/auth/me", "user_id": user_id})

    return auth_controller.get_current_user(user_id)


@app.route("/api/settings")
@jwt_required()
def get_settings():
    user_id = get_jwt_identity()
    logger.info("Get user settings", extra={"endpoint": "/api/settings", "user_id": user_id})

    return auth_controller.get_settings(user_id)


@app.route("/api/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    user_id = get_jwt_identity()
    logger.info(
        "Update user settings",
        extra={"endpoint": "/api/settings", "method": "PUT", "user_id": user_id},
    )

    return auth_controller.update_settings(user_id, request)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 3002))
    logger.info(
        "Starting Authentication Service",
        extra={"port": port, "environment": os.getenv("ENVIRONMENT", "development")},
    )

    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "false").lower() == "true")
