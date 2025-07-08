"""Monitoring and error handling utilities."""
import logging
import time
import traceback
from functools import wraps
from flask import current_app, request, g
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3


class ErrorHandler:
    """Centralized error handling and logging."""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handling for the Flask app."""
        self.app = app
        
        # Configure logging
        self._configure_logging()
        
        # Set up error handlers
        self._register_error_handlers()
        
        # Initialize Sentry if configured
        self._init_sentry()
        
        # Set up database query monitoring
        self._setup_query_monitoring()
        
        # Set up request monitoring
        self._setup_request_monitoring()
    
    def _configure_logging(self):
        """Configure application logging."""
        if not self.app.debug and not self.app.testing:
            # Production logging setup
            if self.app.config.get('LOG_TO_STDOUT'):
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(getattr(logging, self.app.config['LOG_LEVEL']))
                formatter = logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                )
                stream_handler.setFormatter(formatter)
                self.app.logger.addHandler(stream_handler)
            else:
                # File logging
                import os
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                
                file_handler = logging.FileHandler('logs/overunders.log')
                file_handler.setLevel(getattr(logging, self.app.config['LOG_LEVEL']))
                formatter = logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                )
                file_handler.setFormatter(formatter)
                self.app.logger.addHandler(file_handler)
            
            self.app.logger.setLevel(getattr(logging, self.app.config['LOG_LEVEL']))
            self.app.logger.info('Over-Under Contests startup')
    
    def _init_sentry(self):
        """Initialize Sentry error monitoring if configured."""
        if self.app.config.get('ENABLE_ERROR_MONITORING') and self.app.config.get('SENTRY_DSN'):
            try:
                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration
                from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
                
                sentry_sdk.init(
                    dsn=self.app.config['SENTRY_DSN'],
                    integrations=[
                        FlaskIntegration(),
                        SqlalchemyIntegration(),
                    ],
                    traces_sample_rate=0.1,
                    environment=self.app.config.get('FLASK_ENV', 'production')
                )
                self.app.logger.info('Sentry error monitoring initialized')
            except ImportError:
                self.app.logger.warning('Sentry SDK not installed, error monitoring disabled')
    
    def _register_error_handlers(self):
        """Register custom error handlers."""
        
        @self.app.errorhandler(404)
        def not_found_error(error):
            self.app.logger.warning(f'404 error: {request.url}')
            return self._render_error_page(404, 'Page Not Found', 
                                         'The page you are looking for does not exist.')
        
        @self.app.errorhandler(403)
        def forbidden_error(error):
            self.app.logger.warning(f'403 error: {request.url} - User: {getattr(g, "current_user", "Anonymous")}')
            return self._render_error_page(403, 'Access Forbidden', 
                                         'You do not have permission to access this resource.')
        
        @self.app.errorhandler(500)
        def internal_error(error):
            from app import db
            db.session.rollback()
            self.app.logger.error(f'500 error: {request.url}', exc_info=True)
            return self._render_error_page(500, 'Internal Server Error', 
                                         'An unexpected error occurred. Please try again later.')
        
        @self.app.errorhandler(429)
        def ratelimit_handler(error):
            self.app.logger.warning(f'Rate limit exceeded: {request.url} - IP: {request.remote_addr}')
            return self._render_error_page(429, 'Too Many Requests', 
                                         'You have made too many requests. Please try again later.')
    
    def _render_error_page(self, status_code, title, message):
        """Render error page with consistent styling."""
        from flask import render_template
        try:
            return render_template(f'errors/{status_code}.html', 
                                 title=title, message=message), status_code
        except:
            # Fallback if template doesn't exist
            return f'''
            <!DOCTYPE html>
            <html>
            <head><title>{title}</title></head>
            <body>
                <h1>{title}</h1>
                <p>{message}</p>
                <a href="/">Return to Home</a>
            </body>
            </html>
            ''', status_code
    
    def _setup_query_monitoring(self):
        """Set up database query performance monitoring."""
        if self.app.config.get('SLOW_QUERY_THRESHOLD'):
            @event.listens_for(Engine, "before_cursor_execute")
            def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                context._query_start_time = time.time()
            
            @event.listens_for(Engine, "after_cursor_execute")
            def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                total = time.time() - context._query_start_time
                if total > self.app.config['SLOW_QUERY_THRESHOLD']:
                    self.app.logger.warning(
                        f'Slow query: {total:.2f}s - {statement[:100]}...'
                    )
    
    def _setup_request_monitoring(self):
        """Set up request performance monitoring."""
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
        
        @self.app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                total_time = time.time() - g.start_time
                if total_time > 2.0:  # Log slow requests
                    self.app.logger.warning(
                        f'Slow request: {total_time:.2f}s - {request.method} {request.path}'
                    )
            return response


def log_error(error, context=None):
    """Log an error with context information."""
    error_info = {
        'error': str(error),
        'type': type(error).__name__,
        'traceback': traceback.format_exc(),
        'context': context or {},
        'request_info': {
            'url': request.url if request else None,
            'method': request.method if request else None,
            'remote_addr': request.remote_addr if request else None,
            'user_agent': str(request.user_agent) if request else None,
        }
    }
    
    current_app.logger.error(f'Application error: {error_info}')
    return error_info


def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            if execution_time > 1.0:  # Log slow functions
                current_app.logger.warning(
                    f'Slow function: {func.__name__} took {execution_time:.2f}s'
                )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            log_error(e, {
                'function': func.__name__,
                'execution_time': execution_time,
                'args': str(args)[:100],
                'kwargs': str(kwargs)[:100]
            })
            raise
    return wrapper


def safe_execute(func, default=None, log_errors=True):
    """Safely execute a function with error handling."""
    try:
        return func()
    except Exception as e:
        if log_errors:
            log_error(e, {'function': getattr(func, '__name__', 'anonymous')})
        return default


class HealthChecker:
    """Application health checking utilities."""
    
    @staticmethod
    def check_database():
        """Check database connectivity."""
        try:
            from app import db
            from sqlalchemy import text
            
            # Simple query to test database
            result = db.session.execute(text('SELECT 1')).scalar()
            return {'status': 'healthy', 'response_time': 0.1}
        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}
    
    @staticmethod
    def check_email():
        """Check email service connectivity."""
        try:
            from app import mail
            # This is a basic check - in production you might want to send a test email
            if current_app.config.get('MAIL_SERVER'):
                return {'status': 'configured'}
            else:
                return {'status': 'not_configured'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def get_system_info():
        """Get basic system information."""
        import psutil
        import platform
        
        try:
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent
            }
        except ImportError:
            return {'status': 'psutil not available'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# Global error handler instance
error_handler = ErrorHandler()
