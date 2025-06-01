FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy all application code
COPY backend/ backend/
COPY frontend/ frontend/
COPY client_sdk/ client_sdk/
COPY issuer_ed25519.jwk .

# Create landing page
COPY backend/app/landing.html backend/app/

# Set Python path
ENV PYTHONPATH=/app

# Expose port (Railway will override this)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Start command - using uvicorn directly
# Railway sets PORT env var, we use sh -c to expand it properly
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"] 