# Bandit Configuration CI Fix Summary

## Issue

The GitHub Actions CI pipeline was failing with the error:

```
[main] ERROR .bandit : Could not read config file.
```

This was occurring in the pre-commit job that runs bandit security scanning.

## Root Cause

The `.bandit` configuration file was using an INI-style format:

```ini
[bandit]
exclude_dirs = .git,.venv,venv,__pycache__,node_modules,...
skips = B101,B601,B602,B603,B607
exclude = */test_*.py,*/tests/*,...
```

However, bandit expects configuration files to be in either YAML or TOML format when using a separate config file, not INI format.

## Solution Implemented

### 1. Moved Configuration to pyproject.toml

Migrated the bandit configuration from the invalid `.bandit` file to the `pyproject.toml` file using proper TOML format:

```toml
# Bandit configuration
[tool.bandit]
exclude_dirs = [
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".ruff_cache",
    "htmlcov",
    "frontend/build",
    "frontend/node_modules",
    "monitoring/grafana",
    "ssl",
    "logs",
    ".github",
    "tests",
    "backend/tests",
]
skips = ["B101", "B601", "B602", "B603", "B607"]
exclude = [
    "*/test_*.py",
    "*/tests/*",
    "*/*test.py",
    "test_*.py",
    "*_test.py",
    "analyze_code_lines.py",
    "demo_testing.py",
    "validate_testing_setup.py",
]
```

### 2. Updated Pre-commit Configuration

Removed the `--configfile .bandit` argument from the pre-commit configuration since bandit automatically reads configuration from `pyproject.toml`:

```yaml
# Before
- id: bandit
  args: [--recursive, --configfile, .bandit]

# After
- id: bandit
  args: [--recursive]
```

### 3. Removed Invalid Configuration File

Deleted the `.bandit` file that was causing the parsing error.

## Verification

- All pre-commit hooks now pass locally
- Bandit security scanning continues to work with the same exclusions and skips
- Configuration follows modern Python project standards by using `pyproject.toml`

## Files Modified

- `pyproject.toml` - Added bandit configuration section
- `.pre-commit-config.yaml` - Removed `--configfile` argument
- `.bandit` - Removed (deleted)

## Commit

```
fix: Fix bandit configuration issue in CI

- Move bandit configuration from .bandit (INI format) to pyproject.toml (TOML format)
- Remove invalid .bandit file that was causing 'Could not read config file' error
- Update pre-commit config to remove --configfile argument since bandit now reads from pyproject.toml automatically
- All pre-commit hooks now pass successfully
```

This fix ensures the CI pipeline passes while maintaining the same security scanning behavior.
