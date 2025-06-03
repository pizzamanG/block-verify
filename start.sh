#!/bin/bash

# Set default port if not provided
PORT=${PORT:-8000}

echo "🚀 Starting BlockVerify API on port $PORT"
echo "📍 Working directory: $(pwd)"
echo "📁 Contents: $(ls -la)"

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "❌ Backend directory not found!"
    exit 1
fi

echo "✅ Backend directory found"

# Set Python path to include current directory
export PYTHONPATH=/app:$PYTHONPATH

# Start the uvicorn server with more verbose logging
echo "🎯 Starting uvicorn server..."
exec uvicorn backend.app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info \
    --access-log 