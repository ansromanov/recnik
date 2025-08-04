from datetime import datetime
import os

import redis


def get_metrics():
    """Get service metrics"""
    try:
        redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

        # Basic service metrics
        metrics = {
            "service": "news-service",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": get_uptime_seconds(),
            "cache": get_cache_metrics(redis_client),
            "content": get_content_metrics(redis_client),
            "requests": get_request_metrics(redis_client),
        }

        return metrics

    except Exception as e:
        return {
            "service": "news-service",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "status": "metrics_unavailable",
        }


def get_uptime_seconds():
    """Calculate service uptime (simplified)"""
    # This is a simplified implementation
    # In production, you'd track actual service start time
    return 3600  # Placeholder: 1 hour


def get_cache_metrics(redis_client):
    """Get cache-related metrics"""
    try:
        cache_metrics = {
            "formatted_news_keys": 0,
            "content_keys": 0,
            "total_keys": 0,
            "memory_usage": "unknown",
        }

        # Count formatted news cache keys
        formatted_keys = list(redis_client.scan_iter("formatted_news:*"))
        cache_metrics["formatted_news_keys"] = len(formatted_keys)

        # Count content cache keys
        content_keys = list(redis_client.scan_iter("content:*"))
        cache_metrics["content_keys"] = len(content_keys)

        # Total cache keys for this service
        cache_metrics["total_keys"] = (
            cache_metrics["formatted_news_keys"] + cache_metrics["content_keys"]
        )

        # Try to get memory info
        try:
            info = redis_client.info("memory")
            cache_metrics["memory_usage"] = info.get("used_memory_human", "unknown")
        except:
            pass

        return cache_metrics

    except Exception as e:
        return {"error": str(e)}


def get_content_metrics(redis_client):
    """Get content generation metrics"""
    try:
        # These would typically come from database queries
        # For now, return placeholder metrics
        content_metrics = {
            "dialogues_generated_today": get_daily_count(redis_client, "dialogue"),
            "summaries_generated_today": get_daily_count(redis_client, "summary"),
            "stories_generated_today": get_daily_count(redis_client, "story"),
            "total_content_items": get_total_count(redis_client, "content"),
            "cache_hit_rate": get_cache_hit_rate(redis_client),
        }

        return content_metrics

    except Exception as e:
        return {"error": str(e)}


def get_request_metrics(redis_client):
    """Get request-related metrics"""
    try:
        # These would be tracked by middleware in production
        request_metrics = {
            "news_requests_today": get_daily_count(redis_client, "news_requests"),
            "content_generation_requests_today": get_daily_count(redis_client, "content_requests"),
            "error_rate_percent": get_error_rate(redis_client),
            "avg_response_time_ms": get_avg_response_time(redis_client),
        }

        return request_metrics

    except Exception as e:
        return {"error": str(e)}


def get_daily_count(redis_client, metric_type):
    """Get daily count for a specific metric type"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        key = f"metrics:{metric_type}:{today}"
        count = redis_client.get(key)
        return int(count) if count else 0
    except:
        return 0


def get_total_count(redis_client, metric_type):
    """Get total count for a specific metric type"""
    try:
        key = f"metrics:{metric_type}:total"
        count = redis_client.get(key)
        return int(count) if count else 0
    except:
        return 0


def get_cache_hit_rate(redis_client):
    """Calculate cache hit rate"""
    try:
        hits = get_total_count(redis_client, "cache_hits")
        misses = get_total_count(redis_client, "cache_misses")
        total = hits + misses

        if total == 0:
            return 0.0

        return round((hits / total) * 100, 2)
    except:
        return 0.0


def get_error_rate(redis_client):
    """Calculate error rate percentage"""
    try:
        errors = get_daily_count(redis_client, "errors")
        requests = get_daily_count(redis_client, "total_requests")

        if requests == 0:
            return 0.0

        return round((errors / requests) * 100, 2)
    except:
        return 0.0


def get_avg_response_time(redis_client):
    """Get average response time"""
    try:
        # This would be calculated from actual request timing data
        # For now, return a placeholder
        return 150  # 150ms average
    except:
        return 0


def increment_metric(redis_client, metric_type, value=1):
    """Increment a metric counter"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"metrics:{metric_type}:{today}"
        total_key = f"metrics:{metric_type}:total"

        # Increment daily counter
        redis_client.incr(daily_key, value)
        redis_client.expire(daily_key, 86400 * 7)  # Keep for 7 days

        # Increment total counter
        redis_client.incr(total_key, value)

    except Exception:
        # Don't let metrics failures break the service
        pass


def record_response_time(redis_client, response_time_ms):
    """Record response time for metrics"""
    try:
        # In production, you'd maintain a rolling average or histogram
        # For now, just store the latest response time
        key = "metrics:last_response_time"
        redis_client.set(key, response_time_ms, ex=3600)
    except:
        pass
