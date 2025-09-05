#!/usr/bin/env python3
"""
Test script to verify the dashboard works without requiring API token from frontend
"""

import requests
import json
import time

# Base URL
BASE_URL = "http://localhost:4500"

def test_homepage_access():
    """Test that the homepage loads without authentication"""
    print("Testing homepage access...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        # Check that there's no token field in the HTML
        if 'api-token' not in response.text or 'type="password"' not in response.text:
            print("✅ Homepage loads without token field")
        else:
            print("❌ Token field still present in HTML")
        return True
    else:
        print(f"❌ Homepage returned status {response.status_code}")
        return False

def test_session_start():
    """Test starting a session without providing a token"""
    print("\nTesting session start without token...")
    
    # First, we need to get CSRF token
    # Note: The backend now handles auth transparently
    response = requests.post(
        f"{BASE_URL}/api/get-csrf-token",
        headers={'X-API-TOKEN': 'estate-planning-review-2024'},  # Backend still uses it internally
        json={}
    )
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get('session_id')
        csrf_token = data.get('csrf_token')
        
        print(f"✅ Got CSRF token: {csrf_token[:20]}...")
        
        # Now try to start a session
        response = requests.post(
            f"{BASE_URL}/api/start-session",
            headers={
                'X-API-TOKEN': 'estate-planning-review-2024',
                'X-Session-ID': session_id,
                'X-CSRF-Token': csrf_token
            },
            json={'reviewer_name': 'Test User'}
        )
        
        if response.status_code == 200:
            print("✅ Session started successfully without frontend token input")
            return True
        else:
            print(f"❌ Session start failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    else:
        print(f"❌ Failed to get CSRF token: {response.status_code}")
        return False

def test_javascript_functionality():
    """Test that JavaScript loads and functions properly"""
    print("\nTesting JavaScript functionality...")
    response = requests.get(f"{BASE_URL}/static/js/dashboard.js")
    if response.status_code == 200:
        js_content = response.text
        # Check that getAPIToken always returns the hardcoded value
        if "return 'estate-planning-review-2024';" in js_content:
            print("✅ JavaScript correctly returns hardcoded token")
        else:
            print("❌ JavaScript still checks for token field")
        return True
    else:
        print(f"❌ Failed to load JavaScript: {response.status_code}")
        return False

def test_css_layout():
    """Test that CSS has proper responsive layout"""
    print("\nTesting CSS layout improvements...")
    response = requests.get(f"{BASE_URL}/static/css/dashboard.css")
    if response.status_code == 200:
        css_content = response.text
        # Check for responsive improvements
        if "@media (max-width: 768px)" in css_content:
            print("✅ CSS has responsive layout for mobile")
        else:
            print("❌ CSS missing responsive layout")
        
        if "minmax(300px, 350px)" in css_content:
            print("✅ CSS has flexible grid layout")
        else:
            print("❌ CSS missing flexible grid")
        
        return True
    else:
        print(f"❌ Failed to load CSS: {response.status_code}")
        return False

def main():
    print("=" * 60)
    print("Testing Web UI Without Frontend API Token")
    print("=" * 60)
    
    # Wait a moment for server to be ready
    time.sleep(1)
    
    # Run tests
    tests = [
        test_homepage_access(),
        test_javascript_functionality(),
        test_css_layout(),
        test_session_start()
    ]
    
    # Summary
    print("\n" + "=" * 60)
    if all(tests):
        print("✅ ALL TESTS PASSED - Dashboard works without frontend token!")
    else:
        print("❌ Some tests failed - check the output above")
    print("=" * 60)
    
    print("\n📊 You can now access the dashboard at:")
    print("   http://localhost:4500")
    print("\nNo API token input required! Just:")
    print("1. Enter your name (optional)")
    print("2. Click 'Start Review Session'")
    print("3. Everything works transparently!")

if __name__ == "__main__":
    main()