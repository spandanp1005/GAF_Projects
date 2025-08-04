from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import os
import sqlite3
import json
from datetime import datetime
import requests

# Database configuration
DATABASE = 'contacts.db'

def get_db_connection():
    """
    Get a database connection with row factory for easier data access.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def validate_api_user(secret_key) -> bool:
    return secret_key == "Test123"


def init_db():

    """
    Initialize the SQLite database and create the contacts and users tables.
    Clears existing data and resets ID counters to start fresh each session.
    Crucially, it populates initial users and corresponding contacts
    to ensure login leads to a pre-existing contact page.
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # --- Initialize Users Table First ---
        cursor.execute('DROP TABLE IF EXISTS users')
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert initial user data and store their generated IDs
        # In a real application, passwords should be hashed (e.g., using Werkzeug.security.generate_password_hash)
        # For this example, we'll use plain text as provided by the user.
        initial_users_data = [
            ("spatel@gmail.com", "spatel123", "Spandan Patel", "spatel@gmail.com", "111-222-3333", "123 Main St, Anytown, USA", "Enquiry about services."),
            ("jsmith@gmail.com", "jsmith123", "John Smith", "jsmith@gmail.com", "444-555-6666", "456 Oak Ave, Somewhere, USA", "General feedback."),
            ("jdoe@gmail.com", "jdoe123", "Jane Doe", "jdoe@gmail.com", "777-888-9999", "789 Pine Ln, Nowhere, USA", "Question about registration.")
        ]
        
        # This list will store (user_id, name, email, phone, address, message) for contacts table
        contact_entries_for_initial_users = []

        for email, password, name, contact_email, phone, address, message in initial_users_data:
            cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
            user_id = cursor.lastrowid # Get the ID assigned to the newly inserted user
            contact_entries_for_initial_users.append((user_id, name, contact_email, phone, address, message))

        # Reset the SQLite sequence counter for users to ensure AUTOINCREMENT starts from 1 next time
        # This is for consistency in a fresh session, not strictly necessary for existing IDs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='users'") 

        # --- Initialize Contacts Table ---
        cursor.execute('DROP TABLE IF EXISTS contacts')
        cursor.execute('''
            CREATE TABLE contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                address TEXT,
                message TEXT,
                contact_owner_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_owner_id) REFERENCES users (id)
            )
        ''')
        
        # Insert initial contact data, ensuring their IDs match the user IDs
        # We explicitly set the ID here to match the user_id for seamless navigation
        for contact_id, name, email, phone, address, message in contact_entries_for_initial_users:
            cursor.execute('''
                INSERT INTO contacts (id, name, email, phone, address, message, contact_owner_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (contact_id, name, email, phone, address, message, contact_id))

        # Reset the SQLite sequence counter for contacts to ensure AUTOINCREMENT starts from the next available ID
        # after our explicit inserts. For example, if we inserted IDs 1, 2, 3, next autoinc will be 4.
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='contacts'") 
        
        conn.commit()
        print("Database initialized - Contacts and Users tables created and populated.")
        print("Contact and User IDs will start from 1 for this session.")

import requests


def call_rest_api(method_type, api_url, queryParamsOrJsonData):
    response = None
    if method_type == "GET": 
        response = requests.get(api_url, params=queryParamsOrJsonData)
    else: 
        print(queryParamsOrJsonData)
        response = requests.post(api_url, json=queryParamsOrJsonData) 

    # Check if the request was successful
    if response.status_code >= 200 and response.status_code < 300: # Check for 2xx status codes
        try:
            json_data = response.json()
            print("Successful API Call - JSON Response:")
            print(json_data)
            return json_data
        except requests.exceptions.JSONDecodeError:
            print("Response is not valid JSON:")
            print(response.text)
            # Return a dictionary with an error message and a default user_id
            return {"message": "Invalid JSON response", "user_id": -1}
    else:
        message = f"Failed to call API. Status code: {response.status_code}. Error ={response.text}"
        print(message)
        # Return a dictionary with an error message and a default user_id
        return {"message": message, "user_id": -1}
# def call_rest_api(method_type, api_url, queryParamsOrJsonData):
#     response = None
#     # Specify the URL of the REST API
#     # Specify any parameters or data to be sent in the request (if needed)
#     if method_type == "GET": 
#     # Make the GET request to the API
#         response = requests.get(api_url, params=queryParamsOrJsonData)
#     else: 
#         print(queryParamsOrJsonData)
#         response = requests.post(api_url, json=queryParamsOrJsonData) 
#     # Check if the request was successful
#     if response.status_code >= 200:
#         try:
#             json_data = response.json()
#             print("200=====")
#             print(json_data)
#             return json_data
#         except requests.exceptions.JSONDecodeError:
#             print("Response is not valid JSON:")
#             print(response.text)
#             return jsonify({"message": "Invalid JSON response", "user_id": "-1"}), 400
#     else:
#         message = f"Failed to call API. Status code: {response.status_code}. Error ={response.text}"
#         return jsonify({"message": message, "user_id": f"-1"}), 400
    