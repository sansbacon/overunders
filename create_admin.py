#!/usr/bin/env python3
"""
Script to create an admin user with password for testing the dual authentication system.
"""

from app import create_app, db
from app.models import User

def create_admin_user():
    """Create an admin user with password."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print(f"Admin user '{admin_user.username}' already exists.")
            
            # Update to admin if not already
            if not admin_user.is_admin:
                admin_user.is_admin = True
                print("Updated user to admin status.")
            
            # Set password
            admin_user.set_password('admin123')
            db.session.commit()
            print("Password set to 'admin123'")
            
        else:
            # Create new admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            db.session.commit()
            
            print("Created admin user:")
            print(f"  Username: {admin_user.username}")
            print(f"  Email: {admin_user.email}")
            print(f"  Password: admin123")
            print(f"  Admin: {admin_user.is_admin}")

if __name__ == '__main__':
    create_admin_user()
