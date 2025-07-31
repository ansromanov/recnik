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
    libpng-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3001

CMD ["gunicorn", "-b", "0.0.0.0:3001", "--timeout", "120", "--workers", "4", "app:app"]
