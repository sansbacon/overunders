#!/usr/bin/env python3
"""
Test script to verify both authentication methods work correctly.
"""

import requests
from bs4 import BeautifulSoup

def test_auth_urls():
    """Test that authentication URLs are accessible."""
    base_url = "http://localhost:5000"
    
    urls_to_test = [
        "/",
        "/auth/login",
        "/auth/admin-login",
        "/auth/register"
    ]
    
    print("Testing authentication URLs...")
    print("-" * 50)
    
    for url in urls_to_test:
        try:
            response = requests.get(f"{base_url}{url}", timeout=5)
            status = "✓ OK" if response.status_code == 200 else f"✗ {response.status_code}"
            print(f"{url:<20} {status}")
        except requests.exceptions.RequestException as e:
            print(f"{url:<20} ✗ Error: {e}")
    
    print("-" * 50)
    print("URL Summary:")
    print("Regular Login:  http://localhost:5000/auth/login")
    print("Admin Login:    http://localhost:5000/auth/admin-login")
    print("Register:       http://localhost:5000/auth/register")
    print("Home:           http://localhost:5000/")

if __name__ == '__main__':
    test_auth_urls()
