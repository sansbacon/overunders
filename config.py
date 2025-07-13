"""Application configuration module."""
import os
import logging
from datetime import timedelta


class Config:
    """Base configuration class."""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() in ['true', 'on', '1']
    
    # Error monitoring
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    ENABLE_ERROR_MONITORING = os.environ.get('ENABLE_ERROR_MONITORING', 'false').lower() in ['true', 'on', '1']
    
    # Health check configuration
    HEALTH_CHECK_ENABLED = True
    DATABASE_HEALTH_CHECK_TIMEOUT = 5  # seconds
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL') or 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # Performance monitoring
    ENABLE_PROFILING = os.environ.get('ENABLE_PROFILING', 'false').lower() in ['true', 'on', '1']
    SLOW_QUERY_THRESHOLD = float(os.environ.get('SLOW_QUERY_THRESHOLD', '0.5'))
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # SendGrid API configuration
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    USE_SENDGRID_API = os.environ.get('USE_SENDGRID_API', 'false').lower() in ['true', 'on', '1']
    
    # Token expiration
    LOGIN_TOKEN_EXPIRATION = timedelta(minutes=30)
    
    # Pagination
    CONTESTS_PER_PAGE = 10
    ENTRIES_PER_PAGE = 20
    
    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
    
    # OpenAI configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Content moderation configuration
    AI_MODERATION_ENABLED = os.environ.get('AI_MODERATION_ENABLED', 'false').lower() in ['true', 'on', '1']
    CONTENT_MODERATION_LOG_ENABLED = os.environ.get('CONTENT_MODERATION_LOG_ENABLED', 'true').lower() in ['true', 'on', '1']
    AUTO_MODERATE_NEW_CONTENT = os.environ.get('AUTO_MODERATE_NEW_CONTENT', 'true').lower() in ['true', 'on', '1']
    MODERATE_AI_GENERATED_CONTENT = os.environ.get('MODERATE_AI_GENERATED_CONTENT', 'true').lower() in ['true', 'on', '1']
    
    # Verification requirements configuration
    REQUIRE_VERIFICATION_FOR_CONTESTS = os.environ.get('REQUIRE_VERIFICATION_FOR_CONTESTS', 'false').lower() in ['true', 'on', '1']
    REQUIRE_VERIFICATION_FOR_LEAGUES = os.environ.get('REQUIRE_VERIFICATION_FOR_LEAGUES', 'false').lower() in ['true', 'on', '1']
    ALLOW_UNVERIFIED_PARTICIPATION = os.environ.get('ALLOW_UNVERIFIED_PARTICIPATION', 'true').lower() in ['true', 'on', '1']
    MINIMUM_VERIFICATION_LEVEL_CONTESTS = os.environ.get('MINIMUM_VERIFICATION_LEVEL_CONTESTS', 'basic')
    MINIMUM_VERIFICATION_LEVEL_LEAGUES = os.environ.get('MINIMUM_VERIFICATION_LEVEL_LEAGUES', 'basic')


class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///over_under_dev.db'
    
    # Only set SERVER_NAME for local development if explicitly provided
    if os.environ.get('SERVER_NAME'):
        SERVER_NAME = os.environ.get('SERVER_NAME')
        PREFERRED_URL_SCHEME = 'http'


class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///over_under.db'
    
    # Handle Heroku postgres URL format
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Use HTTPS for production
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': ProductionConfig if os.environ.get('DATABASE_URL') else DevelopmentConfig
}
