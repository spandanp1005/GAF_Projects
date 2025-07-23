#!/usr/bin/env python3
"""
Test script to demonstrate the navigation functionality on the success page.
This script will create multiple contacts and show how to navigate between them.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://localhost:5000"

def create_test_contacts():
    """Create multiple test contacts to demonstrate navigation."""
    print("🧪 Creating Test Contacts for Navigation Demo")
    print("=" * 60)
    
    # Test data for multiple contacts
    test_contacts = [
        {
            "name": "Alice Johnson",
            "email": "alice.johnson@example.com",
            "phone": "555-0101",
            "address": "123 Maple Street, Springfield, IL 62701",
            "message": "Looking forward to connecting with your team!"
        },
        {
            "name": "Bob Smith",
            "email": "bob.smith@example.com",
            "phone": "555-0102", 
            "address": "456 Oak Avenue, Chicago, IL 60601",
            "message": "Interested in your services and would like more information."
        },
        {
            "name": "Carol Davis",
            "email": "carol.davis@example.com",
            "phone": "555-0103",
            "address": "789 Pine Road, Peoria, IL 61602",
            "message": "Excited to be part of this community!"
        },
        {
            "name": "David Wilson",
            "email": "david.wilson@example.com", 
            "phone": "555-0104",
            "address": "321 Elm Circle, Rockford, IL 61103",
            "message": "Thank you for providing this registration system."
        },
        {
            "name": "Eva Martinez",
            "email": "eva.martinez@example.com",
            "phone": "555-0105", 
            "address": "654 Birch Lane, Naperville, IL 60540",
            "message": "Looking forward to future opportunities!"
        }
    ]
    
    created_contacts = []
    
    for i, contact in enumerate(test_contacts, 1):
        try:
            print(f"📝 Creating contact {i}: {contact['name']}...")
            
            response = requests.post(
                f"{BASE_URL}/api/savecontact",
                headers={"Content-Type": "application/json"},
                json=contact
            )
            
            if response.status_code == 201:
                result = response.json()
                contact_id = result['contact_id']
                created_contacts.append({
                    'id': contact_id,
                    'name': contact['name']
                })
                print(f"✅ Contact created with ID: {contact_id}")
            else:
                print(f"❌ Failed to create contact: {response.json()}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating contact: {e}")
            return None
        
        # Small delay between requests
        time.sleep(0.5)
    
    return created_contacts

def demonstrate_navigation(contacts):
    """Show navigation URLs and instructions."""
    if not contacts:
        print("❌ No contacts created - cannot demonstrate navigation")
        return
    
    print("\n🎯 Navigation Demonstration")
    print("=" * 60)
    print(f"✅ Created {len(contacts)} contacts successfully!")
    print("\n📋 Contact List:")
    
    for contact in contacts:
        print(f"   ID {contact['id']}: {contact['name']}")
    
    print(f"\n🌐 Navigation URLs:")
    print(f"   First Contact:  {BASE_URL}/success?contact_id={contacts[0]['id']}")
    print(f"   Middle Contact: {BASE_URL}/success?contact_id={contacts[len(contacts)//2]['id']}")
    print(f"   Last Contact:   {BASE_URL}/success?contact_id={contacts[-1]['id']}")
    
    print("\n🎮 How to Test Navigation:")
    print("1. Open any of the URLs above in your browser")
    print("2. You'll see navigation arrows:")
    print("   • 🔵 Blue arrows = Clickable (more contacts in that direction)")
    print("   • ⚪ Gray arrows = Disabled (no more contacts in that direction)")
    print("3. Click the arrows to navigate between contacts")
    print("4. Use keyboard shortcuts:")
    print("   • ← or A key = Previous contact")
    print("   • → or D key = Next contact")
    print("5. The counter shows 'X of Y' (current position of total)")
    
    print("\n🔍 Expected Behavior:")
    print("• First contact: Left arrow gray, right arrow blue")
    print("• Middle contacts: Both arrows blue")
    print("• Last contact: Left arrow blue, right arrow gray")
    print("• Single contact: Navigation section hidden")
    
    print(f"\n🚀 Start here: {BASE_URL}/success?contact_id={contacts[0]['id']}")

if __name__ == "__main__":
    print("🎯 NetGen Navigation System Demo")
    print("Make sure the Flask server is running on localhost:5000")
    print("=" * 60)
    
    # Create test contacts
    contacts = create_test_contacts()
    
    if contacts:
        # Demonstrate navigation
        demonstrate_navigation(contacts)
    else:
        print("❌ Failed to create test contacts. Make sure the server is running!")
