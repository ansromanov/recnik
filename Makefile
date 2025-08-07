# Recnik - Backend Development Makefile

.PHONY: help install install-dev format lint type-check test test-cov clean security check-all pre-commit setup-dev up down restart logs build rebuild-backend rebuild-frontend rebuild-grafana rebuild-all force-rebuild-backend force-rebuild-frontend force-rebuild-grafana force-rebuild-all rebuild-auth rebuild-news rebuild-vocab rebuild-image-sync force-rebuild-auth force-rebuild-news force-rebuild-vocab force-rebuild-image-sync migrate db-shell redis-shell clean-all open-app open-grafana status dev-logs backend-shell frontend-shell quick-restart install-deps setup setup-full dev-setup prod-deploy backup-db restore-db

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
	@echo "Environment Setup:"
	@echo "  setup           - Complete application setup"
	@echo "  setup-full      - Setup with testing verification"
	@echo "  dev-setup       - Quick development setup"
	@echo "  setup-dev       - Setup Python development environment"
	@echo ""
	@echo "Code Quality:"
	@echo "  format          - Format code with Black"
	@echo "  lint            - Lint code with Ruff"
	@echo "  type-check      - Type check with MyPy"
	@echo "  security        - Security scan with Bandit"
	@echo "  test            - Run tests with pytest"
	@echo "  test-cov        - Run tests with coverage report"
	@echo "  check-all       - Run all quality checks"
	@echo "  pre-commit      - Install and run pre-commit hooks"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean           - Clean Python cache and temporary files"
	@echo "  clean-all       - Clean up all Docker resources (destructive)"
	@echo ""
	@echo "Monitoring:"
	@echo "  open-app        - Open application in browser"
	@echo "  open-grafana    - Open Grafana dashboard"
	@echo "  status          - Show container status"
	@echo ""
	@echo "Development Helpers:"
	@echo "  dev-logs        - Follow backend + frontend logs"
	@echo "  backend-shell   - Open backend shell"
	@echo "  frontend-shell  - Open frontend shell"
	@echo "  quick-restart   - Quick restart (backend + frontend)"
	@echo "  install-deps    - Install/update dependencies"
	@echo ""
	@echo "Production:"
	@echo "  prod-deploy     - Deploy to production"
	@echo "  backup-db       - Create database backup"
	@echo "  restore-db      - Restore database from backup"
	@echo ""
	@echo "CI/CD Scripts:"
	@echo "  build-matrix    - Show build matrix script help"
	@echo "  service-config  - Show service configuration script help"
	@echo "  deployment-manifest - Show deployment manifest script help"

# Setup development environment
setup-dev:
	@echo "🚀 Setting up development environment..."
	uv sync --extra dev --extra test
	uv run pre-commit install
	@echo "✅ Development environment setup complete!"

# Install dependencies
install:
	@echo "📦 Installing production dependencies..."
	uv sync

install-dev:
	@echo "📦 Installing development dependencies..."
	uv sync --extra dev --extra test

# Initialize uv project (run once)
init-uv:
	@echo "🔧 Initializing uv project..."
	uv init --no-readme --no-workspace
	@echo "✅ UV project initialized!"

# Code formatting
format:
	@echo "🎨 Formatting code with Black..."
	uv run black .
	@echo "✅ Code formatting complete!"

# Linting
lint:
	@echo "🔍 Linting code with Ruff..."
	uv run ruff check . --fix
	@echo "✅ Linting complete!"

# Type checking
type-check:
	@echo "🔎 Type checking with MyPy..."
	uv run mypy .
	@echo "✅ Type checking complete!"

# Security scanning
security:
	@echo "🔒 Running security scan with Bandit..."
	uv run bandit -r . -f json -o bandit-report.json || true
	uv run bandit -r . --skip B101,B601 --exclude tests/
	@echo "✅ Security scan complete!"

# Testing
test:
	@echo "🧪 Running tests with pytest..."
	uv sync --extra test
	cd services/backend-service && uv run pytest
	@echo "✅ Tests complete!"

test-cov:
	@echo "🧪 Running tests with coverage..."
	uv sync --extra test
	cd services/backend-service && uv run pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "✅ Tests with coverage complete!"
	@echo "📊 Coverage report generated in services/backend-service/htmlcov/"

# Run all quality checks
check-all: format lint type-check security test-cov
	@echo "🎉 All quality checks completed successfully!"

# Pre-commit hooks
pre-commit:
	@echo "🔧 Installing pre-commit hooks..."
	uv run pre-commit install
	@echo "🔍 Running pre-commit on all files..."
	uv run pre-commit run --all-files
	@echo "✅ Pre-commit setup complete!"

# Clean cache and temporary files
clean:
	@echo "🧹 Cleaning cache and temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "bandit-report.json" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

# Development workflow shortcuts
dev-check: format lint type-check
	@echo "🔍 Quick development checks complete!"

quick-test:
	@echo "⚡ Running quick tests..."
	cd services/backend-service && uv run pytest -x --tb=short
	@echo "✅ Quick tests complete!"

# CI/CD helpers
ci-install:
	@echo "🤖 Installing dependencies for CI..."
	pip install -e ".[dev,test]"

ci-test-cov:
	@echo "🧪 Running tests with coverage for CI..."
	cd services/backend-service && uv run pytest \
		--cov=. \
		--cov-report=xml \
		--cov-report=html \
		--cov-report=term-missing \
		--junitxml=pytest-results.xml \
		-v
	@echo "✅ CI tests with coverage complete!"

ci-check: lint type-check security ci-test-cov
	@echo "🤖 CI checks complete!"

# Build matrix generation for CI/CD
build-matrix:
	@echo "🔍 Generating build matrix..."
	@./scripts/generate-build-matrix.sh --help

build-matrix-all:
	@echo "🏗️ All services matrix:"
	@./scripts/generate-build-matrix.sh --event workflow_dispatch

build-matrix-test:
	@echo "🧪 Testing build matrix script..."
	@echo "All services (workflow_dispatch):"
	@./scripts/generate-build-matrix.sh --event workflow_dispatch 2>/dev/null
	@echo ""
	@echo "Backend only (pull_request):"
	@./scripts/generate-build-matrix.sh --event pull_request --backend true 2>/dev/null
	@echo ""
	@echo "Frontend + Auth service (pull_request):"
	@./scripts/generate-build-matrix.sh --event pull_request --frontend true --auth-service true 2>/dev/null
	@echo ""
	@echo "No changes (pull_request):"
	@./scripts/generate-build-matrix.sh --event pull_request 2>/dev/null
	@echo ""
	@echo "✅ Build matrix testing complete!"

# Service configuration for CI/CD
service-config:
	@echo "🔧 Service configuration script help:"
	@./scripts/get-service-config.sh --help

service-config-test:
	@echo "🧪 Testing service configuration script..."
	@echo "Backend service (env format):"
	@./scripts/get-service-config.sh --service backend 2>/dev/null
	@echo ""
	@echo "Frontend service (JSON format):"
	@./scripts/get-service-config.sh --service frontend --output-format json 2>/dev/null
	@echo ""
	@echo "Auth service (YAML format):"
	@./scripts/get-service-config.sh --service auth-service --output-format yaml 2>/dev/null
	@echo ""
	@echo "✅ Service configuration testing complete!"

# Deployment manifest generation for CI/CD
deployment-manifest:
	@echo "📋 Deployment manifest script help:"
	@./scripts/generate-deployment-manifest.sh --help

deployment-manifest-test:
	@echo "🧪 Testing deployment manifest script..."
	@echo "Pull request manifest:"
	@./scripts/generate-deployment-manifest.sh --event pull_request --pr-number 1 --sha abc123 --output-file test-pr-manifest.yml 2>/dev/null
	@cat test-pr-manifest.yml
	@rm -f test-pr-manifest.yml
	@echo ""
	@echo "Main branch manifest:"
	@./scripts/generate-deployment-manifest.sh --event push --ref refs/heads/main --ref-name main --sha def456 --output-file test-main-manifest.yml 2>/dev/null
	@cat test-main-manifest.yml
	@rm -f test-main-manifest.yml
	@echo ""
	@echo "Specific services only:"
	@./scripts/generate-deployment-manifest.sh --event push --ref refs/heads/main --ref-name main --sha def456 --services backend,frontend --output-file test-services-manifest.yml 2>/dev/null
	@cat test-services-manifest.yml
	@rm -f test-services-manifest.yml
	@echo ""
	@echo "✅ Deployment manifest testing complete!"

# =============================================================================
# DOCKER & DEPLOYMENT COMMANDS (restored from commit aa29db636)
# =============================================================================

# Development commands
up:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo "✅ All services started!"

down:
	@echo "🛑 Stopping all services..."
	docker-compose down
	@echo "✅ All services stopped!"

restart: down up
	@echo "🔄 All services restarted!"

logs:
	@echo "📋 Showing logs from all services..."
	docker-compose logs

logs-follow:
	@echo "📋 Following logs from all services..."
	docker-compose logs -f

# Building commands
build:
	@echo "🏗️ Building all images..."
	docker-compose build
	@echo "✅ All images built!"

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

# Microservices rebuild commands
rebuild-auth:
	@echo "🔨 Rebuilding auth service (caching base images)..."
	docker-compose build auth-service
	docker-compose up -d auth-service
	@echo "✅ Auth service rebuilt successfully!"

rebuild-news:
	@echo "🔨 Rebuilding news service (caching base images)..."
	docker-compose build news-service
	docker-compose up -d news-service
	@echo "✅ News service rebuilt successfully!"

rebuild-vocab:
	@echo "🔨 Rebuilding vocabulary service (caching base images)..."
	docker-compose build vocabulary-service
	docker-compose up -d vocabulary-service
	@echo "✅ Vocabulary service rebuilt successfully!"

rebuild-image-sync:
	@echo "🔨 Rebuilding image sync service (caching base images)..."
	docker-compose build image-sync-service
	docker-compose up -d image-sync-service
	@echo "✅ Image sync service rebuilt successfully!"

# Force rebuild microservices (including base images)
force-rebuild-auth:
	@echo "🔨 Force rebuilding auth service (including base images)..."
	docker-compose stop auth-service
	docker-compose build --no-cache auth-service
	docker-compose up -d auth-service
	@echo "✅ Auth service force rebuilt successfully!"

force-rebuild-news:
	@echo "🔨 Force rebuilding news service (including base images)..."
	docker-compose stop news-service
	docker-compose build --no-cache news-service
	docker-compose up -d news-service
	@echo "✅ News service force rebuilt successfully!"

force-rebuild-vocab:
	@echo "🔨 Force rebuilding vocabulary service (including base images)..."
	docker-compose stop vocabulary-service
	docker-compose build --no-cache vocabulary-service
	docker-compose up -d vocabulary-service
	@echo "✅ Vocabulary service force rebuilt successfully!"

force-rebuild-image-sync:
	@echo "🔨 Force rebuilding image sync service (including base images)..."
	docker-compose stop image-sync-service
	docker-compose build --no-cache image-sync-service
	docker-compose up -d image-sync-service
	@echo "✅ Image sync service force rebuilt successfully!"

# Database commands
migrate:
	@echo "🗃️ Running database migrations..."
	docker-compose exec backend python migrate.py
	@echo "✅ Database migrations completed!"

db-shell:
	@echo "🗃️ Opening PostgreSQL shell..."
	docker-compose exec db psql -U vocab_user -d serbian_vocab

redis-shell:
	@echo "🔴 Opening Redis shell..."
	docker-compose exec redis redis-cli

# Maintenance commands
clean-all:
	@echo "🧹 This will remove ALL Docker resources including volumes!"
	@echo "⚠️  WARNING: This will delete all data in your containers!"
	@read -p "Are you sure you want to continue? (y/N): " REPLY; \
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
	@echo "📋 Following development logs..."
	docker-compose logs -f backend frontend

backend-shell:
	@echo "🐚 Opening backend shell..."
	docker-compose exec backend bash

frontend-shell:
	@echo "🐚 Opening frontend shell..."
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
	@if [ ! -f services/backend-service/.env ]; then \
		cp services/backend-service/.env.example services/backend-service/.env; \
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
	@echo "🧪 Running backend tests..."
	docker-compose exec backend python -m pytest tests/ -v || echo "⚠️ Some tests failed, but setup continues..."
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
