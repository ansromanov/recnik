#!/bin/bash

# Start Serbian Vocabulary App with HTTPS support
# This script uses self-signed certificates for local development

echo "🚀 Starting Serbian Vocabulary App with HTTPS..."
echo "📍 Using self-signed certificates for local development"
echo ""

# Check if SSL certificates exist
if [ ! -f "ssl/localhost.crt" ] || [ ! -f "ssl/localhost.key" ]; then
    echo "🔐 Creating SSL certificates..."
    mkdir -p ssl
    openssl req -x509 -newkey rsa:4096 -keyout ssl/localhost.key -out ssl/localhost.crt -days 365 -nodes \
        -subj "/C=RS/ST=Belgrade/L=Belgrade/O=SerbianVocabApp/OU=Development/CN=localhost"
    echo "✅ SSL certificates created"
    echo ""
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys"
    echo ""
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose-https.yml down

# Build and start services
echo "🔨 Building and starting services with HTTPS..."
docker-compose -f docker-compose-https.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🩺 Checking service health..."
echo ""

# Check backend health
if curl -k -s https://localhost:443/api/health > /dev/null; then
    echo "✅ Backend service is healthy"
else
    echo "❌ Backend service health check failed"
fi

# Check frontend
if curl -k -s https://localhost:443 > /dev/null; then
    echo "✅ Frontend service is healthy"
else
    echo "❌ Frontend service health check failed"
fi

echo ""
echo "🎉 Services started successfully!"
echo ""
echo "📱 Access your application:"
echo "   Frontend (HTTPS): https://localhost:443"
echo "   Frontend (HTTP):  http://localhost:3000 (redirects to HTTPS)"
echo "   Backend API:      https://localhost:443/api"
echo "   Grafana:          http://localhost:3100"
echo "   Prometheus:       http://localhost:9090"
echo ""
echo "🔒 SSL Certificate Info:"
echo "   - Self-signed certificate for localhost"
echo "   - Valid for 365 days"
echo "   - Browser will show security warning (click 'Advanced' -> 'Proceed')"
echo ""
echo "📋 To stop services:"
echo "   docker-compose -f docker-compose-https.yml down"
echo ""
echo "📊 To view logs:"
echo "   docker-compose -f docker-compose-https.yml logs -f [service-name]"
echo ""
echo "⚡ Happy learning Serbian vocabulary with HTTPS! 🇷🇸"
