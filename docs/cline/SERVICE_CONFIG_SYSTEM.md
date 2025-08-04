# Service Configuration System

## Overview

The service configuration system provides a centralized way to manage Docker service build configurations. This replaces inline configuration logic in CI/CD workflows with a reusable, testable script.

## Components

### 1. Shell Script (`scripts/get-service-config.sh`)

A standalone script that generates service configuration based on service name and optional parameters:

- **Service context path** (where to build from)
- **Dockerfile path** (which Dockerfile to use)
- **Image name** (full registry path for the image)

**Features:**

- Comprehensive CLI with help and options
- Multiple output formats (env, json, yaml)
- Configurable registry and image name
- Robust error handling and validation
- Debugging output to stderr

### 2. GitHub Workflow Integration

The workflow now uses the script instead of inline bash case statements:

```yaml
- name: Set service context and dockerfile
  id: service-config
  run: |
    # Use the dedicated script to get service configuration
    ./scripts/get-service-config.sh \
      --service "${{ matrix.service }}" \
      --registry "${{ env.REGISTRY }}" \
      --image-name "${{ env.IMAGE_NAME }}" >> $GITHUB_OUTPUT
```

### 3. Makefile Integration

Added targets for local testing and development:

- `make service-config` - Show script help
- `make service-config-test` - Test various output formats

## Supported Services

The script supports all current services in the project:

- **backend** - Main backend API service
- **frontend** - React frontend application
- **auth-service** - Authentication microservice
- **vocabulary-service** - Vocabulary management microservice
- **news-service** - News content microservice
- **image-sync-service** - Image synchronization service

## Usage Examples

### Command Line Usage

```bash
# Get backend service config as environment variables
./scripts/get-service-config.sh --service backend

# Get frontend service config as JSON
./scripts/get-service-config.sh --service frontend --output-format json

# Get service config with custom registry
./scripts/get-service-config.sh \
  --service auth-service \
  --registry my-registry.com \
  --image-name my-app
```

### Output Examples

**Environment Variables Format (default):**

```
context=./backend
dockerfile=./backend/Dockerfile
image-name=ghcr.io/ansromanov/recnik/backend
```

**JSON Format:**

```json
{
  "context": "./frontend",
  "dockerfile": "./frontend/Dockerfile",
  "image_name": "ghcr.io/ansromanov/recnik/frontend"
}
```

**YAML Format:**

```yaml
context: ./services/auth-service
dockerfile: ./services/auth-service/Dockerfile
image_name: ghcr.io/ansromanov/recnik/auth-service
```

## Configuration Mapping

| Service | Context Path | Dockerfile Path | Image Suffix |
|---------|-------------|----------------|---------------|
| backend | `./backend` | `./backend/Dockerfile` | `/backend` |
| frontend | `./frontend` | `./frontend/Dockerfile` | `/frontend` |
| auth-service | `./services/auth-service` | `./services/auth-service/Dockerfile` | `/auth-service` |
| vocabulary-service | `./services/vocabulary-service` | `./services/vocabulary-service/Dockerfile` | `/vocabulary-service` |
| news-service | `./services/news-service` | `./services/news-service/Dockerfile` | `/news-service` |
| image-sync-service | `./image-sync-service` | `./image-sync-service/Dockerfile` | `/image-sync-service` |

## Local Testing

```bash
# Test all output formats
make service-config-test

# Test specific service
./scripts/get-service-config.sh --service backend

# Test with custom parameters
./scripts/get-service-config.sh \
  --service frontend \
  --registry localhost:5000 \
  --image-name my-app \
  --output-format json
```

## Benefits

1. **Maintainability**: Centralized configuration logic that's easier to modify
2. **Testability**: Can be tested locally without running CI/CD pipeline
3. **Reusability**: Same script can be used in different contexts
4. **Flexibility**: Multiple output formats for different use cases
5. **Consistency**: Ensures all services follow the same configuration pattern
6. **Debugging**: Clear error messages and debugging output

## Integration with Workflows

The script is designed to work seamlessly with GitHub Actions:

1. **Environment Variables**: Default format works directly with `$GITHUB_OUTPUT`
2. **Error Handling**: Non-zero exit codes fail the workflow appropriately
3. **Logging**: Debug output goes to stderr, doesn't interfere with main output
4. **Parameters**: Accepts GitHub Actions environment variables as parameters

## Future Enhancements

- Add support for service-specific build arguments
- Include health check configurations
- Support for multi-stage build configurations
- Integration with Docker Compose generation
- Service dependency mapping
