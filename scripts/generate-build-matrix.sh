#!/bin/bash
# Generate build matrix for Docker services based on changed files and trigger conditions

set -euo pipefail

# Function to print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Generate a JSON matrix of services to build for CI/CD workflows.

Options:
    -h, --help              Show this help message
    -e, --event EVENT       GitHub event name (push, pull_request, workflow_dispatch)
    -r, --ref REF           Git reference (branch/tag name)
    -b, --backend BOOL      Backend changed (true/false)
    -f, --frontend BOOL     Frontend changed (true/false)
    -a, --auth-service BOOL Auth service changed (true/false)
    -v, --vocab-service BOOL Vocabulary service changed (true/false)
    -n, --news-service BOOL News service changed (true/false)
    -i, --image-service BOOL Image sync service changed (true/false)
    --output-format FORMAT  Output format: json, comma, or list (default: json)

Examples:
    # Generate matrix for all services (main branch or manual trigger)
    $0 --event workflow_dispatch

    # Generate matrix for changed services only
    $0 --event pull_request --backend true --frontend false --auth-service false --vocab-service false --news-service false --image-service false

    # Output as comma-separated list
    $0 --event pull_request --backend true --frontend true --output-format comma
EOF
}

# Default values
EVENT=""
REF=""
BACKEND="false"
FRONTEND="false"
AUTH_SERVICE="false"
VOCAB_SERVICE="false"
NEWS_SERVICE="false"
IMAGE_SERVICE="false"
OUTPUT_FORMAT="json"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -e|--event)
            EVENT="$2"
            shift 2
            ;;
        -r|--ref)
            REF="$2"
            shift 2
            ;;
        -b|--backend)
            BACKEND="$2"
            shift 2
            ;;
        -f|--frontend)
            FRONTEND="$2"
            shift 2
            ;;
        -a|--auth-service)
            AUTH_SERVICE="$2"
            shift 2
            ;;
        -v|--vocab-service)
            VOCAB_SERVICE="$2"
            shift 2
            ;;
        -n|--news-service)
            NEWS_SERVICE="$2"
            shift 2
            ;;
        -i|--image-service)
            IMAGE_SERVICE="$2"
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
if [[ -z "$EVENT" ]]; then
    echo "Error: --event parameter is required" >&2
    exit 1
fi

# Function to build services list
build_services_list() {
    local services=""

    # Always build all services on main branch, tags, or workflow_dispatch
    if [[ "$EVENT" == "workflow_dispatch" ]] || \
       [[ "$REF" == "refs/heads/main" ]] || \
       [[ "$REF" =~ ^refs/tags/v.* ]]; then
        services="backend,frontend,auth-service,vocabulary-service,news-service,image-sync-service"
    else
        # Build only changed services for other events
        if [[ "$BACKEND" == "true" ]]; then
            services="${services}backend,"
        fi
        if [[ "$FRONTEND" == "true" ]]; then
            services="${services}frontend,"
        fi
        if [[ "$AUTH_SERVICE" == "true" ]]; then
            services="${services}auth-service,"
        fi
        if [[ "$VOCAB_SERVICE" == "true" ]]; then
            services="${services}vocabulary-service,"
        fi
        if [[ "$NEWS_SERVICE" == "true" ]]; then
            services="${services}news-service,"
        fi
        if [[ "$IMAGE_SERVICE" == "true" ]]; then
            services="${services}image-sync-service,"
        fi
        # Remove trailing comma
        services="${services%,}"
    fi

    echo "$services"
}

# Generate services list
services=$(build_services_list)

# Output in requested format
case "$OUTPUT_FORMAT" in
    json)
        if [[ -n "$services" ]]; then
            echo "$services" | jq -R 'split(",") | map(select(length > 0))'
        else
            echo "[]"
        fi
        ;;
    comma)
        echo "$services"
        ;;
    list)
        if [[ -n "$services" ]]; then
            echo "$services" | tr ',' '\n'
        fi
        ;;
    *)
        echo "Error: Invalid output format '$OUTPUT_FORMAT'. Use: json, comma, or list" >&2
        exit 1
        ;;
esac

# Log to stderr for debugging (won't interfere with JSON output)
if [[ -n "$services" ]]; then
    echo "Services to build: $services" >&2
else
    echo "No services to build" >&2
fi
