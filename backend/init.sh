#!/bin/sh

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Database is ready!"

# Run migrations
echo "Running database migrations..."
python migrations/add_auto_advance_settings.py

# Start the application
echo "Starting application..."
exec gunicorn -b 0.0.0.0:3001 --timeout 120 --workers 1 --keep-alive 2 app:app
