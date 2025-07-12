#!/usr/bin/env python3
"""
Quick script to create a test user and generate a login token for testing
"""
import os
import sys
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import secrets

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app, db
from app.models import User, LoginToken

def create_test_user():
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(email='test@example.com').first()
        if existing_user:
            print(f"Test user already exists with ID: {existing_user.user_id}")
            return existing_user
        
        # Create test user
        test_user = User(
            username='testuser123',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password_hash=generate_password_hash('testpassword123'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print(f"Created test user with ID: {test_user.user_id}")
        return test_user

def generate_login_token(user):
    """Generate a login token for the user"""
    app = create_app()
    
    with app.app_context():
        # Create a login token using the existing LoginToken model
        login_token = LoginToken.create_token(user.email, expiration_minutes=60)
        
        # Generate login URL
        login_url = f"http://127.0.0.1:5000/auth/login/{login_token.token}"
        print(f"Login URL: {login_url}")
        return login_url

if __name__ == '__main__':
    user = create_test_user()
    login_url = generate_login_token(user)
    print(f"\nUse this URL to log in: {login_url}")
