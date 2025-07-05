"""OAuth utility functions for Google authentication."""
import json
import requests
from authlib.integrations.flask_client import OAuth
from flask import current_app, url_for
from app import db
from app.models import User


def init_oauth(app):
    """Initialize OAuth with the Flask app.
    
    Args:
        app: Flask application instance
        
    Returns:
        OAuth: Configured OAuth instance
    """
    oauth = OAuth(app)
    
    google = oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    return oauth, google


def get_google_provider_cfg():
    """Get Google's provider configuration.
    
    Returns:
        dict: Google's OpenID Connect configuration
    """
    return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()


def create_or_update_google_user(google_user_info):
    """Create or update user from Google OAuth information.
    
    Args:
        google_user_info (dict): User information from Google
        
    Returns:
        User: Created or updated user instance
    """
    google_id = google_user_info['sub']
    email = google_user_info['email']
    name = google_user_info.get('name', '')
    picture = google_user_info.get('picture', '')
    
    # Check if user exists by Google ID
    user = User.query.filter_by(google_id=google_id).first()
    
    if user:
        # Update existing user's Google information
        user.google_email = email
        user.google_name = name
        user.google_picture = picture
        user.last_login = db.func.now()
        
        # Update email if it changed and doesn't conflict
        if user.email != email:
            existing_email_user = User.query.filter_by(email=email).first()
            if not existing_email_user:
                user.email = email
        
        db.session.commit()
        return user
    
    # Check if user exists by email
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Link existing email user to Google account
        user.google_id = google_id
        user.google_email = email
        user.google_name = name
        user.google_picture = picture
        user.auth_provider = 'google'
        user.last_login = db.func.now()
        
        # Update name fields if they're empty
        if not user.first_name and not user.last_name and name:
            name_parts = name.split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
        
        db.session.commit()
        return user
    
    # Create new user
    name_parts = name.split(' ', 1) if name else ['', '']
    first_name = name_parts[0] if name_parts else ''
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    
    # Generate username from email or name
    username = email.split('@')[0]
    
    # Ensure username is unique
    base_username = username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1
    
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        google_id=google_id,
        google_email=email,
        google_name=name,
        google_picture=picture,
        auth_provider='google'
    )
    
    db.session.add(user)
    db.session.commit()
    
    return user


def get_google_auth_url(google_client):
    """Get Google OAuth authorization URL.
    
    Args:
        google_client: Google OAuth client
        
    Returns:
        str: Authorization URL
    """
    redirect_uri = url_for('auth.google_callback', _external=True)
    return google_client.authorize_redirect(redirect_uri)


def handle_google_callback(google_client, request):
    """Handle Google OAuth callback.
    
    Args:
        google_client: Google OAuth client
        request: Flask request object
        
    Returns:
        tuple: (success, user_or_error_message)
    """
    try:
        # Get authorization code from callback
        token = google_client.authorize_access_token()
        
        # Get user info from Google
        user_info = token.get('userinfo')
        
        if not user_info:
            # Fallback: get user info from Google's userinfo endpoint
            resp = google_client.get('userinfo')
            user_info = resp.json()
        
        # Verify that the user's email is verified
        if not user_info.get('email_verified'):
            return False, "Google account email not verified"
        
        # Create or update user
        user = create_or_update_google_user(user_info)
        
        return True, user
        
    except Exception as e:
        current_app.logger.error(f"Google OAuth error: {str(e)}")
        return False, f"Authentication failed: {str(e)}"
