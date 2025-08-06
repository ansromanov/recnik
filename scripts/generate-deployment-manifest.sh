#!/bin/bash
# Generate deployment manifest for Recnik services

set -euo pipefail

# Function to print usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Generate a deployment manifest for Docker services.

Options:
    -h, --help              Show this help message
    -e, --event EVENT       GitHub event name (push, pull_request, workflow_dispatch)
    -r, --ref REF           Git reference (branch/tag name)
    -n, --ref-name NAME     Git reference name (e.g., main, develop, v1.0.0)
    -s, --sha SHA           Git commit SHA
    -p, --pr-number NUM     Pull request number (for PR events)
    --registry REGISTRY     Container registry URL (default: ghcr.io)
    --image-name IMAGE      Base image name (default: ansromanov/recnik)
    --output-file FILE      Output file path (default: deployment-manifest.yml)
    --services SERVICES     Comma-separated list of services (default: all)

Examples:
    # Generate manifest for pull request
    $0 --event pull_request --pr-number 1 --sha abc123

    # Generate manifest for main branch
    $0 --event push --ref refs/heads/main --ref-name main --sha def456

    # Generate manifest for specific services only
    $0 --event push --ref refs/heads/main --ref-name main --sha def456 --services backend,frontend

    # Generate manifest with custom registry
    $0 --event push --ref refs/heads/main --ref-name main --sha def456 --registry my-registry.com --image-name my-app
EOF
}

# Default values
EVENT=""
REF=""
REF_NAME=""
SHA=""
PR_NUMBER=""
REGISTRY="ghcr.io"
IMAGE_NAME="ansromanov/recnik"
OUTPUT_FILE="deployment-manifest.yml"
SERVICES="backend,frontend,auth-service,vocabulary-service,news-service,image-sync-service"

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
        -n|--ref-name)
            REF_NAME="$2"
            shift 2
            ;;
        -s|--sha)
            SHA="$2"
            shift 2
            ;;
        -p|--pr-number)
            PR_NUMBER="$2"
            shift 2
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --image-name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --output-file)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --services)
            SERVICES="$2"
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

if [[ -z "$SHA" ]]; then
    echo "Error: --sha parameter is required" >&2
    exit 1
fi

# Function to determine tag based on event type
determine_tag() {
    local event="$1"
    local ref="$2"
    local ref_name="$3"
    local pr_number="$4"

    if [[ "$event" == "pull_request" ]]; then
        if [[ -n "$pr_number" ]]; then
            echo "pr-${pr_number}"
        else
            echo "pr-unknown"
        fi
    elif [[ "$ref" == "refs/heads/main" ]]; then
        echo "main"
    elif [[ "$ref" == "refs/heads/develop" ]]; then
        echo "develop"
    elif [[ "$ref" =~ ^refs/tags/v.* ]]; then
        echo "$ref_name"
    else
        echo "$ref_name"
    fi
}

# Function to generate service image reference
generate_image_ref() {
    local service="$1"
    local tag="$2"
    echo "${REGISTRY}/${IMAGE_NAME}/${service}:${tag}"
}

# Function to generate deployment manifest
generate_manifest() {
    local tag="$1"
    local services_list="$2"
    local output_file="$3"

    # Convert comma-separated services to array
    IFS=',' read -ra SERVICES_ARRAY <<< "$services_list"

    # Start writing the manifest
    cat > "$output_file" << EOF
# Recnik - Deployment Manifest
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
# Commit: ${SHA}
# Branch/Tag: ${REF_NAME:-unknown}
# Tag: ${tag}
# Event: ${EVENT}

version: "3.8"

services:
EOF

    # Add each service to the manifest
    for service in "${SERVICES_ARRAY[@]}"; do
        service=$(echo "$service" | xargs)  # Trim whitespace
        if [[ -n "$service" ]]; then
            local image_ref=$(generate_image_ref "$service" "$tag")
            cat >> "$output_file" << EOF
  ${service}:
    image: ${image_ref}

EOF
        fi
    done

    # Remove trailing newlines and add final newline
    sed -i '' -e :a -e '/^\s*$/N;ba' -e 's/\n*$//' "$output_file" 2>/dev/null || \
    sed -i -e :a -e '/^\s*$/N;ba' -e 's/\n*$//' "$output_file" 2>/dev/null || true
    echo "" >> "$output_file"
}

# Determine the tag
TAG=$(determine_tag "$EVENT" "$REF" "$REF_NAME" "$PR_NUMBER")

# Generate the deployment manifest
generate_manifest "$TAG" "$SERVICES" "$OUTPUT_FILE"

# Output success message to stderr (won't interfere with file output)
echo "Generated deployment manifest: $OUTPUT_FILE" >&2
echo "Tag used: $TAG" >&2
echo "Services included: $SERVICES" >&2

# Output the file path for potential use in pipelines
echo "$OUTPUT_FILE"
