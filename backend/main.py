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
if not API_TOKEN or API_TOKEN == "your_api_token_here":
    logger.warning("WAQI_API_TOKEN is not set or using default value. Switching to 'demo' token.")
    API_TOKEN = "demo"
BASE_URL = "https://api.waqi.info/feed/"

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


def fetch_openweather_aqi(lat: float, lon: float):
    """Fallback to OpenWeatherMap Air Pollution API if WAQI is stale"""
    if not OPENWEATHER_API_KEY:
        return None
    try:
        # OpenWeather Air Pollution API: http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_key}
        url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            ow_data = resp.json()
            if ow_data.get("list"):
                main = ow_data["list"][0]["main"]
                components = ow_data["list"][0]["components"]
                dt = ow_data["list"][0]["dt"]
                
                # OpenWeather uses 1-5 index (1=Good, 5=Very Poor)
                # We'll map it to WAQI-like numbers or just return as is with a flag
                # For simplicity, we'll try to return a structure compatible with frontend
                # Native OpenWeather AQI: 1: Good, 2: Fair, 3: Moderate, 4: Poor, 5: Very Poor
                # WAQI scale is 0-500+. We'll do a rough mapping for the UI.
                aqi_map = {1: 25, 2: 75, 3: 125, 4: 175, 5: 250}
                
                return {
                    "aqi": aqi_map.get(main.get("aqi"), 0),
                    "idx": "owm",
                    "attributions": [{"name": "OpenWeatherMap", "url": "https://openweathermap.org/"}],
                    "city": {"name": "OpenWeather Model Data"},
                    "time": {"s": datetime.fromtimestamp(dt).strftime('%Y-%m-%d %H:%M:%S')},
                    "iaqi": {
                        "pm25": {"v": components.get("pm2_5")},
                        "pm10": {"v": components.get("pm10")},
                        "no2": {"v": components.get("no2")},
                        "so2": {"v": components.get("so2")},
                        "co": {"v": components.get("co")},
                    },
                    "source": "openweather"
                }
    except Exception as e:
        logger.error(f"OpenWeather fallback fail: {e}")
    return None


@lru_cache(maxsize=128)
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
        # Mask token in logs
        log_url = url.replace(API_TOKEN, "REDACTED")
        logger.info(f"External API Call: {log_url}")
        
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="City or location not found")
        elif response.status_code == 403:
            raise HTTPException(status_code=403, detail="Invalid API token")
        elif response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch air quality data")

        data = response.json()
        logger.debug(f"WAQI Response: {data}")

        if data.get("status") == "error":
            error_msg = data.get("data", "Invalid response from WAQI API")
            logger.error(f"WAQI API Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
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
    description="Fetch air quality index data for a specific city by name with geocoding and OWM fallback",
    tags=["Air Quality"],
)
def get_air_quality_by_city(city: str):
    """
    Get air quality data for a specific city.
    Now uses geocoding locally in backend to ensure we get coordinates and can use OWM fallback.
    """
    cache_key = f"city_v2:{city}"

    # Check cache first
    cached_data = get_cached_data(cache_key)
    if cached_data:
        return cached_data

    # Try to get coordinates first via Nominatim (OSM)
    try:
        g_url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}&limit=1"
        g_resp = requests.get(g_url, headers={'User-Agent': 'AirQualityApp/1.0'}, timeout=5)
        if g_resp.status_code == 200:
            g_data = g_resp.json()
            if g_data:
                lat = float(g_data[0]["lat"])
                lon = float(g_data[0]["lon"])
                # Use our coordinate-based logic which has the OWM fallback
                data = get_air_quality_by_coords(lat, lon)
                set_cached_data(cache_key, data)
                return data
    except Exception as e:
        logger.error(f"Geocoding failed for {city}: {e}")

    # Fallback to direct WAQI city search if geocoding fails
    url = f"{BASE_URL}{city}/?token={API_TOKEN}"
    data = fetch_aqi_data(url)
    set_cached_data(cache_key, data)
    return data


@app.get(
    "/api/air-quality-coords/{lat}/{lon}",
    summary="Get AQI by Coordinates",
    description="Fetch air quality index data for specific geographic coordinates using a more precise geosearch fallback",
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
    Uses geosearch to find the nearest active station and falls back to OpenWeatherMap for stale data (like Tehran).
    """
    cache_key = f"coords_v3:{lat}:{lon}"

    # Check cache first
    cached_data = get_cached_data(cache_key)
    if cached_data:
        logger.info(f"Returning cached data for coordinates: {lat}, {lon}")
        return cached_data

    # Fetch fresh WAQI data
    logger.info(f"Fetching fresh data for coordinates using geosearch: {lat}, {lon}")
    url = f"{BASE_URL}geo:{lat};{lon}/?token={API_TOKEN}"
    data = fetch_aqi_data(url)

    # CHECK FOR STALENESS (The "Tehran" problem)
    # If the data is from a different country/region (Kuwait for Tehran case)
    # or the value is missing, we fallback to OpenWeatherMap.
    stale = False
    
    # Check if the station name contains the original city/country we expect
    # or if the timestamp is old.
    if data and data.get("city") and data["city"].get("name"):
        station_name = data["city"]["name"].lower()
        # If we are in Tehran but data says Kuwait, it's a mismatch
        if "kuwait" in station_name and (lat > 32 and lat < 38) and (lon > 48 and lon < 53):
            stale = True
            logger.info("Station mismatch detected (Kuwait station for Iran coords). Switching to OpenWeather.")

    if data and data.get("time") and data["time"].get("s") and not stale:
        try:
            # Format: 2026-03-27 13:00:00 or similar
            data_time_str = data["time"]["s"][:10]
            data_time = datetime.strptime(data_time_str, "%Y-%m-%d")
            # If data is more than 2 days old, consider it stale
            if (datetime.now() - data_time).days > 2:
                stale = True
                logger.info(f"WAQI data is stale ({data_time_str}). Switching to OpenWeather.")
        except Exception as e:
            logger.error(f"Time parsing error: {e}")

    if stale or not data or data.get("aqi") == "-" or data.get("aqi") is None:
        ow_data = fetch_openweather_aqi(lat, lon)
        if ow_data:
            # Merge some attribution info to avoid breaking frontend
            ow_data["city"]["geo"] = [lat, lon]
            data = ow_data

    # Cache the result
    set_cached_data(cache_key, data)
    return data


@app.get("/api/data")
async def get_data():
    return {"message": "Hello from FastAPI!", "data": {"air_quality": 42, "weather": "Sunny"}}


# Mount the built frontend at root after API routes so /api endpoints take precedence.
app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 9091))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
