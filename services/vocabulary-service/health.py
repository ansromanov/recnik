"""
Health check endpoint
"""

from flask import Blueprint, jsonify
from sqlalchemy import text

from models.database import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health")
def health_check():
    """Health check endpoint - no authentication required"""
    try:
        # Test database connection
        db.session.execute(text("SELECT 1"))

        return jsonify(
            {
                "status": "healthy",
                "service": "auth-service",
                "version": "1.0.0",
                "database": "connected",
            }
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "service": "auth-service",
                    "version": "1.0.0",
                    "database": "disconnected",
                    "error": str(e),
                }
            ),
            503,
        )
