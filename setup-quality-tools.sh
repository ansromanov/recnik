#!/bin/bash

# Serbian Vocabulary App - Code Quality Tools Setup
set -e

echo "🚀 Setting up code quality tools for Serbian Vocabulary App..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️ uv is not installed. Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}❌ Failed to install uv. Please install it manually: https://docs.astral.sh/uv/getting-started/installation/${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}📦 Using uv for package management${NC}"

# Check uv version
UV_VERSION=$(uv --version)
echo -e "${BLUE}⚡ $UV_VERSION${NC}"

# Install development dependencies
echo -e "${YELLOW}📥 Installing development dependencies...${NC}"
uv sync --extra dev --extra test

# Install pre-commit hooks
echo -e "${YELLOW}🔧 Installing pre-commit hooks...${NC}"
pre-commit install

# Run initial checks
echo -e "${YELLOW}🔍 Running initial code quality checks...${NC}"

# Format code
echo -e "${BLUE}🎨 Formatting code with Black...${NC}"
black . || echo -e "${YELLOW}⚠️ Some files were reformatted${NC}"

# Run linter
echo -e "${BLUE}🔍 Running Ruff linter...${NC}"
ruff check . --fix || echo -e "${YELLOW}⚠️ Some linting issues were found and fixed${NC}"

# Run type checker (allow failures for initial setup)
echo -e "${BLUE}🔎 Running MyPy type checker...${NC}"
mypy . || echo -e "${YELLOW}⚠️ Type checking found some issues (this is normal for initial setup)${NC}"

# Run security scan
echo -e "${BLUE}🔒 Running Bandit security scan...${NC}"
bandit -r . --skip B101,B601 --exclude tests/ || echo -e "${YELLOW}⚠️ Security scan completed with warnings${NC}"

# Run tests if they exist
if [ -d "backend/tests" ] && [ "$(ls -A backend/tests)" ]; then
    echo -e "${BLUE}🧪 Running tests...${NC}"
    cd backend && pytest --cov=. --cov-report=term-missing || echo -e "${YELLOW}⚠️ Some tests failed${NC}"
    cd ..
else
    echo -e "${YELLOW}⚠️ No tests found in backend/tests${NC}"
fi

# Test pre-commit hooks
echo -e "${BLUE}🔧 Testing pre-commit hooks...${NC}"
pre-commit run --all-files || echo -e "${YELLOW}⚠️ Pre-commit hooks made some changes${NC}"

echo -e "${GREEN}✅ Code quality tools setup complete!${NC}"
echo
echo -e "${BLUE}📚 Available commands:${NC}"
echo -e "  ${GREEN}make help${NC}        - Show all available commands"
echo -e "  ${GREEN}make format${NC}      - Format code with Black"
echo -e "  ${GREEN}make lint${NC}        - Lint code with Ruff"
echo -e "  ${GREEN}make type-check${NC}  - Type check with MyPy"
echo -e "  ${GREEN}make test-cov${NC}    - Run tests with coverage"
echo -e "  ${GREEN}make check-all${NC}   - Run all quality checks"
echo
echo -e "${BLUE}📖 Documentation:${NC}"
echo -e "  Read ${GREEN}CODE_QUALITY.md${NC} for detailed usage instructions"
echo
echo -e "${GREEN}🎉 Happy coding!${NC}"
