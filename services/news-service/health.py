from datetime import datetime
import os

import redis


def check_health():
    """Health check for news service"""
    health_status = {
        "service": "news-service",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {},
    }

    try:
        # Check Redis connection
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        redis_client.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health_status["checks"]["redis"] = {"status": "unhealthy", "message": str(e)}
        health_status["status"] = "unhealthy"

    try:
        # Check OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            health_status["checks"]["openai"] = {
                "status": "healthy",
                "message": "API key configured",
            }
        else:
            health_status["checks"]["openai"] = {
                "status": "warning",
                "message": "API key not configured",
            }
    except Exception as e:
        health_status["checks"]["openai"] = {"status": "unhealthy", "message": str(e)}

    # Check database connection would go here
    # For now, we'll assume it's healthy since we don't have direct DB access in this file
    health_status["checks"]["database"] = {
        "status": "assumed_healthy",
        "message": "Database check not implemented",
    }

    return health_status


def get_service_info():
    """Get service information"""
    return {
        "service": "news-service",
        "description": "Enhanced news service with formatting and LLM content generation",
        "version": "1.0.0",
        "features": [
            "Enhanced news formatting",
            "LLM-generated dialogues",
            "Content summaries",
            "Vocabulary-focused content",
            "Multiple content types",
        ],
        "endpoints": [
            "/health",
            "/metrics",
            "/api/news",
            "/api/news/sources",
            "/api/content/dialogue",
            "/api/content/summary",
            "/api/content/vocabulary-context",
        ],
    }
