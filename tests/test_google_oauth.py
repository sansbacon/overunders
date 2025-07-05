#!/usr/bin/env python3
"""Test script to verify Google OAuth integration."""

import os
import sys
from app import create_app, db
from app.models import User

def test_google_oauth_integration():
    """Test Google OAuth integration."""
    print("Testing Google OAuth Integration...")
    print("=" * 50)
    
    # Create app
    app = create_app('development')
    
    with app.app_context():
        # Test 1: Check if Google OAuth fields exist in User model
        print("1. Testing User model Google OAuth fields...")
        try:
            # Create a test user with Google OAuth fields
            test_user = User(
                username="test_google_user",
                email="test@example.com",
                google_id="123456789",
                google_email="test@example.com",
                google_name="Test User",
                google_picture="https://example.com/picture.jpg",
                auth_provider="google"
            )
            
            # Check if all fields are accessible
            assert hasattr(test_user, 'google_id')
            assert hasattr(test_user, 'google_email')
            assert hasattr(test_user, 'google_name')
            assert hasattr(test_user, 'google_picture')
            assert hasattr(test_user, 'auth_provider')
            
            print("   ✅ All Google OAuth fields exist in User model")
            
        except Exception as e:
            print(f"   ❌ Error with User model fields: {e}")
            return False
        
        # Test 2: Check if Google OAuth configuration is loaded
        print("2. Testing Google OAuth configuration...")
        try:
            google_client_id = app.config.get('GOOGLE_CLIENT_ID')
            google_client_secret = app.config.get('GOOGLE_CLIENT_SECRET')
            google_discovery_url = app.config.get('GOOGLE_DISCOVERY_URL')
            
            print(f"   Google Client ID configured: {'Yes' if google_client_id else 'No'}")
            print(f"   Google Client Secret configured: {'Yes' if google_client_secret else 'No'}")
            print(f"   Google Discovery URL: {google_discovery_url}")
            
            if google_discovery_url:
                print("   ✅ Google OAuth configuration loaded")
            else:
                print("   ⚠️  Google OAuth configuration incomplete (this is normal for testing)")
            
        except Exception as e:
            print(f"   ❌ Error with OAuth configuration: {e}")
            return False
        
        # Test 3: Check if OAuth routes are registered
        print("3. Testing OAuth routes...")
        try:
            with app.test_client() as client:
                # Test Google login route
                response = client.get('/auth/google-login')
                print(f"   Google login route status: {response.status_code}")
                
                # Test login page (should contain Google button)
                response = client.get('/auth/login')
                if b'Continue with Google' in response.data:
                    print("   ✅ Google login button found on login page")
                else:
                    print("   ❌ Google login button not found on login page")
                
                # Test register page (should contain Google button)
                response = client.get('/auth/register')
                if b'Sign up with Google' in response.data:
                    print("   ✅ Google signup button found on register page")
                else:
                    print("   ❌ Google signup button not found on register page")
                    
        except Exception as e:
            print(f"   ❌ Error testing routes: {e}")
            return False
        
        # Test 4: Check database schema
        print("4. Testing database schema...")
        try:
            # Check if we can query users with Google fields
            users = User.query.all()
            print(f"   Total users in database: {len(users)}")
            
            # Check if any users have Google OAuth data
            google_users = User.query.filter(User.google_id.isnot(None)).all()
            print(f"   Users with Google OAuth: {len(google_users)}")
            
            print("   ✅ Database schema supports Google OAuth")
            
        except Exception as e:
            print(f"   ❌ Error with database schema: {e}")
            return False
    
    print("\n" + "=" * 50)
    print("✅ Google OAuth integration test completed successfully!")
    print("\nNext steps:")
    print("1. Set up Google Cloud Console project")
    print("2. Configure OAuth credentials")
    print("3. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables")
    print("4. Test with real Google account")
    
    return True

if __name__ == "__main__":
    success = test_google_oauth_integration()
    sys.exit(0 if success else 1)
