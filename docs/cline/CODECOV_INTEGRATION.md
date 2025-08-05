# Codecov Integration Setup

This document explains the Codecov integration that has been added to the Serbian Vocabulary App deployment pipeline.

## Overview

Codecov is now integrated into the CI/CD pipeline to provide comprehensive test coverage reporting and analysis. The integration includes:

- Automated test execution with coverage collection
- Coverage upload to Codecov for all project components
- PR comments with coverage diff and statistics
- Coverage status checks that can block merges if coverage drops

## Files Added/Modified

### 1. `.github/workflows/test-and-coverage.yml`

New workflow that runs tests and uploads coverage data to Codecov. This workflow:

- Runs on push to `main`/`develop` branches and all PRs
- Sets up test databases (PostgreSQL, Redis)
- Executes tests for backend, frontend, and microservices
- Generates coverage reports in XML format
- Uploads coverage to Codecov with proper flags
- Adds coverage comments to PRs

### 2. `codecov.yml`

Codecov configuration file that defines:

- Coverage targets (80% for backend, 70% for frontend, 75% for services)
- File ignore patterns
- Component flags for organized reporting
- PR comment layout and behavior
- Status check configuration

## Setup Requirements

### 1. Codecov Account Setup

1. Go to [codecov.io](https://codecov.io) and sign up/login with GitHub
2. Add your repository to Codecov
3. Get the repository upload token

### 2. GitHub Secrets

Add the following secret to your GitHub repository:

- `CODECOV_TOKEN`: Your Codecov upload token (found in repository settings on Codecov)

To add the secret:

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `CODECOV_TOKEN`
4. Value: Your token from Codecov
5. Click "Add secret"

## Coverage Targets

The following coverage targets are configured:

| Component | Project Target | Patch Target | Threshold |
|-----------|----------------|--------------|-----------|
| Backend | 80% | 70% | 2% |
| Frontend | 70% | N/A | 3% |
| Services | 75% | 65% | 3% |

## Workflow Integration

The test workflow runs independently but can be integrated with the build workflow by:

1. Making the build workflow depend on successful test completion
2. Adding coverage as a required status check in branch protection rules

## Coverage Reports

### In Pull Requests

- Automatic comments showing coverage diff
- Status checks indicating if coverage targets are met
- File-by-file coverage breakdown

### In Codecov Dashboard

- Historical coverage trends
- Detailed file and function coverage
- Coverage comparison between branches
- Sunburst charts and other visualizations

## Local Development

To run tests with coverage locally:

```bash
# Backend tests
make test-cov

# Or directly with pytest
cd backend
uv run pytest --cov=. --cov-report=html --cov-report=term-missing
```

Coverage reports will be generated in `backend/htmlcov/` directory.

## Troubleshooting

### Common Issues

1. **Coverage upload fails**
   - Check if `CODECOV_TOKEN` secret is set correctly
   - Ensure the token has the right permissions
   - Check workflow logs for specific error messages

2. **Tests fail in CI but pass locally**
   - Check environment variables in the workflow
   - Ensure test databases are properly configured
   - Verify dependencies are correctly installed

3. **Coverage reports not appearing**
   - Check if coverage files are generated correctly
   - Verify file paths in codecov.yml match your project structure
   - Ensure proper flags are used in upload action

### Debugging Steps

1. Check workflow logs in GitHub Actions
2. Verify coverage files are generated (check artifacts)
3. Check Codecov dashboard for upload status
4. Review codecov.yml configuration

## Configuration Customization

### Adjusting Coverage Targets

Edit `codecov.yml` to modify coverage targets:

```yaml
coverage:
  status:
    project:
      backend:
        target: 85%  # Increase target
        threshold: 1%  # Stricter threshold
```

### Adding New Components

To add coverage tracking for new services:

1. Add the service to the test workflow matrix
2. Add a new flag in `codecov.yml`
3. Update the coverage status configuration

### Modifying Ignore Patterns

Update the `ignore` section in `codecov.yml` to exclude additional files:

```yaml
ignore:
  - "new-directory/"
  - "**/*.generated.py"
```

## Best Practices

1. **Maintain High Coverage**: Aim for >80% overall coverage
2. **Test Critical Paths**: Ensure business logic has high coverage
3. **Monitor Trends**: Use Codecov dashboard to track coverage over time
4. **Review PR Coverage**: Always check coverage diff in PRs
5. **Set Reasonable Targets**: Balance coverage goals with development velocity

## Integration with Branch Protection

To enforce coverage requirements:

1. Go to GitHub repository → Settings → Branches
2. Add rule for main/develop branches
3. Enable "Require status checks to pass before merging"
4. Add Codecov status checks to required checks

This ensures PRs cannot be merged if they significantly reduce coverage.
