#!/bin/sh
# Start script for Railway deployment

# Use Railway's PORT or default to 8000
PORT="${PORT:-8000}"

echo "Starting BlockVerify API on port $PORT..."
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT" 