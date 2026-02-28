# GitHub Actions CI/CD Setup Guide

This document explains the CI/CD pipeline configuration for the Air Quality Index Weather Live project.

## Overview

The project uses GitHub Actions for continuous integration and deployment with the following workflows:

### 1. CI Pipeline (`.github/workflows/ci.yml`)

Runs automatically on every push and pull request to `main` and `develop` branches.

#### Jobs:

**Backend Tests & Quality Checks**
- Python linting with `flake8`
- Code formatting checks with `black`
- Unit tests with `pytest`
- Uploads test results as artifacts

**Frontend Quality Checks**
- TypeScript compilation check
- Frontend build verification
- Uploads build artifacts

**Security Scanning**
- Vulnerability scanning with Trivy
- Uploads results to GitHub Security tab

**Code Coverage**
- Runs tests with coverage reporting
- Uploads results to Codecov
- Generates HTML coverage report

### 2. Deployment Pipeline (`.github/workflows/deploy.yml`)

Runs on push to `main` branch or can be triggered manually.

#### Jobs:

**Build & Push Docker Image**
- Builds Docker image using Buildx
- Pushes to Docker Hub
- Uses layer caching for faster builds

**Deploy to Cloud Platform**
- Supports multiple deployment targets:
  - Railway
  - Heroku
  - AWS ECS
  - DigitalOcean App Platform
- Configure using GitHub Secrets

**Deployment Notification**
- Sends Slack notifications
- Creates GitHub deployment records

## Required GitHub Secrets

Configure these in your GitHub repository settings (Settings → Secrets and variables → Actions):

### Required for CI:
- `WAQI_API_TOKEN` - Your World Air Quality Index API token

### Required for Docker Build:
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password or access token

### Optional for Deployment:

**Railway:**
- `RAILWAY_TOKEN` - Railway API token
- `RAILWAY_SERVICE_ID` - Railway service ID

**Heroku:**
- `HEROKU_API_KEY` - Heroku API key
- `HEROKU_APP_NAME` - Heroku app name
- `HEROKU_EMAIL` - Heroku account email

**AWS ECS:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region (e.g., us-east-1)
- `ECS_CLUSTER_NAME` - ECS cluster name
- `ECS_SERVICE_NAME` - ECS service name

**DigitalOcean:**
- `DIGITALOCEAN_ACCESS_TOKEN` - DO API token
- `DO_APP_NAME` - App Platform app name

**Notifications:**
- `SLACK_WEBHOOK_URL` - Slack webhook URL for notifications

## Setting Up GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the appropriate name and value
5. Save

## Code Quality Tools Configuration

### Flake8 (`.flake8`)
Python linting configuration with:
- Max line length: 127 characters
- Max complexity: 10
- Ignores common formatting conflicts with Black

### Black (`pyproject.toml`)
Python code formatter configuration:
- Line length: 127 characters
- Target Python version: 3.11

### pytest (`pyproject.toml`)
Test configuration:
- Test discovery in `tests/` directory
- Verbose output with short tracebacks

### Coverage (`pyproject.toml`)
Code coverage configuration:
- Source: `backend/` directory
- Excludes tests and virtual environments
- Common exclusion patterns

## Running Quality Checks Locally

### Install development dependencies:
```bash
pip install flake8 black pytest pytest-cov
```

### Run linting:
```bash
flake8 backend/ tests/
```

### Check code formatting:
```bash
black --check backend/ tests/
```

### Format code:
```bash
black backend/ tests/
```

### Run tests:
```bash
pytest tests/ -v
```

### Run tests with coverage:
```bash
pytest tests/ --cov=backend --cov-report=html
```

## Deployment Options

The deployment workflow supports multiple platforms. Uncomment and configure the sections for your preferred platform:

### Railway (Recommended for simplicity)
1. Create account at railway.app
2. Create new project and link GitHub repo
3. Add `RAILWAY_TOKEN` and `RAILWAY_SERVICE_ID` secrets
4. Push to main branch

### Heroku
1. Create Heroku app
2. Add `HEROKU_API_KEY`, `HEROKU_APP_NAME`, `HEROKU_EMAIL` secrets
3. Push to main branch

### AWS ECS
1. Set up ECS cluster and service
2. Configure AWS secrets
3. Push to main branch

### DigitalOcean App Platform
1. Create app on DigitalOcean
2. Add `DIGITALOCEAN_ACCESS_TOKEN` and `DO_APP_NAME` secrets
3. Push to main branch

## Workflow Status Badges

Add these badges to your README.md to show CI/CD status:

```markdown
![CI Pipeline](https://github.com/YOUR_USERNAME/air_quality_index_weather_live/actions/workflows/ci.yml/badge.svg)
![Deploy Pipeline](https://github.com/YOUR_USERNAME/air_quality_index_weather_live/actions/workflows/deploy.yml/badge.svg)
[![codecov](https://codecov.io/gh/YOUR_USERNAME/air_quality_index_weather_live/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_USERNAME/air_quality_index_weather_live)
```

## Troubleshooting

### CI Fails on Flake8
- Run `flake8 backend/ tests/` locally
- Fix any linting errors
- Commit and push

### CI Fails on Black
- Run `black backend/ tests/` to format code
- Commit and push

### Tests Fail
- Make sure `WAQI_API_TOKEN` secret is set
- Run tests locally: `pytest tests/ -v`
- Check test output for specific failures

### Deployment Fails
- Verify all required secrets are configured
- Check deployment platform status
- Review workflow logs in GitHub Actions tab

## Best Practices

1. **Always run tests locally** before pushing
2. **Use feature branches** and create pull requests
3. **Review CI results** before merging PRs
4. **Monitor deployment notifications** 
5. **Keep dependencies updated** with Dependabot
6. **Review security scan results** regularly

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Black Documentation](https://black.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.com/)
