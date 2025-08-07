#!/bin/bash
# Get service configuration (context, dockerfile, image-name) for Docker builds

set -euo pipefail

# Function to print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Get service configuration for Docker builds.

Options:
    -h, --help              Show this help message
    -s, --service SERVICE   Service name (backend, frontend, auth-service, etc.)
    -r, --registry REGISTRY Container registry URL (default: ghcr.io)
    -i, --image-name IMAGE  Base image name (default: ansromanov/recnik)
    --output-format FORMAT  Output format: env, json, or yaml (default: env)

Examples:
    # Get backend service config as environment variables
    $0 --service backend

    # Get frontend service config as JSON
    $0 --service frontend --output-format json

    # Get service config with custom registry
    $0 --service auth-service --registry my-registry.com --image-name my-app
EOF
}

# Default values
SERVICE=""
REGISTRY="ghcr.io"
IMAGE_NAME="ansromanov/recnik"
OUTPUT_FORMAT="env"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -i|--image-name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --output-format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SERVICE" ]]; then
    echo "Error: --service parameter is required" >&2
    exit 1
fi

# Function to get service configuration
get_service_config() {
    local service="$1"
    local context=""
    local dockerfile=""
    local image_name=""

    case "$service" in
        "backend")
            context="./services/backend-service"
            dockerfile="./services/backend-service/Dockerfile"
            image_name="${REGISTRY}/${IMAGE_NAME}/backend"
            ;;
        "frontend")
            context="./frontend"
            dockerfile="./frontend/Dockerfile"
            image_name="${REGISTRY}/${IMAGE_NAME}/frontend"
            ;;
        "auth-service")
            context="./services/auth-service"
            dockerfile="./services/auth-service/Dockerfile"
            image_name="${REGISTRY}/${IMAGE_NAME}/auth-service"
            ;;
        "vocabulary-service")
            context="./services/vocabulary-service"
            dockerfile="./services/vocabulary-service/Dockerfile"
            image_name="${REGISTRY}/${IMAGE_NAME}/vocabulary-service"
            ;;
        "news-service")
            context="./services/news-service"
            dockerfile="./services/news-service/Dockerfile"
            image_name="${REGISTRY}/${IMAGE_NAME}/news-service"
            ;;
        "image-sync-service")
            context="./services/image-sync-service"
            dockerfile="./services/image-sync-service/Dockerfile"
            image_name="${REGISTRY}/${IMAGE_NAME}/image-sync-service"
            ;;
        *)
            echo "Error: Unknown service '$service'" >&2
            echo "Supported services: backend, frontend, auth-service, vocabulary-service, news-service, image-sync-service" >&2
            exit 1
            ;;
    esac

    # Output in requested format
    case "$OUTPUT_FORMAT" in
        env)
            echo "context=${context}"
            echo "dockerfile=${dockerfile}"
            echo "image-name=${image_name}"
            ;;
        json)
            cat << EOF
{
  "context": "${context}",
  "dockerfile": "${dockerfile}",
  "image_name": "${image_name}"
}
EOF
            ;;
        yaml)
            cat << EOF
context: ${context}
dockerfile: ${dockerfile}
image_name: ${image_name}
EOF
            ;;
        *)
            echo "Error: Invalid output format '$OUTPUT_FORMAT'. Use: env, json, or yaml" >&2
            exit 1
            ;;
    esac
}

# Generate service configuration
get_service_config "$SERVICE"

# Log to stderr for debugging (won't interfere with output)
echo "Generated config for service: $SERVICE" >&2
