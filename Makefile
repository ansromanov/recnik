# Serbian Vocabulary App - Common Tasks
# Usage: make <task>

.PHONY: help up down restart logs build rebuild-backend rebuild-frontend rebuild-grafana rebuild-all force-rebuild-backend force-rebuild-frontend force-rebuild-grafana force-rebuild-all rebuild-auth rebuild-news rebuild-vocab rebuild-image-sync force-rebuild-auth force-rebuild-news force-rebuild-vocab force-rebuild-image-sync clean migrate test

# Default target
help:
	@echo "Serbian Vocabulary App - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  up              - Start all services"
	@echo "  down            - Stop all services"
	@echo "  restart         - Restart all services"
	@echo "  logs            - View logs from all services"
	@echo "  logs-follow     - Follow logs from all services"
	@echo ""
	@echo "Building:"
	@echo "  build           - Build all images"
	@echo "  rebuild-backend - Rebuild only backend (cache base images)"
	@echo "  rebuild-frontend - Rebuild only frontend (cache base images)"
	@echo "  rebuild-grafana - Rebuild only Grafana (cache base images)"
	@echo "  rebuild-all     - Rebuild all services (cache base images)"
	@echo "  force-rebuild-backend - Force rebuild backend (including base images)"
	@echo "  force-rebuild-frontend - Force rebuild frontend (including base images)"
	@echo "  force-rebuild-grafana - Force rebuild Grafana (including base images)"
	@echo "  force-rebuild-all - Force rebuild all services (including base images)"
	@echo ""
	@echo "Microservices:"
	@echo "  rebuild-auth - Rebuild auth service (cache base images)"
	@echo "  rebuild-news - Rebuild news service (cache base images)"
	@echo "  rebuild-vocab - Rebuild vocabulary service (cache base images)"
	@echo "  rebuild-image-sync - Rebuild image sync service (cache base images)"
	@echo "  force-rebuild-auth - Force rebuild auth service (including base images)"
	@echo "  force-rebuild-news - Force rebuild news service (including base images)"
	@echo "  force-rebuild-vocab - Force rebuild vocabulary service (including base images)"
	@echo "  force-rebuild-image-sync - Force rebuild image sync service (including base images)"
	@echo ""
	@echo "Database:"
	@echo "  migrate         - Run database migrations"
	@echo "  db-shell        - Open PostgreSQL shell"
	@echo "  redis-shell     - Open Redis shell"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean           - Clean up unused Docker resources"
	@echo "  clean-all       - Clean up all Docker resources (destructive)"
	@echo "  test            - Run backend tests"
	@echo ""
	@echo "Monitoring:"
	@echo "  open-app        - Open application in browser"
	@echo "  open-grafana    - Open Grafana dashboard"
	@echo "  status          - Show container status"

# Development commands
up:
	docker-compose up -d

down:
	docker-compose down

restart: down up

logs:
	docker-compose logs

logs-follow:
	docker-compose logs -f

# Building commands
build:
	docker-compose build

rebuild-backend:
	@echo "🔨 Rebuilding backend (caching base images)..."
	docker-compose build backend
	docker-compose up -d backend
	@echo "✅ Backend rebuilt successfully!"

rebuild-frontend:
	@echo "🔨 Rebuilding frontend (caching base images)..."
	docker-compose build frontend
	docker-compose up -d frontend
	@echo "✅ Frontend rebuilt successfully!"

rebuild-grafana:
	@echo "🔨 Rebuilding Grafana (caching base images)..."
	docker-compose build grafana
	docker-compose up -d grafana
	@echo "✅ Grafana rebuilt successfully!"

rebuild-all:
	@echo "🔨 Rebuilding all services (caching base images)..."
	docker-compose build
	docker-compose up -d
	@echo "✅ All services rebuilt successfully!"

# Force rebuild commands (including base images)
force-rebuild-backend:
	@echo "🔨 Force rebuilding backend (including base images)..."
	docker-compose stop backend
	docker-compose build --no-cache backend
	docker-compose up -d backend
	@echo "✅ Backend force rebuilt successfully!"

force-rebuild-frontend:
	@echo "🔨 Force rebuilding frontend (including base images)..."
	docker-compose stop frontend
	docker-compose build --no-cache frontend
	docker-compose up -d frontend
	@echo "✅ Frontend force rebuilt successfully!"

force-rebuild-grafana:
	@echo "🔨 Force rebuilding Grafana (including base images)..."
	docker-compose stop grafana
	docker-compose build --no-cache grafana
	docker-compose up -d grafana
	@echo "✅ Grafana force rebuilt successfully!"

force-rebuild-all:
	@echo "🔨 Force rebuilding all services (including base images)..."
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ All services force rebuilt successfully!"

# Microservice rebuild commands (cache base images)
rebuild-auth:
	@echo "🔨 Rebuilding auth service (caching base images)..."
	docker-compose build auth-service
	docker-compose up -d auth-service
	@echo "✅ Auth service rebuilt successfully!"

rebuild-news:
	@echo "🔨 News service not configured in docker-compose.yml"
	@echo "❌ Please add news-service to docker-compose.yml first!"

rebuild-vocab:
	@echo "🔨 Rebuilding vocabulary service (caching base images)..."
	docker-compose --profile microservices build vocabulary-service
	docker-compose --profile microservices up -d vocabulary-service
	@echo "✅ Vocabulary service rebuilt successfully!"

rebuild-image-sync:
	@echo "🔨 Rebuilding image sync service (caching base images)..."
	docker-compose build image-sync-service
	docker-compose up -d image-sync-service
	@echo "✅ Image sync service rebuilt successfully!"

# Microservice force rebuild commands (including base images)
force-rebuild-auth:
	@echo "🔨 Force rebuilding auth service (including base images)..."
	docker-compose stop auth-service
	docker-compose build --no-cache auth-service
	docker-compose up -d auth-service
	@echo "✅ Auth service force rebuilt successfully!"

force-rebuild-news:
	@echo "🔨 News service not configured in docker-compose.yml"
	@echo "❌ Please add news-service to docker-compose.yml first!"

force-rebuild-vocab:
	@echo "🔨 Force rebuilding vocabulary service (including base images)..."
	docker-compose --profile microservices stop vocabulary-service
	docker-compose --profile microservices build --no-cache vocabulary-service
	docker-compose --profile microservices up -d vocabulary-service
	@echo "✅ Vocabulary service force rebuilt successfully!"

force-rebuild-image-sync:
	@echo "🔨 Force rebuilding image sync service (including base images)..."
	docker-compose stop image-sync-service
	docker-compose build --no-cache image-sync-service
	docker-compose up -d image-sync-service
	@echo "✅ Image sync service force rebuilt successfully!"

# Database commands
migrate:
	@echo "🔄 Running database migrations..."
	docker-compose exec backend python migrations/add_excluded_words_table.py
	@echo "✅ Migrations completed!"

db-shell:
	docker-compose exec db psql -U vocab_user -d serbian_vocab

redis-shell:
	docker-compose exec redis redis-cli

# Maintenance commands
clean:
	@echo "🧹 Cleaning up unused Docker resources..."
	docker system prune -f
	docker volume prune -f
	@echo "✅ Cleanup completed!"

clean-all:
	@echo "⚠️  WARNING: This will remove ALL Docker resources!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo ""; \
		docker-compose down -v; \
		docker system prune -af; \
		docker volume prune -f; \
		echo "✅ Complete cleanup done!"; \
	else \
		echo ""; \
		echo "❌ Cleanup cancelled."; \
	fi

test:
	@echo "🧪 Running backend tests..."
	docker-compose exec backend python -m pytest tests/ -v
	@echo "✅ Tests completed!"

# Monitoring commands
open-app:
	@echo "🌐 Opening application..."
	open http://localhost:3000 || xdg-open http://localhost:3000 || echo "Please open http://localhost:3000 in your browser"

open-grafana:
	@echo "📊 Opening Grafana dashboard..."
	open http://localhost:3001 || xdg-open http://localhost:3001 || echo "Please open http://localhost:3001 in your browser (admin/admin)"

status:
	@echo "📋 Container Status:"
	@docker-compose ps

# Development helpers
dev-logs:
	docker-compose logs -f backend frontend

backend-shell:
	docker-compose exec backend bash

frontend-shell:
	docker-compose exec frontend sh

# Quick actions
quick-restart:
	@echo "⚡ Quick restart (backend + frontend)..."
	docker-compose restart backend frontend
	@echo "✅ Quick restart completed!"

install-deps:
	@echo "📦 Installing/updating dependencies..."
	docker-compose exec backend pip install -r requirements.txt
	docker-compose exec frontend npm install
	@echo "✅ Dependencies updated!"

# Environment setup
setup:
	@echo "🚀 Setting up Serbian Vocabulary App..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "📝 Created .env file from template"; \
	fi
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "📝 Created backend/.env file from template"; \
	fi
	make build
	make up
	@echo "⏳ Waiting for services to be ready..."
	@sleep 15
	@echo "✅ Setup completed! App should be running at http://localhost:80"
	@echo "🔗 Backend API available at http://localhost:3000"
	@echo "📊 Grafana dashboard at http://localhost:3001 (admin/admin)"

# Complete automated setup with testing
setup-full:
	@echo "🚀 Complete automated setup with testing..."
	make setup
	@echo "🧪 Running tests to verify setup..."
	make test
	@echo "🎉 Full setup completed successfully!"

# Quick development setup
dev-setup:
	@echo "⚡ Quick development setup..."
	make rebuild-all
	@echo "✅ Development environment ready!"

# Production commands
prod-deploy:
	@echo "🚀 Deploying to production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production deployment completed!"

# Backup commands
backup-db:
	@echo "💾 Creating database backup..."
	docker-compose exec db pg_dump -U vocab_user serbian_vocab > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created!"

restore-db:
	@echo "📥 Restoring database..."
	@read -p "Enter backup file path: " backup_file; \
	docker-compose exec -T db psql -U vocab_user -d serbian_vocab < $$backup_file
	@echo "✅ Database restored!"
