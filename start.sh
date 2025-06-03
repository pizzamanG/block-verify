#!/bin/bash

# Set default port if not provided
PORT=${PORT:-8000}

echo "🚀 Starting BlockVerify API on port $PORT"

# Start the uvicorn server
exec uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT" 