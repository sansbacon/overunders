"""Health check and monitoring endpoints."""
from flask import Blueprint, jsonify, current_app
from app.utils.monitoring import HealthChecker, safe_execute
import time

health = Blueprint('health', __name__)


@health.route('/health')
def health_check():
    """Basic health check endpoint."""
    start_time = time.time()
    
    checks = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'environment': current_app.config.get('FLASK_ENV', 'production')
    }
    
    # Database check
    db_check = safe_execute(HealthChecker.check_database, {'status': 'error'})
    checks['database'] = db_check
    
    # Email service check
    email_check = safe_execute(HealthChecker.check_email, {'status': 'error'})
    checks['email'] = email_check
    
    # Overall status
    if db_check.get('status') != 'healthy':
        checks['status'] = 'unhealthy'
    
    checks['response_time'] = round(time.time() - start_time, 3)
    
    status_code = 200 if checks['status'] == 'healthy' else 503
    return jsonify(checks), status_code


@health.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with system information."""
    if not current_app.config.get('HEALTH_CHECK_ENABLED', True):
        return jsonify({'error': 'Health checks disabled'}), 404
    
    start_time = time.time()
    
    checks = {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'environment': current_app.config.get('FLASK_ENV', 'production'),
        'checks': {}
    }
    
    # Database check
    checks['checks']['database'] = safe_execute(HealthChecker.check_database, {'status': 'error'})
    
    # Email service check
    checks['checks']['email'] = safe_execute(HealthChecker.check_email, {'status': 'error'})
    
    # System information
    checks['checks']['system'] = safe_execute(HealthChecker.get_system_info, {'status': 'error'})
    
    # Application metrics
    checks['checks']['application'] = {
        'debug_mode': current_app.debug,
        'testing_mode': current_app.testing,
        'config_loaded': bool(current_app.config),
        'blueprints': list(current_app.blueprints.keys())
    }
    
    # Check if any critical services are down
    critical_checks = ['database']
    for check_name in critical_checks:
        if checks['checks'].get(check_name, {}).get('status') not in ['healthy', 'configured']:
            checks['status'] = 'unhealthy'
    
    checks['response_time'] = round(time.time() - start_time, 3)
    
    status_code = 200 if checks['status'] == 'healthy' else 503
    return jsonify(checks), status_code


@health.route('/health/ready')
def readiness_check():
    """Kubernetes-style readiness check."""
    # Check if the application is ready to serve traffic
    checks = {
        'ready': True,
        'timestamp': time.time()
    }
    
    # Database connectivity check
    db_check = safe_execute(HealthChecker.check_database, {'status': 'error'})
    if db_check.get('status') != 'healthy':
        checks['ready'] = False
        checks['reason'] = 'Database not available'
    
    status_code = 200 if checks['ready'] else 503
    return jsonify(checks), status_code


@health.route('/health/live')
def liveness_check():
    """Kubernetes-style liveness check."""
    # Simple check to see if the application is alive
    return jsonify({
        'alive': True,
        'timestamp': time.time()
    }), 200


@health.route('/metrics')
def metrics():
    """Basic application metrics endpoint."""
    try:
        from app import db
        from app.models import User, Contest, Entry
        
        metrics = {
            'timestamp': time.time(),
            'database': {
                'users_total': safe_execute(lambda: User.query.count(), 0),
                'contests_total': safe_execute(lambda: Contest.query.count(), 0),
                'entries_total': safe_execute(lambda: Entry.query.count(), 0),
                'active_contests': safe_execute(
                    lambda: Contest.query.filter_by(is_active=True).count(), 0
                )
            },
            'application': {
                'debug_mode': current_app.debug,
                'environment': current_app.config.get('FLASK_ENV', 'production')
            }
        }
        
        return jsonify(metrics)
    except Exception as e:
        current_app.logger.error(f'Error generating metrics: {e}')
        return jsonify({'error': 'Unable to generate metrics'}), 500


@health.route('/health/ping')
def ping():
    """Simple ping endpoint for load balancers."""
    return 'pong', 200
