#!/usr/bin/env python3
"""
Simple script to create admin user for Heroku deployment.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    from app.models import User
    
    print("Creating admin user...")
    
    app = create_app()
    
    with app.app_context():
        try:
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
                print("Password updated to 'admin123'")
                
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
                
                print("SUCCESS: Created admin user:")
                print(f"  Username: {admin_user.username}")
                print(f"  Email: {admin_user.email}")
                print(f"  Password: admin123")
                print(f"  Admin: {admin_user.is_admin}")
                
        except Exception as e:
            print(f"ERROR: Failed to create admin user: {str(e)}")
            db.session.rollback()
            sys.exit(1)
            
except ImportError as e:
    print(f"ERROR: Failed to import modules: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error: {str(e)}")
    sys.exit(1)

print("Admin user creation completed successfully!")
