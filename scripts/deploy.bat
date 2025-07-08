@echo off
REM Over-Under Contests Deployment Script for Windows
REM Usage: scripts\deploy.bat [environment]

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

echo 🚀 Starting deployment for environment: %ENVIRONMENT%

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is required but not installed
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is required but not installed
    exit /b 1
)

echo 🔍 Running pre-deployment checks...

REM Check if .env file exists
if not exist ".env.%ENVIRONMENT%" (
    echo ⚠️  Warning: .env.%ENVIRONMENT% file not found
    echo    Creating from template...
    copy ".env.example" ".env.%ENVIRONMENT%"
    echo    Please edit .env.%ENVIRONMENT% with your configuration
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "nginx" mkdir nginx
if not exist "backups" mkdir backups

REM Build and deploy
echo 🏗️  Building application...
if "%ENVIRONMENT%"=="development" (
    docker-compose -f docker-compose.dev.yml build
) else (
    docker-compose -f docker-compose.yml build
)

echo 🔄 Stopping existing containers...
if "%ENVIRONMENT%"=="development" (
    docker-compose -f docker-compose.dev.yml down
) else (
    docker-compose -f docker-compose.yml down
)

echo 🚀 Starting new containers...
if "%ENVIRONMENT%"=="development" (
    docker-compose -f docker-compose.dev.yml up -d
) else (
    docker-compose -f docker-compose.yml up -d
)

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Run database migrations
echo 🗃️  Running database migrations...
if "%ENVIRONMENT%"=="development" (
    docker-compose -f docker-compose.dev.yml exec web flask db upgrade
) else (
    docker-compose -f docker-compose.yml exec web flask db upgrade
)

REM Health check
echo 🏥 Running health checks...
set /a attempt=1
set /a max_attempts=30

:healthcheck_loop
curl -f http://localhost:5000/health/ping >nul 2>&1
if not errorlevel 1 (
    echo ✅ Application is healthy!
    goto :post_deployment
)

if !attempt! geq !max_attempts! (
    echo ❌ Health check failed after !max_attempts! attempts
    echo 📋 Container logs:
    if "%ENVIRONMENT%"=="development" (
        docker-compose -f docker-compose.dev.yml logs web
    ) else (
        docker-compose -f docker-compose.yml logs web
    )
    exit /b 1
)

echo ⏳ Attempt !attempt!/!max_attempts! - waiting for application...
timeout /t 5 /nobreak >nul
set /a attempt+=1
goto :healthcheck_loop

:post_deployment
echo 🔧 Running post-deployment tasks...

REM Show deployment summary
echo.
echo 🎉 Deployment completed successfully!
echo 📊 Deployment Summary:
echo    Environment: %ENVIRONMENT%
echo    Application URL: http://localhost:5000
if "%ENVIRONMENT%"=="development" (
    echo    Database: http://localhost:5432
    echo    Redis: http://localhost:6379
    echo    MailHog: http://localhost:8025
)
echo    Health Check: http://localhost:5000/health
echo    Metrics: http://localhost:5000/metrics
echo.
echo 📋 Useful commands:
if "%ENVIRONMENT%"=="development" (
    echo    View logs: docker-compose -f docker-compose.dev.yml logs -f
    echo    Stop services: docker-compose -f docker-compose.dev.yml down
    echo    Restart: docker-compose -f docker-compose.dev.yml restart
) else (
    echo    View logs: docker-compose logs -f
    echo    Stop services: docker-compose down
    echo    Restart: docker-compose restart
)
echo.

endlocal
