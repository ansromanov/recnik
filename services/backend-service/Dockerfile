# Build stage - includes build dependencies
FROM python:3.11-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev \
    libimagequant-dev \
    libxcb-dev \
    libpng-dev

# Install Python dependencies
COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r requirements-test.txt

# Runtime stage - minimal runtime dependencies
FROM python:3.11-alpine AS runtime

WORKDIR /app

# Install only runtime system dependencies
RUN apk add --no-cache \
    postgresql-libs \
    jpeg \
    zlib \
    freetype \
    lcms2 \
    openjpeg \
    tiff \
    tk \
    tcl \
    harfbuzz \
    fribidi \
    libimagequant \
    libxcb \
    libpng \
    netcat-openbsd

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable:
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Make init script executable
RUN chmod +x init.sh

EXPOSE 3001

CMD ["./init.sh"]
