# Air Quality Index Weather Live

This project provides live Air Quality Index (AQI) and weather information with a React + Vite frontend and a FastAPI backend.

## Development

- Backend (Python - virtualenv):

```bash
# create and activate virtualenv (macOS/Linux)
python -m venv .venv
source .venv/bin/activate

# install Python deps
pip install -r requirements.txt

# run backend (uvicorn)
./.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

- Frontend (Vite + React):

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

## Notes
- The backend mounts the built frontend into `backend/frontend` and serves static files at root.
- The project expects an API token for WAQI inside `backend/main.py` (replace `API_TOKEN` with a valid token).

If you want, I can commit these README changes and create a small release/build script.