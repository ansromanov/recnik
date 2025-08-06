#!/bin/bash

echo "🚀 Deploying Recnik with Image Service..."

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Remove existing backend image to force rebuild
echo "🔄 Removing old backend image to force rebuild..."
docker rmi recnik_backend 2>/dev/null || true
docker rmi recnik_cache-updater 2>/dev/null || true

# Rebuild and start containers
echo "🏗️  Building and starting containers..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:3001"
echo "📊 Database: localhost:5432"
echo "🗄️  Redis: localhost:6379"
echo ""
echo "📸 Image service is now active and will automatically load images for vocabulary words!"
echo ""
echo "To check logs:"
echo "  docker-compose logs -f backend"
echo "  docker-compose logs -f frontend"
echo ""
echo "To stop services:"
echo "  docker-compose down"
