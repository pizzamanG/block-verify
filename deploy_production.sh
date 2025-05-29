#!/bin/bash

# BlockVerify Production Deployment Script
# Deploys BlockVerify to production environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
DEPLOY_ENV=${1:-production}
COMPOSE_FILE="docker-compose.production.yml"

log_info "🚀 Starting BlockVerify deployment (${DEPLOY_ENV})"

# Check prerequisites
log_info "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

log_success "Prerequisites check passed"

# Check environment file
ENV_FILE=".env.${DEPLOY_ENV}"
if [ ! -f "$ENV_FILE" ]; then
    log_error "Environment file $ENV_FILE not found!"
    log_info "Please copy env.production.example to $ENV_FILE and configure it"
    exit 1
fi

log_success "Environment file found: $ENV_FILE"

# Load environment variables
export $(cat $ENV_FILE | grep -v '^#' | xargs)

# Validate required environment variables
REQUIRED_VARS=(
    "DB_PASSWORD"
    "CHAIN_RPC_URL" 
    "PRIVATE_KEY"
    "BULLETIN_ADDRESS"
)

log_info "🔍 Validating environment variables..."

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log_error "Required environment variable $var is not set"
        exit 1
    fi
done

log_success "Environment validation passed"

# Create necessary directories
log_info "📁 Creating necessary directories..."

mkdir -p keys
mkdir -p logs
mkdir -p infra/nginx
mkdir -p infra/monitoring
mkdir -p infra/postgres

log_success "Directories created"

# Generate issuer key if it doesn't exist
ISSUER_KEY_PATH="keys/issuer_ed25519.jwk"
if [ ! -f "$ISSUER_KEY_PATH" ]; then
    log_warning "Issuer key not found. This should be generated securely."
    log_info "Please run 'python deploy.py' first to generate keys and deploy contracts"
    exit 1
fi

log_success "Issuer key found"

# Build and deploy with Docker Compose
log_info "🐳 Building and deploying with Docker..."

# Pull latest images
docker-compose -f $COMPOSE_FILE pull

# Build custom images
docker-compose -f $COMPOSE_FILE build --no-cache

# Create and start containers
log_info "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d

# Wait for services to be healthy
log_info "⏳ Waiting for services to be healthy..."

# Function to check service health
check_service_health() {
    local service=$1
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f $COMPOSE_FILE ps $service | grep -q "healthy\|Up"; then
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 10
        echo -n "."
    done
    
    return 1
}

# Check each service
services=("postgres" "blockverify-api" "demo-adult-site" "nginx")

for service in "${services[@]}"; do
    log_info "Checking $service health..."
    if check_service_health $service; then
        log_success "$service is healthy"
    else
        log_error "$service failed to become healthy"
        log_info "Checking logs..."
        docker-compose -f $COMPOSE_FILE logs $service
        exit 1
    fi
done

# Run database migrations
log_info "🗄️  Running database migrations..."
docker-compose -f $COMPOSE_FILE exec -T blockverify-api python -c "
from backend.app.db import engine
from backend.app.models import SQLModel
SQLModel.metadata.create_all(engine)
print('Database migration completed')
"

# Validate deployment
log_info "✅ Validating deployment..."

# Test API health endpoint
API_URL="http://localhost:8000/health"
if curl -f -s $API_URL > /dev/null; then
    log_success "BlockVerify API is responding"
else
    log_error "BlockVerify API is not responding"
    exit 1
fi

# Test demo site
DEMO_URL="http://localhost:3000/health"
if curl -f -s $DEMO_URL > /dev/null; then
    log_success "Demo site is responding" 
else
    log_error "Demo site is not responding"
    exit 1
fi

# Display deployment information
log_success "🎉 BlockVerify deployment completed successfully!"

echo ""
echo "📊 Deployment Summary:"
echo "======================"
echo "Environment: $DEPLOY_ENV"
echo "API URL: http://localhost:8000"
echo "Demo Site: http://localhost:3000"
echo "Dashboard: http://localhost:8000/dashboard.html"
echo "API Docs: http://localhost:8000/docs"
echo ""

echo "🔧 Management Commands:"
echo "======================"
echo "View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "Stop services: docker-compose -f $COMPOSE_FILE down"
echo "Restart services: docker-compose -f $COMPOSE_FILE restart"
echo "Update: ./deploy_production.sh $DEPLOY_ENV"
echo ""

echo "🌐 For AWS/Cloud Deployment:"
echo "============================"
echo "1. Set up domain: api.blockverify.com"
echo "2. Configure SSL certificates in infra/nginx/ssl/"
echo "3. Update CORS_ORIGINS in environment file"
echo "4. Set up monitoring alerts"
echo "5. Configure backup strategies"
echo ""

log_success "Deployment completed! 🚀" 