import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from functools import lru_cache
from datetime import datetime, timedelta
import time
import os
from dotenv import load_dotenv
import logging
import pathlib

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize the FastAPI app with metadata for Swagger documentation
app = FastAPI(
    title="Air Quality Index API",
    description="API for fetching real-time air quality index (AQI) data from World Air Quality Index (WAQI)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Simple cache with timestamp for API responses
cache = {}
CACHE_DURATION = 300  # 5 minutes in seconds

# Request tracking for analytics
request_stats = {"total_requests": 0, "cache_hits": 0, "cache_misses": 0, "errors": 0}


# Monitoring middleware
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Middleware for monitoring and logging requests"""
    start_time = time.time()
    request_stats["total_requests"] += 1

    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(f"Response: {response.status_code} (took {process_time:.3f}s)")

        # Add custom header with process time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        request_stats["errors"] += 1
        logger.error(f"Error processing request: {str(e)}")
        raise


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# compute project base dir (repo root)
BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()


# Load API token from environment variable
API_TOKEN = os.getenv("WAQI_API_TOKEN")
if not API_TOKEN:
    raise ValueError("WAQI_API_TOKEN environment variable is not set. Please set it in your .env file or environment.")
BASE_URL = "https://api.waqi.info/feed/"


def get_cached_data(key):
    """Get cached data if available and not expired"""
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_DURATION:
            request_stats["cache_hits"] += 1
            logger.debug(f"Cache hit for key: {key}")
            return data
    request_stats["cache_misses"] += 1
    logger.debug(f"Cache miss for key: {key}")
    return None


def set_cached_data(key, data):
    """Cache data with current timestamp"""
    cache[key] = (data, time.time())


def fetch_aqi_data(url):
    """Fetch AQI data from WAQI API with error handling"""
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City or location not found")
        elif response.status_code == 403:
            raise HTTPException(status_code=403, detail="Invalid API token")
        elif response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch air quality data")

        data = response.json()

        if data.get("status") == "error":
            raise HTTPException(status_code=400, detail=data.get("data", "Invalid response from WAQI API"))
        elif data.get("status") != "ok":
            raise HTTPException(status_code=400, detail="Invalid response from WAQI API")

        return data.get("data", {})

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout - external API is not responding")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Connection error - unable to reach external API")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# keep an API root under /api so that static mounting doesn't conflict
@app.get(
    "/api", summary="API Welcome Message", description="Returns a welcome message for the Air Quality Index API", tags=["Info"]
)
def read_root():
    """Get API welcome message and basic information"""
    return {
        "message": "Welcome to the Air Quality Index API!",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/health",
            "stats": "/api/stats",
            "city_search": "/api/air-quality/{city}",
            "coords_search": "/api/air-quality-coords/{lat}/{lon}",
        },
    }


@app.get("/api/health", summary="Health Check", description="Check if the API is running and healthy", tags=["Info"])
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "cache_size": len(cache)}


@app.get("/api/stats", summary="API Statistics", description="Get API usage statistics and analytics", tags=["Info"])
def get_stats():
    """Get API usage statistics for monitoring and analytics"""
    cache_hit_rate = (
        (request_stats["cache_hits"] / (request_stats["cache_hits"] + request_stats["cache_misses"]) * 100)
        if (request_stats["cache_hits"] + request_stats["cache_misses"]) > 0
        else 0
    )

    return {
        "total_requests": request_stats["total_requests"],
        "cache_hits": request_stats["cache_hits"],
        "cache_misses": request_stats["cache_misses"],
        "cache_hit_rate": f"{cache_hit_rate:.2f}%",
        "errors": request_stats["errors"],
        "cached_items": len(cache),
    }


@app.get(
    "/api/air-quality",
    summary="Air Quality Placeholder",
    description="Placeholder endpoint for general air quality data",
    tags=["Air Quality"],
)
def get_air_quality():
    """Placeholder for air quality data fetching logic"""
    return {"data": "Air quality data will be here."}


@app.get(
    "/api/air-quality/{city}",
    summary="Get AQI by City Name",
    description="Fetch air quality index data for a specific city by name",
    tags=["Air Quality"],
    responses={
        200: {"description": "Successful response with AQI data"},
        400: {"description": "Invalid response from WAQI API"},
        404: {"description": "City not found"},
        503: {"description": "Service unavailable - unable to reach external API"},
    },
)
def get_air_quality_by_city(city: str):
    """
    Get air quality data for a specific city.

    Parameters:
    - **city**: City name (e.g., London, Paris, Tokyo)

    Returns:
    - AQI value
    - Dominant pollutant
    - Temperature, humidity, and other measurements
    - Forecast data
    """
    cache_key = f"city:{city}"

    # Check cache first
    cached_data = get_cached_data(cache_key)
    if cached_data:
        logger.info(f"Returning cached data for city: {city}")
        return cached_data

    # Fetch fresh data
    logger.info(f"Fetching fresh data for city: {city}")
    url = f"{BASE_URL}{city}/?token={API_TOKEN}"
    data = fetch_aqi_data(url)

    # Cache the result
    set_cached_data(cache_key, data)
    return data


@app.get(
    "/api/air-quality-coords/{lat}/{lon}",
    summary="Get AQI by Coordinates",
    description="Fetch air quality index data for specific geographic coordinates",
    tags=["Air Quality"],
    responses={
        200: {"description": "Successful response with AQI data"},
        400: {"description": "Invalid response from WAQI API"},
        404: {"description": "Location not found"},
        503: {"description": "Service unavailable - unable to reach external API"},
    },
)
def get_air_quality_by_coords(lat: float, lon: float):
    """
    Get air quality data for specific geographic coordinates.

    Parameters:
    - **lat**: Latitude (e.g., 51.5074)
    - **lon**: Longitude (e.g., -0.1278)

    Returns:
    - AQI value
    - Dominant pollutant
    - Temperature, humidity, and other measurements
    - Forecast data
    """
    cache_key = f"coords:{lat}:{lon}"

    # Check cache first
    cached_data = get_cached_data(cache_key)
    if cached_data:
        logger.info(f"Returning cached data for coordinates: {lat}, {lon}")
        return cached_data

    # Fetch fresh data
    logger.info(f"Fetching fresh data for coordinates: {lat}, {lon}")
    url = f"{BASE_URL}geo:{lat};{lon}/?token={API_TOKEN}"
    data = fetch_aqi_data(url)

    # Cache the result
    set_cached_data(cache_key, data)
    return data


@app.get("/api/data")
async def get_data():
    return {"message": "Hello from FastAPI!", "data": {"air_quality": 42, "weather": "Sunny"}}


# Mount the built frontend at root after API routes so /api endpoints take precedence.
app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")
