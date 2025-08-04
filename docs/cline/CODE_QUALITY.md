# Code Quality Setup for Serbian Vocabulary App

This document explains the code quality tools and practices implemented for the Serbian Vocabulary App backend.

## 🛠️ Tools Overview

### 1. **Black** - Code Formatter

- **Purpose**: Automatically formats Python code to ensure consistent style
- **Configuration**: Defined in `pyproject.toml`
- **Line length**: 88 characters
- **Target**: Python 3.8+

### 2. **Ruff** - Fast Python Linter

- **Purpose**: Extremely fast Python linter that replaces flake8, isort, and more
- **Features**:
  - Code style enforcement (pycodestyle)
  - Import sorting (isort)
  - Security checks (bandit-like)
  - Code complexity analysis
  - Modern Python practices (pyupgrade)
- **Configuration**: Comprehensive rules in `pyproject.toml`

### 3. **MyPy** - Static Type Checker

- **Purpose**: Catches type-related errors before runtime
- **Configuration**: Strict typing enabled in `pyproject.toml`
- **Features**:
  - Type inference
  - Gradual typing support
  - Third-party library stubs

### 4. **Bandit** - Security Scanner

- **Purpose**: Identifies common security issues in Python code
- **Features**: Scans for SQL injection, hardcoded passwords, etc.
- **Configuration**: Integrated with pre-commit hooks

### 5. **Pre-commit** - Git Hooks

- **Purpose**: Runs quality checks before each commit
- **Configuration**: `.pre-commit-config.yaml`
- **Benefits**: Prevents bad code from entering the repository

## 📥 Installation & Setup

### Quick Setup (Recommended)

```bash
# Install all development tools and setup pre-commit hooks
make setup-dev
```

### Manual Setup

```bash
# Install development dependencies
pip install -e ".[dev,test]"

# Install pre-commit hooks
pre-commit install
```

## 🚀 Usage

### Command Line Usage

#### Format Code

```bash
# Format all Python files
make format
# or
black .
```

#### Lint Code

```bash
# Lint and auto-fix issues
make lint
# or
ruff check . --fix
```

#### Type Check

```bash
# Run static type checking
make type-check
# or
mypy .
```

#### Security Scan

```bash
# Run security analysis
make security
# or
bandit -r . --exclude tests/
```

#### Run Tests

```bash
# Run tests with coverage
make test-cov
# or
cd backend && pytest --cov=. --cov-report=html
```

#### Run All Checks

```bash
# Run all quality checks at once
make check-all
```

### Development Workflow

#### Before Committing

Pre-commit hooks will automatically run, but you can also run manually:

```bash
# Run pre-commit on all files
pre-commit run --all-files

# Quick development checks
make dev-check
```

#### During Development

```bash
# Quick test run
make quick-test

# Clean cache files
make clean
```

## ⚙️ Configuration Details

### Black Configuration

```toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
exclude = migrations, __pycache__, .venv
```

### Ruff Configuration

- **Selected rules**: pycodestyle, pyflakes, isort, flake8-bugbear, etc.
- **Ignored rules**: Line length (handled by Black), assert usage in tests
- **Complexity limit**: 10
- **Import sorting**: First-party modules prioritized

### MyPy Configuration

- **Strict mode**: Enabled for better type safety
- **Features**:
  - Disallow untyped definitions
  - Warn about unused imports
  - Check untyped definitions
  - Require return type annotations

### Test Configuration

- **Coverage target**: 80% minimum
- **Test discovery**: `test_*.py` and `*_test.py`
- **Markers**: unit, integration, e2e, slow
- **Coverage reports**: HTML and terminal

## 🔄 Continuous Integration

### GitHub Actions

The `.github/workflows/python-quality.yml` workflow runs:

- Code formatting checks
- Linting
- Type checking
- Security scanning
- Tests with coverage
- Pre-commit hooks
- Dependency review (for PRs)

### Matrix Testing

Tests run against Python versions: 3.8, 3.9, 3.10, 3.11

## 📊 Reports & Metrics

### Coverage Reports

- **HTML Report**: Generated in `backend/htmlcov/`
- **Terminal Report**: Shows missing lines
- **XML Report**: For CI/CD integration

### Security Reports

- **JSON Report**: `bandit-report.json`
- **Console Output**: Direct feedback

## 🎯 Best Practices

### Type Hints

```python
from typing import List, Optional, Dict, Any

def process_words(words: List[str], limit: Optional[int] = None) -> Dict[str, Any]:
    """Process a list of words with optional limit."""
    return {"processed": len(words[:limit]) if limit else len(words)}
```

### Error Handling

```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def safe_operation(data: str) -> Optional[Dict[str, Any]]:
    """Safely perform operation with proper error handling."""
    try:
        return {"result": data.upper()}
    except AttributeError as e:
        logger.error("Invalid data type: %s", e)
        return None
```

### Testing

```python
import pytest
from unittest.mock import Mock, patch

def test_word_processing():
    """Test word processing functionality."""
    # Arrange
    words = ["kuća", "auto", "knjiga"]

    # Act
    result = process_words(words, limit=2)

    # Assert
    assert result["processed"] == 2
```

## 🚨 Common Issues & Solutions

### MyPy Ignores

For third-party libraries without type stubs:

```python
import some_library  # type: ignore[import]
```

### Ruff Ignores

For specific line ignores:

```python
password = "temp123"  # noqa: S105
```

### Pre-commit Bypassing

Emergency commits (use sparingly):

```bash
git commit --no-verify -m "Emergency fix"
```

## 📝 IDE Integration

### VS Code

Install extensions:

- Python
- Black Formatter
- Ruff
- MyPy Type Checker

### PyCharm

Configure external tools for Black, Ruff, and MyPy in settings.

## 🔧 Troubleshooting

### Dependencies Issues

```bash
# Clean and reinstall
make clean
pip install -e ".[dev,test]"
```

### Pre-commit Issues

```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean
```

### Type Checking Issues

```bash
# Clear MyPy cache
rm -rf .mypy_cache
mypy .
```

## 📈 Metrics & Goals

### Code Quality Targets

- **Test Coverage**: ≥80%
- **Type Coverage**: ≥90%
- **Complexity**: ≤10 per function
- **Security Issues**: 0 high/medium severity

### Performance Benchmarks

- **Ruff**: <1s for full codebase
- **Black**: <2s for formatting
- **MyPy**: <10s for type checking
- **Tests**: <30s for full suite

## 🔄 Maintenance

### Regular Updates

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Update dependencies in pyproject.toml
# Check for security updates regularly
```

### Monthly Review

- Review and update ignored rules
- Assess test coverage gaps
- Update dependency versions
- Review security scan results

This setup ensures high code quality, consistency, and maintainability across the Serbian Vocabulary App backend codebase.
