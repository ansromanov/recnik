# Serbian Vocabulary App - Common Tasks
# Usage: make <task>

.PHONY: help up down restart logs build rebuild-frontend rebuild-grafana rebuild-all clean migrate test

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
	@echo "  rebuild-frontend - Rebuild only frontend"
	@echo "  rebuild-grafana - Rebuild only Grafana"
	@echo "  rebuild-all     - Rebuild all services"
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

rebuild-frontend:
	@echo "🔨 Rebuilding frontend..."
	docker-compose stop frontend
	docker-compose build --no-cache frontend
	docker-compose up -d frontend
	@echo "✅ Frontend rebuilt successfully!"

rebuild-grafana:
	@echo "🔨 Rebuilding Grafana..."
	docker-compose stop grafana
	docker-compose build --no-cache grafana
	docker-compose up -d grafana
	@echo "✅ Grafana rebuilt successfully!"

rebuild-all:
	@echo "🔨 Rebuilding all services..."
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ All services rebuilt successfully!"

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
	sleep 10
	make migrate
	@echo "✅ Setup completed! App should be running at http://localhost:3000"

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
