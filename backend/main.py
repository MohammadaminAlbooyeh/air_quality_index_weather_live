import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# Allow CORS for frontend to access the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI()

# compute project base dir (repo root)
import pathlib
BASE_DIR = pathlib.Path(__file__).parent.parent.resolve()


API_TOKEN = "5b530e5c4347dfd343d98578efe34d8ea618c6ec"  # Replace with your WAQI API token
BASE_URL = "https://api.waqi.info/feed/"

# keep an API root under /api so that static mounting doesn't conflict
@app.get("/api")
def read_root():
    return {"message": "Welcome to the Air Quality Index API!"}

@app.get("/api/air-quality")
def get_air_quality():
    # Placeholder for air quality data fetching logic
    return {"data": "Air quality data will be here."}

@app.get("/api/air-quality/{city}")
def get_air_quality(city: str):
    url = f"{BASE_URL}{city}/?token={API_TOKEN}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch air quality data")

    data = response.json()
    if data.get("status") != "ok":
        raise HTTPException(status_code=400, detail="Invalid response from WAQI API")

    return data.get("data", {})

@app.get("/api/air-quality-coords/{lat}/{lon}")
def get_air_quality_by_coords(lat: float, lon: float):
    """Get air quality data for specific coordinates"""
    url = f"{BASE_URL}geo:{lat};{lon}/?token={API_TOKEN}"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch air quality data")

    data = response.json()
    if data.get("status") != "ok":
        raise HTTPException(status_code=400, detail="Invalid response from WAQI API")

    return data.get("data", {})

@app.get("/api/data")
async def get_data():
    return {"message": "Hello from FastAPI!", "data": {"air_quality": 42, "weather": "Sunny"}}


# Mount the built frontend at root after API routes so /api endpoints take precedence.
app.mount("/", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")