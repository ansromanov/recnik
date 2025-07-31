FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies for psycopg2
RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 3001

CMD ["gunicorn", "-b", "0.0.0.0:3001", "--timeout", "120", "--workers", "4", "app:app"]
