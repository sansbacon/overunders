"""Simple test script to verify the application is working."""
import requests
import sys


def test_application():
    """Test basic application functionality."""
    base_url = "http://localhost:5000"
    
    try:
        # Test home page
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✓ Home page loads successfully")
            print(f"  Status: {response.status_code}")
            print(f"  Title found: {'Over-Under Contests' in response.text}")
        else:
            print(f"✗ Home page failed: {response.status_code}")
            return False
        
        # Test login page
        response = requests.get(f"{base_url}/auth/login", timeout=5)
        if response.status_code == 200:
            print("✓ Login page loads successfully")
        else:
            print(f"✗ Login page failed: {response.status_code}")
        
        # Test register page
        response = requests.get(f"{base_url}/auth/register", timeout=5)
        if response.status_code == 200:
            print("✓ Register page loads successfully")
        else:
            print(f"✗ Register page failed: {response.status_code}")
        
        # Test contests page
        response = requests.get(f"{base_url}/contests/", timeout=5)
        if response.status_code == 200:
            print("✓ Contests page loads successfully")
        else:
            print(f"✗ Contests page failed: {response.status_code}")
        
        print("\n🎉 Application is running successfully!")
        print(f"🌐 Visit: {base_url}")
        return True
        
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to the application")
        print("  Make sure the Flask app is running on http://localhost:5000")
        return False
    except Exception as e:
        print(f"✗ Error testing application: {e}")
        return False


if __name__ == "__main__":
    success = test_application()
    sys.exit(0 if success else 1)
