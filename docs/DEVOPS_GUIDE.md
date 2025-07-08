# DevOps and Deployment Guide

This guide covers error handling, monitoring, and deployment best practices for the Over-Under Contests application.

## 🚨 Error Handling and Monitoring

### Error Monitoring System

The application includes a comprehensive error monitoring system with the following features:

#### 1. Centralized Error Handling
- **Custom error handlers** for 404, 403, 500, and 429 errors
- **Automatic database rollback** on 500 errors
- **Structured error logging** with context information
- **Fallback error pages** when templates are unavailable

#### 2. Performance Monitoring
- **Slow query detection** (configurable threshold)
- **Request performance tracking** (logs requests > 2 seconds)
- **Function performance monitoring** with decorators
- **Database query timing** with SQLAlchemy event listeners

#### 3. Health Check Endpoints

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `/health/ping` | Simple liveness check | `pong` |
| `/health` | Basic health status | JSON with database/email status |
| `/health/detailed` | Comprehensive health check | JSON with system info |
| `/health/ready` | Kubernetes readiness probe | JSON ready status |
| `/health/live` | Kubernetes liveness probe | JSON alive status |
| `/metrics` | Application metrics | JSON with user/contest counts |

#### 4. Logging Configuration

```python
# Environment Variables for Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_TO_STDOUT=true               # For containerized environments
ENABLE_ERROR_MONITORING=true     # Enable Sentry integration
SENTRY_DSN=your_sentry_dsn       # Sentry error tracking
```

#### 5. Sentry Integration

When configured, the application automatically sends errors to Sentry with:
- **Flask integration** for request context
- **SQLAlchemy integration** for database errors
- **Performance monitoring** with 10% sample rate
- **Environment tagging** for proper error categorization

### Error Handling Best Practices

#### 1. Using the Monitoring Decorators

```python
from app.utils.monitoring import monitor_performance, log_error, safe_execute

@monitor_performance
def slow_function():
    # Function will be logged if it takes > 1 second
    pass

# Safe execution with error handling
result = safe_execute(lambda: risky_operation(), default="fallback_value")
```

#### 2. Custom Error Logging

```python
from app.utils.monitoring import log_error

try:
    risky_operation()
except Exception as e:
    log_error(e, context={'user_id': user.id, 'operation': 'contest_creation'})
    raise
```

## 🐳 Docker Deployment

### Container Architecture

The application uses a multi-stage Docker build:

1. **Builder stage**: Installs dependencies and creates virtual environment
2. **Production stage**: Copies only necessary files for minimal image size

### Docker Compose Configurations

#### Production (`docker-compose.yml`)
- **Web application** with Gunicorn
- **PostgreSQL database** with health checks
- **Redis** for caching and rate limiting
- **Nginx** reverse proxy (optional)
- **Persistent volumes** for data

#### Development (`docker-compose.dev.yml`)
- **Flask development server** with hot reload
- **MailHog** for email testing
- **Volume mounting** for live code changes
- **Debug logging** enabled

### Deployment Commands

#### Quick Start (Development)
```bash
# Windows
scripts\deploy.bat development

# Linux/Mac
./scripts/deploy.sh development
```

#### Production Deployment
```bash
# Windows
scripts\deploy.bat production

# Linux/Mac
./scripts/deploy.sh production
```

### Environment Configuration

Create environment-specific files:

#### `.env.development`
```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key
DATABASE_URL=postgresql://postgres:password@localhost:5432/overunders_dev
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=true
```

#### `.env.production`
```env
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=your-production-database-url
SENTRY_DSN=your-sentry-dsn
ENABLE_ERROR_MONITORING=true
LOG_LEVEL=INFO
LOG_TO_STDOUT=true
```

## 📊 Monitoring and Maintenance

### Health Monitoring

#### Automated Health Checks
```bash
# Check application status
curl http://localhost:5000/health

# Detailed system information
curl http://localhost:5000/health/detailed

# Application metrics
curl http://localhost:5000/metrics
```

#### Monitoring Script Usage

```bash
# Windows
scripts\monitor.bat status
scripts\monitor.bat logs web
scripts\monitor.bat backup
scripts\monitor.bat resources

# Linux/Mac
./scripts/monitor.sh status
./scripts/monitor.sh logs web
./scripts/monitor.sh backup
./scripts/monitor.sh resources
```

### Database Backup Strategy

#### Automated Backups
- **Daily backups** during deployment
- **Retention policy**: 7 days for frequent backups, 30 days for weekly
- **Backup verification** with restore testing

#### Manual Backup
```bash
# Create immediate backup
./scripts/monitor.sh backup

# Restore from backup
docker-compose exec db psql -U postgres -d overunders < backups/backup_20240107_120000.sql
```

### Log Management

#### Log Locations
- **Application logs**: `logs/overunders.log`
- **Nginx logs**: `logs/nginx/`
- **Container logs**: `docker-compose logs`

#### Log Rotation
- **Automatic cleanup** of logs older than 30 days
- **Size-based rotation** for high-traffic environments
- **Structured logging** with JSON format for production

## 🔧 Performance Optimization

### Database Optimization

#### Query Performance
- **Slow query logging** (threshold: 0.5 seconds)
- **Database connection pooling** with SQLAlchemy
- **Index optimization** for frequently queried fields

#### Monitoring Queries
```python
# Queries slower than threshold are automatically logged
# Check logs for: "Slow query: 1.23s - SELECT ..."
```

### Caching Strategy

#### Redis Integration
- **Session storage** for user sessions
- **Rate limiting** storage
- **Application caching** for expensive operations

#### Cache Configuration
```python
# Environment variables
REDIS_URL=redis://localhost:6379/0
RATELIMIT_STORAGE_URL=redis://localhost:6379/1
```

### Resource Monitoring

#### System Metrics
- **CPU usage** monitoring
- **Memory consumption** tracking
- **Disk space** alerts
- **Database size** monitoring

#### Container Resource Limits
```yaml
# docker-compose.yml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: ./scripts/deploy.sh production
```

### Deployment Checklist

#### Pre-deployment
- [ ] Run tests locally
- [ ] Check environment variables
- [ ] Verify database migrations
- [ ] Review security configurations

#### Post-deployment
- [ ] Verify health checks pass
- [ ] Check application logs
- [ ] Test critical user flows
- [ ] Monitor error rates

## 🔒 Security Best Practices

### Container Security

#### Image Security
- **Non-root user** in containers
- **Minimal base images** (Alpine Linux)
- **Regular security updates**
- **Vulnerability scanning**

#### Runtime Security
- **Read-only file systems** where possible
- **Resource limits** to prevent DoS
- **Network segmentation** with Docker networks
- **Secrets management** with environment variables

### Application Security

#### Error Handling
- **No sensitive data** in error messages
- **Proper error logging** without exposing internals
- **Rate limiting** on all endpoints
- **CSRF protection** enabled

#### Monitoring Security
- **Failed login attempts** logging
- **Suspicious activity** detection
- **Security headers** enforcement
- **SSL/TLS** termination at load balancer

## 📈 Scaling Considerations

### Horizontal Scaling

#### Load Balancing
- **Multiple application instances** behind load balancer
- **Session affinity** or shared session storage
- **Health check** integration with load balancer

#### Database Scaling
- **Read replicas** for read-heavy workloads
- **Connection pooling** optimization
- **Query optimization** and indexing

### Monitoring at Scale

#### Metrics Collection
- **Prometheus** integration for metrics
- **Grafana** dashboards for visualization
- **Alert manager** for notifications

#### Log Aggregation
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Centralized logging** from all containers
- **Log parsing** and alerting rules

## 🛠 Troubleshooting Guide

### Common Issues

#### Application Won't Start
1. Check environment variables
2. Verify database connectivity
3. Review application logs
4. Check port conflicts

#### Database Connection Issues
1. Verify database is running
2. Check connection string format
3. Verify network connectivity
4. Check database user permissions

#### Performance Issues
1. Check slow query logs
2. Monitor resource usage
3. Review application metrics
4. Analyze request patterns

### Debug Commands

```bash
# Check container status
docker-compose ps

# View application logs
docker-compose logs -f web

# Access application container
docker-compose exec web bash

# Check database connectivity
docker-compose exec web python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"

# Monitor resource usage
docker stats

# Check health endpoints
curl -v http://localhost:5000/health/detailed
```

This comprehensive DevOps setup provides robust error handling, monitoring, and deployment capabilities for the Over-Under Contests application.
