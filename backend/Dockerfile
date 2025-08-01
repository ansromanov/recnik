FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies for psycopg2, Pillow, and other packages
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
    libpng-dev \
    netcat-openbsd

COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt

COPY . .

# Make init script executable
RUN chmod +x init.sh

EXPOSE 3001

CMD ["./init.sh"]
