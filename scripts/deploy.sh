#!/bin/bash

# Over-Under Contests Deployment Script
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting deployment for environment: $ENVIRONMENT"

# Load environment variables
if [ -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
    echo "📋 Loading environment variables from .env.$ENVIRONMENT"
    export $(cat "$PROJECT_DIR/.env.$ENVIRONMENT" | grep -v '^#' | xargs)
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check required tools
echo "🔍 Checking required tools..."
if ! command_exists docker; then
    echo "❌ Docker is required but not installed"
    exit 1
fi

if ! command_exists docker-compose; then
    echo "❌ Docker Compose is required but not installed"
    exit 1
fi

# Pre-deployment checks
echo "🔍 Running pre-deployment checks..."

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
    echo "⚠️  Warning: .env.$ENVIRONMENT file not found"
    echo "   Creating from template..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env.$ENVIRONMENT"
    echo "   Please edit .env.$ENVIRONMENT with your configuration"
fi

# Check if required environment variables are set
required_vars=("SECRET_KEY" "DATABASE_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set"
        exit 1
    fi
done

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$PROJECT_DIR/nginx"
mkdir -p "$PROJECT_DIR/backups"

# Backup database (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "💾 Creating database backup..."
    BACKUP_FILE="$PROJECT_DIR/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    if [ -n "$DATABASE_URL" ]; then
        pg_dump "$DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null || echo "⚠️  Database backup failed (database may not exist yet)"
    fi
fi

# Build and deploy
echo "🏗️  Building application..."
if [ "$ENVIRONMENT" = "development" ]; then
    docker-compose -f "$PROJECT_DIR/docker-compose.dev.yml" build
else
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" build
fi

echo "🔄 Stopping existing containers..."
if [ "$ENVIRONMENT" = "development" ]; then
    docker-compose -f "$PROJECT_DIR/docker-compose.dev.yml" down
else
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" down
fi

echo "🚀 Starting new containers..."
if [ "$ENVIRONMENT" = "development" ]; then
    docker-compose -f "$PROJECT_DIR/docker-compose.dev.yml" up -d
else
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" up -d
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Run database migrations
echo "🗃️  Running database migrations..."
if [ "$ENVIRONMENT" = "development" ]; then
    docker-compose -f "$PROJECT_DIR/docker-compose.dev.yml" exec web flask db upgrade
else
    docker-compose -f "$PROJECT_DIR/docker-compose.yml" exec web flask db upgrade
fi

# Health check
echo "🏥 Running health checks..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:5000/health/ping >/dev/null 2>&1; then
        echo "✅ Application is healthy!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Health check failed after $max_attempts attempts"
        echo "📋 Container logs:"
        if [ "$ENVIRONMENT" = "development" ]; then
            docker-compose -f "$PROJECT_DIR/docker-compose.dev.yml" logs web
        else
            docker-compose -f "$PROJECT_DIR/docker-compose.yml" logs web
        fi
        exit 1
    fi
    
    echo "⏳ Attempt $attempt/$max_attempts - waiting for application..."
    sleep 5
    ((attempt++))
done

# Post-deployment tasks
echo "🔧 Running post-deployment tasks..."

# Create admin user if it doesn't exist (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "👤 Checking admin user..."
    if [ "$ENVIRONMENT" = "development" ]; then
        docker-compose -f "$PROJECT_DIR/docker-compose.dev.yml" exec web python create_admin.py || echo "⚠️  Admin user creation skipped"
    else
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" exec web python create_admin.py || echo "⚠️  Admin user creation skipped"
    fi
fi

# Show deployment summary
echo ""
echo "🎉 Deployment completed successfully!"
echo "📊 Deployment Summary:"
echo "   Environment: $ENVIRONMENT"
echo "   Application URL: http://localhost:5000"
if [ "$ENVIRONMENT" = "development" ]; then
    echo "   Database: http://localhost:5432"
    echo "   Redis: http://localhost:6379"
    echo "   MailHog: http://localhost:8025"
fi
echo "   Health Check: http://localhost:5000/health"
echo "   Metrics: http://localhost:5000/metrics"
echo ""
echo "📋 Useful commands:"
if [ "$ENVIRONMENT" = "development" ]; then
    echo "   View logs: docker-compose -f docker-compose.dev.yml logs -f"
    echo "   Stop services: docker-compose -f docker-compose.dev.yml down"
    echo "   Restart: docker-compose -f docker-compose.dev.yml restart"
else
    echo "   View logs: docker-compose logs -f"
    echo "   Stop services: docker-compose down"
    echo "   Restart: docker-compose restart"
fi
echo ""
