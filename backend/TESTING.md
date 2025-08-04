# Testing Guide for Serbian Vocabulary Application

This document provides comprehensive information about the testing setup and how to run tests for the Serbian Vocabulary Application backend.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Setup](#setup)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)
- [Coverage](#coverage)
- [CI/CD Integration](#cicd-integration)
- [Writing Tests](#writing-tests)
- [Troubleshooting](#troubleshooting)

## 🔍 Overview

The testing suite is built using **pytest** and includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions and external services
- **Model Tests**: Test database models and ORM functionality
- **Service Tests**: Test business logic services
- **Mocking**: Extensive use of mocks for external dependencies
- **Coverage**: Code coverage reporting with minimum 80% requirement

## 📁 Test Structure

```
backend/
├── tests/                          # Test directory
│   ├── __init__.py                 # Test package init
│   ├── conftest.py                 # Pytest fixtures and configuration
│   ├── test_models.py              # Database model tests
│   ├── test_text_processor.py      # Text processing service tests
│   ├── test_translation_cache.py   # Translation cache tests
│   └── test_image_service.py       # Image service tests
├── pytest.ini                     # Pytest configuration
├── requirements-test.txt           # Test dependencies
├── run_tests.py                    # Test runner script
└── TESTING.md                      # This file
```

## 🚀 Setup

### 1. Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt

# Or use the test runner to install everything
python run_tests.py --install-deps
```

### 2. Environment Setup

Create a `.env` file in the backend directory with test configurations:

```bash
# Test database (uses SQLite in-memory by default)
DATABASE_URL=sqlite:///:memory:

# Redis for caching tests (fakeredis is used in tests)
REDIS_URL=redis://localhost:6379/1

# Optional: OpenAI API key for integration tests
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Unsplash API key for image service tests
UNSPLASH_ACCESS_KEY=your_unsplash_key_here
```

## 🧪 Running Tests

### Using the Test Runner (Recommended)

The `run_tests.py` script provides an easy way to run tests with various options:

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --type unit

# Run only integration tests
python run_tests.py --type integration

# Run model tests
python run_tests.py --type models

# Run service tests
python run_tests.py --type services

# Run fast tests (exclude slow integration tests)
python run_tests.py --type fast

# Run specific test file
python run_tests.py tests/test_models.py

# Run without coverage
python run_tests.py --no-coverage

# Run in quiet mode
python run_tests.py --quiet

# Generate comprehensive report
python run_tests.py --report

# Run with specific markers
python run_tests.py --markers unit redis
```

### Using Pytest Directly

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_models.py::TestUser

# Run specific test method
pytest tests/test_models.py::TestUser::test_user_creation

# Run tests with specific marker
pytest -m unit

# Run tests excluding specific marker
pytest -m "not slow"

# Run with verbose output
pytest -v

# Run with extra verbose output
pytest -vv
```

## 🏷️ Test Categories

Tests are organized using pytest markers:

### Unit Tests (`@pytest.mark.unit`)

- Test individual functions and methods
- Use mocks for external dependencies
- Fast execution
- High isolation

### Integration Tests (`@pytest.mark.integration`)

- Test component interactions
- May use real external services
- Slower execution
- Require proper environment setup

### Redis Tests (`@pytest.mark.redis`)

- Tests that require Redis functionality
- Use fakeredis for isolation
- Test caching behavior

### Slow Tests (`@pytest.mark.slow`)

- Tests that take longer to execute
- Usually integration tests with external APIs
- Can be excluded for faster test runs

### OpenAI Tests (`@pytest.mark.openai`)

- Tests that require OpenAI API key
- Skipped if API key not available
- Use real API (consume quota)

## 📊 Coverage

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# Open coverage report (macOS)
open htmlcov/index.html

# Open coverage report (Linux)
xdg-open htmlcov/index.html

# Terminal coverage report
pytest --cov=. --cov-report=term-missing
```

### Coverage Requirements

- **Minimum**: 80% overall coverage
- **Target**: 90%+ for core business logic
- **Exclusions**: Configuration files, migrations, test files

### Coverage Configuration

Coverage settings are in `pytest.ini`:

```ini
--cov-fail-under=80
--cov-report=term-missing
--cov-report=html:htmlcov
```

## 🔧 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        cd backend
        python run_tests.py --report

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
```

## ✍️ Writing Tests

### Test File Structure

```python
"""
Unit tests for [Component Name]
"""

import pytest
from unittest.mock import Mock, patch
from your_module import YourClass


@pytest.mark.unit
class TestYourClass:
    """Test cases for YourClass"""

    def test_method_success(self, fixture_name):
        """Test successful method execution"""
        # Arrange
        instance = YourClass()

        # Act
        result = instance.method()

        # Assert
        assert result is not None

    def test_method_error(self, fixture_name):
        """Test method error handling"""
        # Test error scenarios
        pass


@pytest.mark.integration
class TestYourClassIntegration:
    """Integration tests for YourClass"""

    def test_with_real_dependencies(self):
        """Test with real external dependencies"""
        pass
```

### Fixtures

Common fixtures are defined in `conftest.py`:

```python
def test_with_database(db_session):
    """Test that uses database"""
    user = User(username="test")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None

def test_with_cache(translation_cache):
    """Test that uses Redis cache"""
    translation_cache.set("word", {"translation": "translation"})
    result = translation_cache.get("word")

    assert result is not None

def test_with_mocked_openai(text_processor):
    """Test with mocked OpenAI"""
    result = text_processor.process_text("test", categories)
    assert "translations" in result
```

### Best Practices

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Use Descriptive Names**: Test names should describe what they test
3. **One Assertion Per Test**: Keep tests focused
4. **Use Fixtures**: Leverage pytest fixtures for setup
5. **Mock External Dependencies**: Use mocks for APIs, databases, etc.
6. **Test Edge Cases**: Include error conditions and boundary cases
7. **Keep Tests Independent**: Tests should not depend on each other

### Mocking Examples

```python
@patch('openai.ChatCompletion.create')
def test_with_mocked_openai(mock_create):
    """Test with mocked OpenAI API"""
    mock_response = Mock()
    mock_response.choices[0].message = {"content": "{}"}
    mock_create.return_value = mock_response

    # Your test code here

@patch.dict('os.environ', {'API_KEY': 'test-key'})
def test_with_env_var():
    """Test with mocked environment variable"""
    # Your test code here
```

## 🔧 Troubleshooting

### Common Issues

#### Import Errors

```bash
# Make sure you're in the backend directory
cd backend

# Install dependencies
pip install -r requirements.txt -r requirements-test.txt

# Check Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

#### Database Errors

```bash
# For SQLite issues, make sure you have write permissions
# Tests use in-memory SQLite by default
```

#### Redis Connection Errors

```bash
# Tests use fakeredis by default
# Make sure fakeredis is installed
pip install fakeredis
```

#### Coverage Issues

```bash
# Clear coverage data
rm -rf .coverage htmlcov/

# Run tests again
pytest --cov=.
```

### Debug Mode

```bash
# Run tests with pdb debugger
pytest --pdb

# Run specific test with debugger
pytest tests/test_models.py::TestUser::test_creation --pdb

# Add breakpoint in test code
import pdb; pdb.set_trace()
```

### Verbose Logging

```bash
# Enable logging in tests
pytest -s --log-level=DEBUG

# Or modify conftest.py to set logging level
```

## 📈 Test Metrics

### Running Test Report

```bash
# Generate comprehensive report
python run_tests.py --report

# View generated files
ls -la *.xml htmlcov/
```

### Key Metrics

- **Test Count**: Total number of tests
- **Coverage Percentage**: Code coverage metrics
- **Execution Time**: Performance of test suite
- **Success Rate**: Percentage of passing tests

## 🎯 Goals

### Short-term

- [x] Achieve 80%+ test coverage
- [x] Set up automated testing pipeline
- [x] Create comprehensive test documentation

### Long-term

- [ ] Achieve 95%+ test coverage
- [ ] Performance testing suite
- [ ] End-to-end testing integration
- [ ] Mutation testing implementation

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)
- [Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

For questions or issues with testing, please check the troubleshooting section or create an issue in the project repository.
