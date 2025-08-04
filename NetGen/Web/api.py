# Import necessary modules from Flask
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import os
import sqlite3
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

# Create a Flask web application instance
app = Flask(__name__)
# Secret key for session management (important for security in production)
# In a real application, this should be a long, random string
app.secret_key = 'your_super_secret_key_here_please_change_this_for_production'


# Initialize the database when the app starts
utils.init_db()

# --- Logout Route ---
@app.route('/api/logout')
def logout():
    """
    Logs out the user by clearing the session and redirects to login page.
    """
    user_id= request.args.get('user_id')

    if not user_id:
        data = request.get_json()
        user_id= data.get("user_id")

    message = "Invalid User or Password"
    if user_id > 0:
        message = "Logout succesful"
    return jsonify({"message": message, "user_id": f"{user_id}"}), 200
    
@app.route('/api/login',methods=["GET", "POST"])
def login() :
    """
    Logs out the user by clearing the session and redirects to login page.
    """
    email = request.args.get('email')
    password = request.args.get('password')

    if not email:
        data = request.get_json()
        email = data.get("email")

    if not password:
        data = request.get_json()
        password = data.get("password")

    user_id = -1
    with utils.get_db_connection() as conn:
        cursor = conn.cursor()
        print("cursor---",cursor)
        # In a real app, you'd hash the password and compare hashes
        cursor.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        if user:
            user_id = user['id']
    
         
    message = "Invalid User or Password"
    if user_id > 0:
        message = "Login succesful"
    return jsonify({"message": message, "user_id": f"{user_id}"}), 200

@app.route("/api/saveuser", methods=["POST"])
def saveuser():
    """
    Save a new user and return user id
    """
    email = request.args.get('email')
    password = request.args.get('password')

    if not email:
        data = request.get_json()
        email = data.get("email")

    if not password:
        data = request.get_json()
        password = data.get("password")

    user_id = -1
    with utils.get_db_connection() as conn:
        cursor = conn.cursor()
        print("cursor---",cursor)
        # In a real app, you'd hash the password and compare hashes
        cursor.execute(f"INSERT INTO users (email, password) VALUES ('{email}', '{password}')")
        conn.commit()
        cursor.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", (email, password))
        user = cursor.fetchone()
        if user:
            user_id = user['id']
    message = "Unable to create new user"
    if user_id > 0:
        message = "Successfully Created new user"
    return jsonify({"message": message, "user_id": f"{user_id}"}), 200

@app.route('/api/savecontact', methods=['POST'])
def savecontact():
    """
    API endpoint to save contact information to SQLite database.
    Expects JSON data with contact details.
    """
    try:
        # Check if the request contains JSON data
        if not request.is_json:
            return jsonify({"error": "Request must contain JSON data"}), 400
        
        # Get JSON data from the request
        contact_data = request.get_json()
        #secret_key = request.headers.get('MyKey')

        
        # Validate required fields
        if not contact_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract contact information with default values
        name = contact_data.get('name', '')
        email = contact_data.get('email', '')
        phone = contact_data.get('phone', '') # Corrected typo here
        address = contact_data.get('address', '')
        message = contact_data.get('message', '')
        contact_owner_id = contact_data.get('user_id', '')
        
        # Validate that at least name is provided
        if not name.strip():
            return jsonify({"error": "Name is required"}), 400
        
        # Check if user is logged in
        # if utils.validate_api_user(secret_key):
        #     return jsonify({"error": "User must be logged in to register contacts"}), 401

        
        # Save to database
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contacts (name, email, phone, address, message, contact_owner_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, address, message, contact_owner_id))
            
            contact_id = cursor.lastrowid
            conn.commit()
        
        # Return success response with the created contact ID
        return jsonify({
            "success": True,
            "message": "Contact saved successfully",
            "contact_id": contact_id,
            "data": {
                "name": name,
                "email": email,
                "phone": phone,
                "address": address,
                "message": message
                
            }
        }), 200
        
    except sqlite3.Error as e:
        # Handle database errors
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        # Handle other unexpected errors
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/api/loadcontacts', methods=['POST', 'GET'])
def get_contacts():
    """
    API endpoint to retrieve all contacts from the database.
    """
    user_id = request.args.get('user_id')
    if not user_id:
        data = request.get_json()
        user_id = data.get("user_id")
    try:
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM contacts where contact_owner_id = {user_id} ORDER BY created_at DESC")
            contacts = cursor.fetchall()
            
            # Convert rows to dictionaries
            contacts_list = []
            for contact in contacts:
                contacts_list.append({
                    "id": contact["id"],
                    "name": contact["name"],
                    "email": contact["email"],
                    "phone": contact["phone"],
                    "address": contact["address"],
                    "message": contact["message"],
                    "created_at": contact["created_at"]
                })
            
            return jsonify({
                "success": True,
                "contacts": contacts_list,
                "count": len(contacts_list)
            })
            
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/loadusers', methods=['GET'])
def get_users():
    """
    API endpoint to retrieve all users
    """
    try:
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM users")
            _users = cursor.fetchall()
            
            # Convert rows to dictionaries
            users = []
            for user in _users:
                users.append({
                    "id": user["id"],
                    "email": user["email"],
                    "pwd": user["password"],
                })
            
            return jsonify({
                "success": True,
                "contacts": users,
                "count": len(users)
            })
            
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    print("=========starting API ========")
    print("Server will be available at: http://localhost:5001")
    print("Contact and User IDs reset to start from 1 for this session")
    print("=" * 60)
    
    # Run the Flask application
    # debug=True allows for automatic reloading on code changes and provides a debugger
    # host='0.0.0.0' makes the server accessible from any IP address, useful for hosting
    try:
        app.run(debug=True, host='0.0.0.0', port=5001)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Server stopped by user")
        print("All session data has been cleared")
        print("Contact and User IDs will reset to 1 on next startup")
