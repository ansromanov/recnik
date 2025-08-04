# Serbian Vocabulary App - Backend Development Makefile

.PHONY: help install install-dev format lint type-check test test-cov clean security check-all pre-commit setup-dev

# Default target
help:
	@echo "Available commands:"
	@echo "  setup-dev       - Setup development environment with all tools"
	@echo "  install         - Install production dependencies"
	@echo "  install-dev     - Install development dependencies"
	@echo "  format          - Format code with Black"
	@echo "  lint            - Lint code with Ruff"
	@echo "  type-check      - Type check with MyPy"
	@echo "  security        - Security scan with Bandit"
	@echo "  test            - Run tests with pytest"
	@echo "  test-cov        - Run tests with coverage report"
	@echo "  check-all       - Run all quality checks (format, lint, type-check, security, test)"
	@echo "  pre-commit      - Install and run pre-commit hooks"
	@echo "  clean           - Clean cache and temporary files"
	@echo "  build-matrix    - Show build matrix script help"
	@echo "  build-matrix-all - Generate matrix for all services"
	@echo "  build-matrix-test - Test build matrix script with various scenarios"

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
	cd backend && uv run pytest
	@echo "✅ Tests complete!"

test-cov:
	@echo "🧪 Running tests with coverage..."
	uv sync --extra test
	cd backend && uv run pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "✅ Tests with coverage complete!"
	@echo "📊 Coverage report generated in backend/htmlcov/"

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
	cd backend && uv run pytest -x --tb=short
	@echo "✅ Quick tests complete!"

# CI/CD helpers
ci-install:
	@echo "🤖 Installing dependencies for CI..."
	pip install -e ".[dev,test]"

ci-check: lint type-check security test-cov
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
	@./scripts/generate-build-matrix.sh --event workflow_dispatch
	@echo ""
	@echo "Backend only (pull_request):"
	@./scripts/generate-build-matrix.sh --event pull_request --backend true
	@echo ""
	@echo "Frontend + Auth service (pull_request):"
	@./scripts/generate-build-matrix.sh --event pull_request --frontend true --auth-service true
	@echo ""
	@echo "No changes (pull_request):"
	@./scripts/generate-build-matrix.sh --event pull_request
	@echo "✅ Build matrix testing complete!"
