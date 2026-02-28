# Air Quality Index Weather Live

This project provides live Air Quality Index (AQI) and weather information with a React + Vite frontend and a FastAPI backend.

## Development

### Prerequisites
1. Python 3.8+
2. Node.js 18+
3. WAQI API Token (get free from [https://aqicn.org/data-platform/token/](https://aqicn.org/data-platform/token/))

### Environment Setup

**Step 1: Configure Environment Variables**

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your WAQI API token
# WAQI_API_TOKEN=your_actual_token_here
```

**Step 2: Backend (Python - virtualenv)**

```bash
# create and activate virtualenv (macOS/Linux)
python -m venv .venv
source .venv/bin/activate

# install Python deps
pip install -r requirements.txt

# run backend (uvicorn)
./.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Step 3: Frontend (Vite + React)**

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev -- --host
# open http://localhost:5173
```

## Build / Production

- Build frontend (Vite):

```bash
cd frontend
npm run build
```

- Build Docker image (requires Docker):

```bash
# from project root
docker build -t air-quality-app:latest .

# run container (exposes port 8000)
docker run -p 8000:8000 air-quality-app:latest
# then open http://localhost:8000 in the browser
```

## API Endpoints

- `GET /api`: Welcome message.
- `GET /api/air-quality`: Placeholder for air quality data.
- `GET /api/air-quality/{city}`: Fetch air quality data for a specific city.
- `GET /api/air-quality-coords/{lat}/{lon}`: Fetch air quality data for specific coordinates.

## Environment Variables

### Required
- `WAQI_API_TOKEN`: World Air Quality Index API token

### Setup Instructions
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Get your free API token from [WAQI Data Platform](https://aqicn.org/data-platform/token/)

3. Edit `.env` and replace `your_api_token_here` with your actual token:
   ```
   WAQI_API_TOKEN=your_actual_token_here
   ```

4. ⚠️ **Security**: Never commit `.env` to git. It's already in `.gitignore`.

## CI/CD Pipeline

This project includes a complete CI/CD pipeline using GitHub Actions for automated testing, code quality checks, and deployment.

### Features
- ✅ **Automated Testing**: Runs on every push and PR
- ✅ **Code Quality Checks**: Linting (flake8) and formatting (black)
- ✅ **Security Scanning**: Vulnerability detection with Trivy
- ✅ **Code Coverage**: Test coverage reporting with Codecov
- ✅ **Automated Deployment**: Deploy to Railway, Heroku, AWS, or DigitalOcean
- ✅ **Notifications**: Slack integration for deployment status

### Quick Start

**Run tests locally:**
```bash
pytest tests/ -v
```

**Check code quality:**
```bash
flake8 backend/ tests/
black --check backend/ tests/
```

**Format code:**
```bash
black backend/ tests/
```

For detailed CI/CD setup and configuration, see [.github/CI_CD_SETUP.md](.github/CI_CD_SETUP.md)

### GitHub Actions Workflows

1. **CI Pipeline** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml))
   - Backend tests and quality checks
   - Frontend build verification
   - Security vulnerability scanning
   - Code coverage reporting

2. **Deploy Pipeline** ([`.github/workflows/deploy.yml`](.github/workflows/deploy.yml))
   - Docker image build and push
   - Multi-platform deployment support
   - Automated notifications

## Testing

### Running Unit Tests

The project includes comprehensive unit tests for the backend API.

```bash
# Run all tests
./.venv/bin/python -m pytest tests/ -v

# Run with coverage report
./.venv/bin/python -m pytest tests/ --cov=backend --cov-report=html

# Run specific test file
./.venv/bin/python -m pytest tests/test_main.py -v
```

Tests cover:
- API endpoint functionality
- Caching mechanism
- Error handling (404, 503, timeouts)
- Request monitoring
- Cache expiration

## Monitoring & Analytics

### API Statistics

The API includes built-in monitoring and analytics:

```bash
# Check API health
curl http://127.0.0.1:8000/api/health

# View usage statistics
curl http://127.0.0.1:8000/api/stats
```

Statistics include:
- Total requests
- Cache hits/misses
- Cache hit rate
- Error count
- Cached items count

### Logging

The backend logs all requests with:
- Request method and path
- Response status code
- Processing time
- Cache hits/misses

Logs are output to console with timestamps.

## API Documentation

### Interactive Documentation

FastAPI provides automatic interactive API documentation:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

These interfaces allow you to:
- View all available endpoints
- See request/response schemas
- Test API calls directly from the browser
- View detailed parameter descriptions

### Available Endpoints

#### Information Endpoints
- `GET /api` - API welcome message and endpoint list
- `GET /api/health` - Health check for monitoring
- `GET /api/stats` - API usage statistics

#### Air Quality Endpoints
- `GET /api/air-quality/{city}` - Get AQI by city name
- `GET /api/air-quality-coords/{lat}/{lon}` - Get AQI by coordinates

### Response Headers

All responses include:
- `X-Process-Time` - Request processing time in seconds

## Notes
- The backend mounts the built frontend into `backend/frontend` and serves static files at root.
- The project uses environment variables for sensitive data like API tokens.
- Make sure to set up your `.env` file before running the backend (see Environment Variables section).

## User Guide

### Overview
This application provides live Air Quality Index (AQI) and weather information for cities worldwide. Users can search for a city or provide coordinates to get detailed AQI data.

### How to Use
1. Open the application in your browser.
2. Use the search bar to enter a city name.
3. View the AQI data, including dominant pollutants and forecasts.
4. Alternatively, provide latitude and longitude to fetch AQI data for specific coordinates.

### API Endpoints
- `GET /api`: Returns a welcome message.
- `GET /api/air-quality`: Placeholder for air quality data.
- `GET /api/air-quality/{city}`: Fetches AQI data for a specific city.
- `GET /api/air-quality-coords/{lat}/{lon}`: Fetches AQI data for specific coordinates.

### Notes
- Ensure the backend server is running at `http://127.0.0.1:8000`.
- The frontend runs at `http://localhost:5173` (or another port if specified).

If you want, I can commit these README changes and create a small release/build script.