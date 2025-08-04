# Docker Tagging Fix

## Problem

The GitHub Actions workflow for building Docker images was failing with an invalid Docker tag format error:

```
ERROR: failed to build: invalid tag "ghcr.io/ansromanov/recnik/backend:-50bba56": invalid reference format
```

## Root Cause

The issue was in the `docker/metadata-action@v5` configuration in `.github/workflows/docker-build.yml`. The problematic tag configuration was:

```yaml
tags: |
  type=sha,prefix={{branch}}-
```

For pull requests, the `{{branch}}` template becomes empty or invalid, resulting in malformed tags like `ghcr.io/ansromanov/recnik/backend:-50bba56` (note the colon followed immediately by a hyphen).

## Solution

### 1. Fixed Tag Generation

Updated the metadata action configuration to handle different event types properly:

```yaml
tags: |
  # set latest tag for main branch
  type=ref,event=branch
  type=ref,event=pr
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}
  type=semver,pattern={{major}}
  type=raw,value=latest,enable={{is_default_branch}}
  # add short sha for all builds (fixed format)
  type=sha,prefix={{branch}}-,enable={{is_default_branch}}
  type=sha,prefix=pr-{{branch}}-,enable=${{ github.event_name == 'pull_request' }}
  type=sha,prefix=develop-,enable=${{ github.ref == 'refs/heads/develop' }}
```

This creates proper tags for different scenarios:

- **Pull Requests**: `pr-1`, `pr-1-abc123`
- **Main Branch**: `main`, `latest`, `main-abc123`
- **Develop Branch**: `develop`, `develop-abc123`
- **Tags**: `v1.2.3`, `1.2`, `1`

### 2. Consistent Tagging Across Jobs

Updated the deployment manifest and security scan jobs to use consistent tag formats:

```bash
# Determine the tag based on event type
if [[ "${{ github.event_name }}" == "pull_request" ]]; then
  TAG="pr-${{ github.event.number }}"
elif [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
  TAG="main"
elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
  TAG="develop"
elif [[ "${{ github.ref }}" =~ ^refs/tags/v.* ]]; then
  TAG="${{ github.ref_name }}"
else
  TAG="${{ github.ref_name }}"
fi
```

## Tag Format Examples

### Pull Request (PR #1)

- `ghcr.io/ansromanov/recnik/backend:pr-1`
- `ghcr.io/ansromanov/recnik/frontend:pr-1`

### Main Branch

- `ghcr.io/ansromanov/recnik/backend:main`
- `ghcr.io/ansromanov/recnik/backend:latest`
- `ghcr.io/ansromanov/recnik/backend:main-abc123` (with SHA)

### Develop Branch

- `ghcr.io/ansromanov/recnik/backend:develop`
- `ghcr.io/ansromanov/recnik/backend:develop-abc123` (with SHA)

### Version Tags (v1.2.3)

- `ghcr.io/ansromanov/recnik/backend:v1.2.3`
- `ghcr.io/ansromanov/recnik/backend:1.2.3`
- `ghcr.io/ansromanov/recnik/backend:1.2`
- `ghcr.io/ansromanov/recnik/backend:1`

## Files Modified

1. **`.github/workflows/docker-build.yml`**
   - Fixed metadata action tag configuration
   - Updated deployment manifest generation
   - Updated security scan job tagging
   - Replaced inline service configuration with script call

2. **`scripts/get-service-config.sh`** (new)
   - Centralized service configuration logic
   - Supports multiple output formats (env, json, yaml)
   - Configurable registry and image name
   - Comprehensive help and error handling

3. **`Makefile`**
   - Added `service-config` and `service-config-test` targets
   - Updated help documentation

## Benefits

1. **Valid Docker Tags**: All generated tags now follow proper Docker tag format
2. **Consistent Naming**: Same tag format used across build, deployment, and security jobs
3. **Clear Identification**: Easy to identify images by branch/PR/version
4. **Better Organization**: Logical tag hierarchy for different environments

## Testing

The fix can be tested by:

1. Creating a pull request (should generate `pr-N` tags)
2. Pushing to main branch (should generate `main` and `latest` tags)
3. Pushing to develop branch (should generate `develop` tags)
4. Creating version tags (should generate semantic version tags)

## Future Improvements

- Consider adding build date or commit message to labels
- Implement tag cleanup strategies for development branches
- Add support for feature branch naming conventions
