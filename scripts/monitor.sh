#!/bin/bash

# Over-Under Contests Monitoring Script
# Usage: ./scripts/monitor.sh [action]

set -e

ACTION=${1:-status}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check service health
check_health() {
    local service_name=$1
    local health_url=$2
    
    if curl -f -s "$health_url" >/dev/null 2>&1; then
        print_status "$service_name is healthy"
        return 0
    else
        print_error "$service_name is unhealthy"
        return 1
    fi
}

# Function to get service status
get_service_status() {
    echo "🔍 Checking service status..."
    
    # Check if containers are running
    if docker-compose ps | grep -q "Up"; then
        print_status "Docker containers are running"
    else
        print_error "Some Docker containers are not running"
        docker-compose ps
    fi
    
    # Check application health
    check_health "Application" "http://localhost:5000/health/ping"
    
    # Check detailed health
    echo ""
    echo "📊 Detailed Health Check:"
    curl -s http://localhost:5000/health/detailed | python3 -m json.tool 2>/dev/null || print_warning "Could not get detailed health info"
    
    # Check metrics
    echo ""
    echo "📈 Application Metrics:"
    curl -s http://localhost:5000/metrics | python3 -m json.tool 2>/dev/null || print_warning "Could not get metrics"
}

# Function to show logs
show_logs() {
    local service=${2:-web}
    local lines=${3:-50}
    
    echo "📋 Showing last $lines lines of logs for $service:"
    docker-compose logs --tail="$lines" "$service"
}

# Function to backup database
backup_database() {
    echo "💾 Creating database backup..."
    
    local backup_dir="$PROJECT_DIR/backups"
    local backup_file="$backup_dir/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    mkdir -p "$backup_dir"
    
    # Get database URL from environment or docker-compose
    local db_url=$(docker-compose exec web printenv DATABASE_URL 2>/dev/null | tr -d '\r')
    
    if [ -n "$db_url" ]; then
        docker-compose exec db pg_dump "$db_url" > "$backup_file" 2>/dev/null || {
            print_error "Database backup failed"
            return 1
        }
        print_status "Database backup created: $backup_file"
        
        # Keep only last 7 backups
        find "$backup_dir" -name "backup_*.sql" -type f -mtime +7 -delete
        print_info "Old backups cleaned up (keeping last 7 days)"
    else
        print_error "Could not determine database URL"
        return 1
    fi
}

# Function to restart services
restart_services() {
    local service=${2:-all}
    
    echo "🔄 Restarting services..."
    
    if [ "$service" = "all" ]; then
        docker-compose restart
        print_status "All services restarted"
    else
        docker-compose restart "$service"
        print_status "Service $service restarted"
    fi
    
    # Wait and check health
    sleep 10
    check_health "Application" "http://localhost:5000/health/ping"
}

# Function to show resource usage
show_resources() {
    echo "💻 Resource Usage:"
    echo ""
    
    # Docker stats
    echo "🐳 Docker Container Stats:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    echo ""
    echo "💾 Disk Usage:"
    df -h | grep -E "(Filesystem|/dev/)"
    
    echo ""
    echo "🗃️  Database Size:"
    docker-compose exec db psql -U postgres -d overunders -c "SELECT pg_size_pretty(pg_database_size('overunders')) as database_size;" 2>/dev/null || print_warning "Could not get database size"
    
    echo ""
    echo "📁 Log Files:"
    if [ -d "$PROJECT_DIR/logs" ]; then
        du -sh "$PROJECT_DIR/logs"/* 2>/dev/null || print_info "No log files found"
    else
        print_info "Logs directory not found"
    fi
}

# Function to clean up old data
cleanup() {
    echo "🧹 Cleaning up old data..."
    
    # Clean old Docker images
    docker image prune -f
    print_status "Old Docker images cleaned"
    
    # Clean old logs (keep last 30 days)
    if [ -d "$PROJECT_DIR/logs" ]; then
        find "$PROJECT_DIR/logs" -name "*.log" -type f -mtime +30 -delete
        print_status "Old log files cleaned (keeping last 30 days)"
    fi
    
    # Clean old backups (keep last 30 days)
    if [ -d "$PROJECT_DIR/backups" ]; then
        find "$PROJECT_DIR/backups" -name "backup_*.sql" -type f -mtime +30 -delete
        print_status "Old backups cleaned (keeping last 30 days)"
    fi
    
    print_status "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Over-Under Contests Monitoring Script"
    echo ""
    echo "Usage: $0 [action] [options]"
    echo ""
    echo "Actions:"
    echo "  status          Show service status and health checks (default)"
    echo "  logs [service]  Show logs for service (default: web)"
    echo "  backup          Create database backup"
    echo "  restart [service] Restart services (default: all)"
    echo "  resources       Show resource usage"
    echo "  cleanup         Clean up old data"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 logs web"
    echo "  $0 backup"
    echo "  $0 restart web"
    echo "  $0 resources"
    echo "  $0 cleanup"
}

# Main script logic
case $ACTION in
    "status")
        get_service_status
        ;;
    "logs")
        show_logs "$@"
        ;;
    "backup")
        backup_database
        ;;
    "restart")
        restart_services "$@"
        ;;
    "resources")
        show_resources
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown action: $ACTION"
        echo ""
        show_help
        exit 1
        ;;
esac
