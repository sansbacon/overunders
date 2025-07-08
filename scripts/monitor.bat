@echo off
REM Over-Under Contests Monitoring Script for Windows
REM Usage: scripts\monitor.bat [action]

setlocal enabledelayedexpansion

set ACTION=%1
if "%ACTION%"=="" set ACTION=status

echo Over-Under Contests Monitoring Script

REM Main script logic
if "%ACTION%"=="status" goto :status
if "%ACTION%"=="logs" goto :logs
if "%ACTION%"=="backup" goto :backup
if "%ACTION%"=="restart" goto :restart
if "%ACTION%"=="resources" goto :resources
if "%ACTION%"=="cleanup" goto :cleanup
if "%ACTION%"=="help" goto :help
if "%ACTION%"=="-h" goto :help
if "%ACTION%"=="--help" goto :help

echo ❌ Unknown action: %ACTION%
echo.
goto :help

:status
echo 🔍 Checking service status...

REM Check if containers are running
docker-compose ps | findstr "Up" >nul
if not errorlevel 1 (
    echo ✅ Docker containers are running
) else (
    echo ❌ Some Docker containers are not running
    docker-compose ps
)

REM Check application health
curl -f -s http://localhost:5000/health/ping >nul 2>&1
if not errorlevel 1 (
    echo ✅ Application is healthy
) else (
    echo ❌ Application is unhealthy
)

echo.
echo 📊 Detailed Health Check:
curl -s http://localhost:5000/health/detailed 2>nul || echo ⚠️  Could not get detailed health info

echo.
echo 📈 Application Metrics:
curl -s http://localhost:5000/metrics 2>nul || echo ⚠️  Could not get metrics

goto :end

:logs
set SERVICE=%2
if "%SERVICE%"=="" set SERVICE=web
set LINES=%3
if "%LINES%"=="" set LINES=50

echo 📋 Showing last %LINES% lines of logs for %SERVICE%:
docker-compose logs --tail=%LINES% %SERVICE%
goto :end

:backup
echo 💾 Creating database backup...

if not exist "backups" mkdir backups

REM Create backup filename with timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "datestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

set BACKUP_FILE=backups\backup_%datestamp%.sql

REM Get database URL from container
for /f "delims=" %%i in ('docker-compose exec web printenv DATABASE_URL 2^>nul') do set DB_URL=%%i

if not "%DB_URL%"=="" (
    docker-compose exec db pg_dump "%DB_URL%" > "%BACKUP_FILE%" 2>nul
    if not errorlevel 1 (
        echo ✅ Database backup created: %BACKUP_FILE%
        
        REM Keep only last 7 backups
        forfiles /p backups /m backup_*.sql /d -7 /c "cmd /c del @path" 2>nul
        echo ℹ️  Old backups cleaned up (keeping last 7 days)
    ) else (
        echo ❌ Database backup failed
    )
) else (
    echo ❌ Could not determine database URL
)
goto :end

:restart
set SERVICE=%2
if "%SERVICE%"=="" set SERVICE=all

echo 🔄 Restarting services...

if "%SERVICE%"=="all" (
    docker-compose restart
    echo ✅ All services restarted
) else (
    docker-compose restart %SERVICE%
    echo ✅ Service %SERVICE% restarted
)

REM Wait and check health
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

curl -f -s http://localhost:5000/health/ping >nul 2>&1
if not errorlevel 1 (
    echo ✅ Application is healthy
) else (
    echo ❌ Application is unhealthy
)
goto :end

:resources
echo 💻 Resource Usage:
echo.

echo 🐳 Docker Container Stats:
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"

echo.
echo 💾 Disk Usage:
wmic logicaldisk get size,freespace,caption

echo.
echo 🗃️  Database Size:
docker-compose exec db psql -U postgres -d overunders -c "SELECT pg_size_pretty(pg_database_size('overunders')) as database_size;" 2>nul || echo ⚠️  Could not get database size

echo.
echo 📁 Log Files:
if exist "logs" (
    dir logs /s /-c | findstr /E ".log"
) else (
    echo ℹ️  Logs directory not found
)
goto :end

:cleanup
echo 🧹 Cleaning up old data...

REM Clean old Docker images
docker image prune -f
echo ✅ Old Docker images cleaned

REM Clean old logs (keep last 30 days)
if exist "logs" (
    forfiles /p logs /m *.log /d -30 /c "cmd /c del @path" 2>nul
    echo ✅ Old log files cleaned (keeping last 30 days)
)

REM Clean old backups (keep last 30 days)
if exist "backups" (
    forfiles /p backups /m backup_*.sql /d -30 /c "cmd /c del @path" 2>nul
    echo ✅ Old backups cleaned (keeping last 30 days)
)

echo ✅ Cleanup completed
goto :end

:help
echo Over-Under Contests Monitoring Script
echo.
echo Usage: %0 [action] [options]
echo.
echo Actions:
echo   status          Show service status and health checks (default)
echo   logs [service]  Show logs for service (default: web)
echo   backup          Create database backup
echo   restart [service] Restart services (default: all)
echo   resources       Show resource usage
echo   cleanup         Clean up old data
echo   help            Show this help message
echo.
echo Examples:
echo   %0 status
echo   %0 logs web
echo   %0 backup
echo   %0 restart web
echo   %0 resources
echo   %0 cleanup
goto :end

:end
endlocal
