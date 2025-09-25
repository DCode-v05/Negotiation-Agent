#!/usr/bin/env python3
"""
Test script to verify seller authentication and redirection flow
"""

import requests
import json

def test_seller_auth():
    """Test seller registration and login"""
    base_url = "http://localhost:8000"
    
    # Test data for seller (using unique identifier)
    import time
    unique_id = int(time.time()) % 10000  # Keep it short
    seller_data = {
        "username": f"seller{unique_id}@test.com",
        "email": f"seller{unique_id}@test.com", 
        "password": "testpass123",
        "full_name": "Test Seller",
        "phone": "1234567890",
        "role": "seller"
    }
    
    print("Testing Seller Authentication Flow")
    print("=" * 50)
    
    # Test registration
    print("1. Testing seller registration...")
    response = requests.post(f"{base_url}/api/auth/register", json=seller_data)
    print(f"Registration Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Registration Response: {json.dumps(data, indent=2)}")
        
        if data.get("success"):
            print("✅ Seller registration successful!")
            user_data = data.get("user", {})
            print(f"User Role: {user_data.get('role')}")
            
            if user_data.get('role') == 'seller':
                print("✅ Role correctly set as 'seller'")
            else:
                print("❌ Role issue - expected 'seller', got:", user_data.get('role'))
        else:
            print("❌ Registration failed:", data.get("message"))
            
            # Try login instead (user might already exist)
            print("\n2. Trying login instead...")
            login_data = {
                "username": seller_data["username"],
                "password": seller_data["password"],
                "role": "seller"
            }
            
            response = requests.post(f"{base_url}/api/auth/login", json=login_data)
            print(f"Login Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Login Response: {json.dumps(data, indent=2)}")
                
                if data.get("success"):
                    print("✅ Seller login successful!")
                    user_data = data.get("user", {})
                    print(f"User Role: {user_data.get('role')}")
                    
                    if user_data.get('role') == 'seller':
                        print("✅ Role correctly set as 'seller'")
                        print("✅ Redirection should work to seller-portal.html")
                    else:
                        print("❌ Role issue - expected 'seller', got:", user_data.get('role'))
                else:
                    print("❌ Login failed:", data.get("message"))
            else:
                print(f"❌ Login request failed with status {response.status_code}")
                print(response.text)
    else:
        print(f"❌ Registration request failed with status {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    try:
        test_seller_auth()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server at http://localhost:8000")
        print("Make sure the backend server is running with: python backend/main.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")