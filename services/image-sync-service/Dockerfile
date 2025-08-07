FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    zlib1g-dev \
    libjpeg62-turbo \
    libpng16-16 \
    libfreetype6 \
    liblcms2-2 \
    libwebp7 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies globally to avoid path issues with volume mounts
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Create non-root user and set permissions
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import redis; redis.from_url('redis://redis:6379').ping()" || exit 1

# Default command
CMD ["python", "image_sync_worker.py"]
