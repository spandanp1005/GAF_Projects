#!/usr/bin/env python3
"""
Test script for the Contact API endpoints.
This script demonstrates how to save and retrieve contacts using the Flask API.
"""

import requests
import json

# API base URL
BASE_URL = "http://localhost:5000"

def test_save_contact():
    """Test saving a contact to the database."""
    print("Testing /api/savecontact endpoint...")
    
    # Sample contact data
    contact_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "address": "123 Main Street, Anytown, USA 12345",
        "message": "This is a test contact submission."
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/savecontact",
            headers={"Content-Type": "application/json"},
            json=contact_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Contact saved successfully!")
            return True
        else:
            print("❌ Failed to save contact")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error making request: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Contact API")
    test_save_contact()
