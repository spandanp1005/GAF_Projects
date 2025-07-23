#!/usr/bin/env python3
"""
Test script to demonstrate contact ID reset functionality.
Run this script multiple times to see that IDs always start from 1.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5000"

def test_id_reset():
    """Test that contact IDs start from 1 each session."""
    print("🧪 Testing Contact ID Reset Functionality")
    print("=" * 50)
    
    # Test data for multiple contacts
    test_contacts = [
        {
            "name": "First Contact",
            "email": "first@example.com",
            "phone": "111-111-1111",
            "address": "111 First St"
        },
        {
            "name": "Second Contact", 
            "email": "second@example.com",
            "phone": "222-222-2222",
            "address": "222 Second St"
        },
        {
            "name": "Third Contact",
            "email": "third@example.com", 
            "phone": "333-333-3333",
            "address": "333 Third St"
        }
    ]
    
    print("📝 Adding test contacts...")
    contact_ids = []
    
    for i, contact in enumerate(test_contacts, 1):
        try:
            response = requests.post(
                f"{BASE_URL}/api/savecontact",
                headers={"Content-Type": "application/json"},
                json=contact
            )
            
            if response.status_code == 201:
                result = response.json()
                contact_id = result['contact_id']
                contact_ids.append(contact_id)
                print(f"✅ Contact {i}: '{contact['name']}' saved with ID: {contact_id}")
            else:
                print(f"❌ Failed to save contact {i}: {response.json()}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error saving contact {i}: {e}")
            return False
    
    print("\n📊 Results:")
    print(f"Contact IDs generated: {contact_ids}")
    
    # Check if IDs start from 1 and increment properly
    expected_ids = list(range(1, len(contact_ids) + 1))
    if contact_ids == expected_ids:
        print("✅ SUCCESS: Contact IDs start from 1 and increment correctly!")
        print(f"   Expected: {expected_ids}")
        print(f"   Actual:   {contact_ids}")
    else:
        print("❌ ISSUE: Contact IDs don't start from 1 or don't increment correctly")
        print(f"   Expected: {expected_ids}")
        print(f"   Actual:   {contact_ids}")
    
    print("\n💡 To test the reset functionality:")
    print("   1. Stop the Flask server (Ctrl+C)")
    print("   2. Start it again (python3 TestAPIV2.py)")
    print("   3. Run this test script again")
    print("   4. You should see IDs start from 1 again!")
    
    return contact_ids == expected_ids

if __name__ == "__main__":
    test_id_reset()
