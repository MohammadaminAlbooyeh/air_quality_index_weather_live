# Multi-stage build: build React frontend, then create a Python image that serves the built assets

# --- Builder: build the frontend (Vite + React) ---
FROM node:18-alpine AS node-builder
WORKDIR /build

# Copy only the frontend app and install/build
# Use `frontend/` (matches local dev folder) so Docker builds the same app
COPY frontend/package.json frontend/package-lock.json* ./frontend/
COPY frontend/ ./frontend/
WORKDIR /build/frontend

# Install and build. Use legacy-peer-deps to match local dev installs where needed.
RUN npm install --legacy-peer-deps --no-audit --no-fund && npm run build


# --- Final image: Python runtime serving FastAPI and static files ---
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from the node builder into the location FastAPI expects
RUN mkdir -p /app/backend/frontend
COPY --from=node-builder /build/frontend/dist/ /app/backend/frontend/

# Expose port used by Uvicorn
EXPOSE 8000

# Start the FastAPI app (serves static files from backend/frontend under /static)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
