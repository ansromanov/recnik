# Build Matrix System

## Overview

The build matrix system intelligently determines which Docker services to build based on changed files and trigger conditions. This optimizes CI/CD performance by building only what's necessary.

## Components

### 1. Shell Script (`scripts/generate-build-matrix.sh`)

A standalone script that generates JSON arrays of services to build based on:

- GitHub event type (push, pull_request, workflow_dispatch)
- Git reference (branch/tag)
- Changed file indicators for each service

**Features:**

- Comprehensive CLI with help and options
- Multiple output formats (JSON, comma-separated, list)
- Robust error handling and validation
- Debugging output to stderr

### 2. Makefile Integration

Added targets for local testing and development:

- `make build-matrix` - Show script help
- `make build-matrix-all` - Generate matrix for all services
- `make build-matrix-test` - Test various scenarios

### 3. GitHub Workflow Integration

The workflow now uses the script instead of inline bash logic:

- Cleaner and more maintainable
- Easier to test locally
- Consistent behavior between local and CI environments

## Logic Rules

### Always Build All Services

- Main branch pushes (`refs/heads/main`)
- Tag pushes (`refs/tags/v*`)
- Manual workflow dispatch (`workflow_dispatch`)

### Build Only Changed Services

- Pull requests to main
- Push to develop branch
- Based on path filters:
  - `backend/` changes → build backend
  - `frontend/` changes → build frontend
  - `services/auth-service/` changes → build auth-service
  - `services/vocabulary-service/` changes → build vocabulary-service
  - `services/news-service/` changes → build news-service
  - `image-sync-service/` changes → build image-sync-service

## Usage Examples

### Local Testing

```bash
# Test all scenarios
make build-matrix-test

# Generate matrix for all services
make build-matrix-all

# Generate matrix for specific changes
./scripts/generate-build-matrix.sh \
  --event pull_request \
  --backend true \
  --frontend false \
  --auth-service false \
  --vocab-service false \
  --news-service false \
  --image-service false
```

### Output Examples

**All services (workflow_dispatch):**

```json
["backend","frontend","auth-service","vocabulary-service","news-service","image-sync-service"]
```

**Backend only (pull_request with backend changes):**

```json
["backend"]
```

**No changes (pull_request with no relevant changes):**

```json
[]
```

## Benefits

1. **Performance**: Only builds necessary services
2. **Maintainability**: Logic separated into testable script
3. **Reliability**: Robust error handling and validation
4. **Debugging**: Clear logging and multiple output formats
5. **Local Testing**: Easy to test scenarios before pushing

## File Structure

```
scripts/
└── generate-build-matrix.sh    # Main logic script

.github/workflows/
└── docker-build.yml           # Uses the script

Makefile                       # Testing targets

docs/cline/
└── BUILD_MATRIX_SYSTEM.md     # This documentation
```

## Future Enhancements

- Add dependency-based building (e.g., if shared library changes, build dependent services)
- Support for build prioritization
- Integration with deployment strategies
- Metrics collection for build optimization
