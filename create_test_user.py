#!/usr/bin/env python3
"""
Simple script to create a test user for testing
"""
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app import create_app, db
from app.models import User

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
        print(f"Username: {test_user.username}")
        print(f"Email: {test_user.email}")
        return test_user

if __name__ == '__main__':
    create_test_user()
