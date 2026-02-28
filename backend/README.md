# FastAPI Backend

This is the backend for the Air Quality Index Weather Live project, built with FastAPI.

## Setup

### 1. Environment Variables
Create a `.env` file in the project root with your WAQI API token:
```bash
# From project root
cp .env.example .env
```

Edit `.env` and add your token:
```
WAQI_API_TOKEN=your_actual_token_here
```

Get your free token from: https://aqicn.org/data-platform/token/

### 2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Run the development server:
   ```bash
   uvicorn backend.main:app --reload
   ```

### 4. Access the API documentation at:
   - Swagger UI: `http://127.0.0.1:8000/docs`
   - ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

- `GET /api`: Welcome message.
- `GET /api/air-quality`: Placeholder for air quality data.
- `GET /api/air-quality/{city}`: Fetch air quality data for a specific city.
- `GET /api/air-quality-coords/{lat}/{lon}`: Fetch air quality data for specific coordinates.

## Environment Variables

### Required
- `WAQI_API_TOKEN`: World Air Quality Index API token for fetching air quality data

### Setup
The backend uses `python-dotenv` to load environment variables from a `.env` file in the project root. Make sure to create this file before running the server (see Setup section above).

⚠️ **Security**: Never commit your `.env` file to version control. It's already included in `.gitignore`.

## Testing

Run unit tests:
```bash
# From project root
./.venv/bin/python -m pytest tests/ -v
```

## Monitoring

The API includes built-in monitoring and analytics:

### Health Check
```bash
curl http://127.0.0.1:8000/api/health
```

### Statistics
```bash
curl http://127.0.0.1:8000/api/stats
```

Statistics tracked:
- Total requests
- Cache hits/misses and hit rate
- Error count
- Current cache size

### Logging

All requests are logged with:
- Request details (method, path)
- Response status and processing time
- Cache operations
- Error details

## Features

- **Caching**: 5-minute cache for API responses to reduce external API calls
- **Error Handling**: Comprehensive error handling for various failure scenarios
- **Monitoring**: Built-in request tracking and analytics
- **Documentation**: Auto-generated Swagger UI at `/docs`
- **Health Checks**: Endpoint for service monitoring