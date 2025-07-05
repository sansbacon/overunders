"""Flask application factory."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()

# OAuth will be initialized in create_app
oauth = None
google = None


def create_app(config_name=None):
    """Create and configure Flask application.
    
    Args:
        config_name (str): Configuration name ('development', 'production', 'testing')
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_CONFIG') or 'default'
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Initialize OAuth if Google credentials are provided
    global oauth, google
    if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
        from app.utils.oauth import init_oauth
        oauth, google = init_oauth(app)
    
    # Register blueprints
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes.contests import contests as contests_blueprint
    app.register_blueprint(contests_blueprint, url_prefix='/contests')
    
    from app.routes.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # Register template filters
    from app.utils.timezone import convert_from_utc
    
    @app.template_filter('to_central_time')
    def to_central_time_filter(utc_datetime):
        """Convert UTC datetime to Central Time for templates."""
        return convert_from_utc(utc_datetime, 'America/Chicago')
    
    @app.template_filter('strftime')
    def strftime_filter(datetime_obj, format_str='%Y-%m-%d %H:%M'):
        """Format datetime object using strftime."""
        if datetime_obj is None:
            return 'Not set'
        return datetime_obj.strftime(format_str)
    
    return app
