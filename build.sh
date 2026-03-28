#!/usr/bin/env bash

# Exit on error
set -o errexit

# Install backend dependencies via poetry
# Since we are in the root, it will use the root pyproject.toml
poetry install

# Build frontend
cd frontend
npm install --legacy-peer-deps
npm run build

# Go back to root
cd ..

# Ensure the backend knows where to find the built frontend if needed
# (Optional: some projects copy the dist to a specific folder)
