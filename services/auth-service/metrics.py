"""
Prometheus metrics endpoint
"""

from flask import Blueprint

metrics_bp = Blueprint("metrics", __name__)

# Metrics are automatically handled by prometheus_flask_exporter
# This endpoint is registered automatically when PrometheusMetrics is initialized
