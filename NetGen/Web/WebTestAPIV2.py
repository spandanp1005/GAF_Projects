# Import necessary modules from Flask
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import os
import sqlite3
import json
from datetime import datetime
import sys
import os

# Assuming web.py and utils.py are in the same directory or properly imported.
# This line might need to be adjusted based on your project structure.
# If they are in the same directory, 'import utils' is sufficient.
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

# Create a Flask web application instance
app = Flask(__name__)
# Secret key for session management (important for security in production)
app.secret_key = 'your_super_secret_key_here_please_change_this_for_production'

# Define the directory where HTML templates will be stored
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.template_folder = template_dir

API_URL = "http://localhost:5000"

# --- Login Page and Authentication (now the landing page) ---
@app.route('/', methods=['GET', 'POST'])
def login():
    """
    Renders the login.html template and handles login attempts.
    This is now the landing page.
    """
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        url = f"{API_URL}/api/login"
        data = {
            "email": email,
            "password" : password,
        }
        
        response = utils.call_rest_api("POST", url, data)
        print(f"======= response = {response}")
        
        # This will now work correctly since call_rest_api returns a dict
        # whether the API call succeeds or fails.
        userId = int(response["user_id"])
        
        if userId > 0:
            # Store user ID in session upon successful login
            session['user_id'] = userId
            session['user_email'] = email
            
            # This redirect will now correctly point to the new success route
            # that takes an integer URL parameter.
            return redirect(url_for('success', contact_id=userId))
        else:
            error = 'Invalid Credentials. Please try again.'
    
    return render_template('login.html', error=error)

# --- Route for Register New User Form (index.html) ---
@app.route('/register', methods=['GET'])
def register_form():
    """
    Renders the index.html template for new user registration.
    This is now accessed via /register and requires user to be logged in.
    """
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    return render_template('index.html')

# --- Logout Route ---
@app.route('/logout')
def logout():
    """
    Logs out the user by clearing the session and redirects to login page.
    """
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/savecontact', methods=['POST'])
def savecontact():
    """
    API endpoint to save contact information to SQLite database.
    Expects JSON data with contact details.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must contain JSON data"}), 400
        
        contact_data = request.get_json()
        secret_key = request.headers.get('MyKey')

        if not contact_data:
            return jsonify({"error": "No data provided"}), 400
        
        name = contact_data.get('name', '')
        email = contact_data.get('email', '')
        phone = contact_data.get('phone', '')
        address = contact_data.get('address', '')
        message = contact_data.get('message', '')
        contact_owner_id = contact_data.get('user_id', '')
        
        if not name.strip():
            return jsonify({"error": "Name is required"}), 400
        
        if utils.validate_api_user(secret_key):
            return jsonify({"error": "User must be logged in to register contacts"}), 401
        
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contacts (name, email, phone, address, message, contact_owner_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, phone, address, message, contact_owner_id))
            
            contact_id = cursor.lastrowid
            conn.commit()
        
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
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """
    API endpoint to retrieve all contacts from the database.
    """
    try:
        url = f"{API_URL}/api/loadcontacts"
        contact_id = request.args.get('contact_id')
        params = {
            "user_id": contact_id
        }
        contacts = utils.call_rest_api("GET", url, )     
        
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
        
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# --- CHANGE 1: Corrected the route decorator for the success page ---
# It now correctly accepts 'contact_id' as a URL parameter.
@app.route('/success/<int:contact_id>')
def success(contact_id):
    """
    Route to display the success page after form submission or login.
    'contact_id' is now received directly from the URL.
    """
    print(f"==== web.py:success() -> contact_id = {contact_id}")

    # Your original session check is now active and is a good practice.
    if 'user_id' not in session:
        return redirect(url_for('login'))

    logged_in_user_id = session['user_id']
    print(f"==== web.py:success() -> logged user id = {logged_in_user_id}")
    
    # We no longer need to get contact_id from request.args.get()
    # It's already available as a function argument.

    try:
        # Check if the requested contact belongs to the logged-in user
        if not (contact_id == logged_in_user_id):
            return redirect(url_for('login'))
        
        with utils.get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM contacts WHERE contact_owner_id = ? ORDER BY id ASC', (logged_in_user_id,))
            user_contact_ids = [row['id'] for row in cursor.fetchall()]
            
            # Check if the requested contact exists and belongs to the logged-in user
            if contact_id not in user_contact_ids:
                if user_contact_ids:
                    return redirect(url_for('success', contact_id=user_contact_ids[0]))
                else:
                    return redirect(url_for('login'))
            
            cursor.execute('SELECT * FROM contacts WHERE id = ? AND contact_owner_id = ?', (contact_id, logged_in_user_id))
            contact = cursor.fetchone()
            
            if not contact:
                return redirect(url_for('login'))
            
            current_index = user_contact_ids.index(contact_id)
            total_user_contacts = len(user_contact_ids)
            
            prev_contact_id = user_contact_ids[current_index - 1] if current_index > 0 else None
            next_contact_id = user_contact_ids[current_index + 1] if current_index < total_user_contacts - 1 else None
            
            cursor.execute('SELECT id, name FROM contacts WHERE contact_owner_id = ? ORDER BY created_at DESC', (logged_in_user_id,))
            user_contacts = cursor.fetchall()

            contact_data = {
                "id": contact["id"],
                "name": contact["name"],
                "email": contact["email"],
                "phone": contact["phone"],
                "address": contact["address"],
                "message": contact["message"],
                "created_at": contact["created_at"],
                "contact_owner_id": contact["contact_owner_id"]
            }
            
            navigation = {
                "current_position": current_index + 1,
                "total_contacts": total_user_contacts,
                "prev_contact_id": prev_contact_id,
                "next_contact_id": next_contact_id,
                "has_prev": prev_contact_id is not None,
                "has_next": next_contact_id is not None,
                "is_logged_in": True,
                "user_id": logged_in_user_id
            }
            
            user_toggle = {
                "current_contact_id": contact_id,
                "user_contacts": [{"id": row["id"], "name": row["name"]} for row in user_contacts],
                "has_multiple_contacts": len(user_contacts) > 1
            }
            
            return render_template('success.html', contact=contact_data, navigation=navigation, user_toggle=user_toggle)
            
    except sqlite3.Error as e:
        print(f"Database error in success route: {e}")
        return redirect(url_for('login'))
    
    except Exception as e:
        print(f"An error occurred in success route: {e}")
        return redirect(url_for('login'))

# --- NEW ROUTE: Added the missing /api/login endpoint ---
# This is the endpoint that your front-end login form was trying to call.
@app.route('/api/login', methods=['POST'])
def api_login():
    """
    API endpoint to handle login requests.
    Expects JSON with 'email' and 'password'.
    Returns a JSON object with 'user_id' and a message.
    """
    if not request.is_json:
        return jsonify({"message": "Request must be JSON", "user_id": -1}), 400

    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Email and password are required", "user_id": -1}), 400

    try:
        with utils.get_db_connection() as conn:
            user = conn.execute(
                'SELECT id FROM users WHERE email = ? AND password = ?',
                (email, password)
            ).fetchone()

            if user:
                return jsonify({"message": "Login successful", "user_id": user['id']}), 200
            else:
                return jsonify({"message": "Invalid Credentials. Please try again.", "user_id": -1}), 401

    except sqlite3.Error as e:
        return jsonify({"message": f"Database error: {str(e)}", "user_id": -1}), 500

    except Exception as e:
        return jsonify({"message": f"An unexpected error occurred: {str(e)}", "user_id": -1}), 500

if __name__ == '__main__':
    print("=========starting API ========")
    print("Server will be available at: http://localhost:5000")
    print("Contact and User IDs reset to start from 1 for this session")
    print("=" * 60)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Server stopped by user")
        print("All session data has been cleared")
        print("Contact and User IDs will reset to 1 on next startup")


 # Import necessary modules from Flask
# from flask import Flask, render_template, jsonify, request, redirect, url_for, session
# import os
# import sqlite3
# import json
# from datetime import datetime
# import sys
# import os
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# import utils

# # Create a Flask web application instance
# app = Flask(__name__)
# # Secret key for session management (important for security in production)
# # In a real application, this should be a long, random string
# app.secret_key = 'your_super_secret_key_here_please_change_this_for_production'

# # Define the directory where HTML templates will be stored
# # This assumes 'templates' folder is in the same directory as this Python script
# template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
# app.template_folder = template_dir

# API_URL = "http://localhost:5000"

# # --- Login Page and Authentication (now the landing page) ---
# @app.route('/', methods=['GET', 'POST'])
# def login():
#     """
#     Renders the login.html template and handles login attempts.
#     This is now the landing page.
#     """
#     error = None
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         url = f"{API_URL}/api/login"
#         data = {
#             "email": email,
#             "password" : password,
#         }
#         #print(url)
#         #print(data)
#         response = utils.call_rest_api("POST", url, data )
#         print(f"======= response = {response}")
#         userId = int(response["user_id"])
#         if userId > 0:
#             # Store user ID in session upon successful login
#             session['user_id'] = userId
#             session['user_email'] = email
#             # Redirect to the success page for this user's contact ID
#             # The user['id'] from the users table now corresponds to a contact_id
#             print(1)
#             return redirect(url_for('success', contact_id=userId))
#         else:
#             error = 'Invalid Credentials. Please try again.'
    
#     return render_template('login.html', error=error)

# # --- Route for Register New User Form (index.html) ---
# @app.route('/register', methods=['GET'])
# def register_form():
#     """
#     Renders the index.html template for new user registration.
#     This is now accessed via /register and requires user to be logged in.
#     """
#     # Check if user is logged in
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     return render_template('index.html')

# # --- Logout Route ---
# @app.route('/logout')
# def logout():
#     """
#     Logs out the user by clearing the session and redirects to login page.
#     """
#     session.clear()
#     return redirect(url_for('login'))

# @app.route('/api/savecontact', methods=['POST'])
# def savecontact():
#     """
#     API endpoint to save contact information to SQLite database.
#     Expects JSON data with contact details.
#     """
#     try:
#         # Check if the request contains JSON data
#         if not request.is_json:
#             return jsonify({"error": "Request must contain JSON data"}), 400
        
#         # Get JSON data from the request
#         contact_data = request.get_json()
#         secret_key = request.headers.get('MyKey')

        
#         # Validate required fields
#         if not contact_data:
#             return jsonify({"error": "No data provided"}), 400
        
#         # Extract contact information with default values
#         name = contact_data.get('name', '')
#         email = contact_data.get('email', '')
#         phone = contact_data.get('phone', '') # Corrected typo here
#         address = contact_data.get('address', '')
#         message = contact_data.get('message', '')
#         contact_owner_id = contact_data.get('user_id', '')
        
#         # Validate that at least name is provided
#         if not name.strip():
#             return jsonify({"error": "Name is required"}), 400
        
#         # Check if user is logged in
#         if utils.validate_api_user(secret_key):
#             return jsonify({"error": "User must be logged in to register contacts"}), 401

        
#         # Save to database
#         with utils.get_db_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 INSERT INTO contacts (name, email, phone, address, message, contact_owner_id)
#                 VALUES (?, ?, ?, ?, ?, ?)
#             ''', (name, email, phone, address, message, contact_owner_id))
            
#             contact_id = cursor.lastrowid
#             conn.commit()
        
#         # Return success response with the created contact ID
#         return jsonify({
#             "success": True,
#             "message": "Contact saved successfully",
#             "contact_id": contact_id,
#             "data": {
#                 "name": name,
#                 "email": email,
#                 "phone": phone,
#                 "address": address,
#                 "message": message
                
#             }
#         }), 200
        
#     except sqlite3.Error as e:
#         # Handle database errors
#         return jsonify({"error": f"Database error: {str(e)}"}), 500
    
#     except Exception as e:
#         # Handle other unexpected errors
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# @app.route('/api/contacts', methods=['GET'])
# def get_contacts():
#     """
#     API endpoint to retrieve all contacts from the database.
#     """
#     try:
#         url = f"{API_URL}/api/loadcontacts"
#         contact_id = request.args.get('contact_id')
#         params = {
#             "user_id": contact_id
#         }
#         contacts = utils.call_rest_api("GET", url, )    
#         # Convert rows to dictionaries
#         contacts_list = []
#         for contact in contacts:
#             contacts_list.append({
#                 "id": contact["id"],
#                 "name": contact["name"],
#                 "email": contact["email"],
#                 "phone": contact["phone"],
#                 "address": contact["address"],
#                 "message": contact["message"],
#                 "created_at": contact["created_at"]
#             })
        
#         return jsonify({
#             "success": True,
#             "contacts": contacts_list,
#             "count": len(contacts_list)
#         })
       
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# @app.route('/success')
# def success():
#     """
#     Route to display the success page after form submission or login.
#     Expects contact_id as a query parameter to display the saved contact.
#     Now includes navigation information for browsing between contacts owned by the logged-in user.
#     """
#     # Check if user is logged in
#     contact_id = request.args.get('contact_id')
#     print(f"==== web.py:success() -> contactI = {contact_id}")

#     #TOOD Validate thser contact in active session
#     # if 'user_id' not in session:
#     #     return redirect(url_for('login'))
    
#     #contact_id = request.args.get('contact_id')
#     logged_in_user_id = session['user_id']
#     print(f"==== web.py:success() -> logged user id = {logged_in_user_id}")
    
#     if not contact_id:
#         # If no contact_id provided, redirect to login page
#         return redirect(url_for('login'))
    
#     try:
#         contact_id = int(contact_id)
#     except ValueError:
#         # If contact_id is not a valid integer, redirect to login page
#         return redirect(url_for('login'))
    
#     try:
#         with utils.get_db_connection() as conn:
#             cursor = conn.cursor()
            
#             # Get all contacts owned by the logged-in user, ordered by ID
#             cursor.execute('SELECT id FROM contacts WHERE contact_owner_id = ? ORDER BY id ASC', (logged_in_user_id,))
#             user_contact_ids = [row['id'] for row in cursor.fetchall()]
            
#             # Check if the requested contact exists and belongs to the logged-in user
#             if contact_id not in user_contact_ids:
#                 # If contact doesn't belong to user, redirect to their first contact or login
#                 if user_contact_ids:
#                     return redirect(url_for('success', contact_id=user_contact_ids[0]))
#                 else:
#                     return redirect(url_for('login'))
            
#             # Get the specific contact
#             cursor.execute('SELECT * FROM contacts WHERE id = ? AND contact_owner_id = ?', (contact_id, logged_in_user_id))
#             contact = cursor.fetchone()
            
#             if not contact:
#                 return redirect(url_for('login'))
            
#             # Find current position in the user's contact list
#             current_index = user_contact_ids.index(contact_id)
#             total_user_contacts = len(user_contact_ids)
            
#             # Determine previous and next contact IDs within user's contacts
#             prev_contact_id = user_contact_ids[current_index - 1] if current_index > 0 else None
#             next_contact_id = user_contact_ids[current_index + 1] if current_index < total_user_contacts - 1 else None
            
#             # Get all contacts for user toggle dropdown (user's own contacts)
#             cursor.execute('SELECT id, name FROM contacts WHERE contact_owner_id = ? ORDER BY created_at DESC', (logged_in_user_id,))
#             user_contacts = cursor.fetchall()


#             #TODO Clean up as we are reading from api 
#             # url = f"{API_URL}/api/loadcontacts"
#             # data = {
#             #     "user_id": 1 # userId
#             # }
#             # response = utils.call_rest_api("POST", url, data )
#             # print(f"======= response = {response}")

#             #-----------

#             # Convert contact to dictionary for template
#             contact_data = {
#                 "id": contact["id"],
#                 "name": contact["name"],
#                 "email": contact["email"],
#                 "phone": contact["phone"],
#                 "address": contact["address"],
#                 "message": contact["message"],
#                 "created_at": contact["created_at"],
#                 "contact_owner_id": contact["contact_owner_id"]
#             }
            
#             # Navigation information (only within user's own contacts)
#             navigation = {
#                 "current_position": current_index + 1,  # 1-based for display
#                 "total_contacts": total_user_contacts,
#                 "prev_contact_id": prev_contact_id,
#                 "next_contact_id": next_contact_id,
#                 "has_prev": prev_contact_id is not None,
#                 "has_next": next_contact_id is not None,
#                 "is_logged_in": True,
#                 "user_id": logged_in_user_id
#             }
            
#             # User toggle information
#             user_toggle = {
#                 "current_contact_id": contact_id,
#                 "user_contacts": [{"id": row["id"], "name": row["name"]} for row in user_contacts],
#                 "has_multiple_contacts": len(user_contacts) > 1
#             }
            
#             return render_template('success.html', contact=contact_data, navigation=navigation, user_toggle=user_toggle)
            
#     except sqlite3.Error as e:
#         # On database error, redirect to login page
#         print(f"Database error in success route: {e}")
#         return redirect(url_for('login'))
    
#     except Exception as e:
#         # On any other error, redirect to login page
#         print(f"An error occurred in success route: {e}")
#         return redirect(url_for('login'))

# @app.route('/api/login', methods=['POST'])
# def api_login():
#     """
#     API endpoint to handle login requests.
#     Expects JSON with 'email' and 'password'.
#     Returns a JSON object with 'user_id' and a message.
#     """
#     # Check if the request body is JSON
#     if not request.is_json:
#         return jsonify({"message": "Request must be JSON", "user_id": -1}), 400

#     data = request.json
#     email = data.get('email')
#     password = data.get('password')

#     # Basic input validation
#     if not email or not password:
#         return jsonify({"message": "Email and password are required", "user_id": -1}), 400

#     try:
#         with utils.get_db_connection() as conn:
#             # Query the database for a user with matching email and password
#             # IMPORTANT: In a real app, passwords should be hashed and compared securely.
#             user = conn.execute(
#                 'SELECT id FROM users WHERE email = ? AND password = ?',
#                 (email, password)
#             ).fetchone()

#             if user:
#                 # Login successful, return the user's ID
#                 return jsonify({"message": "Login successful", "user_id": user['id']}), 200
#             else:
#                 # No user found, login failed
#                 return jsonify({"message": "Invalid Credentials. Please try again.", "user_id": -1}), 401

#     except sqlite3.Error as e:
#         # Handle database errors gracefully
#         return jsonify({"message": f"Database error: {str(e)}", "user_id": -1}), 500

#     except Exception as e:
#         # Handle other unexpected errors
#         return jsonify({"message": f"An unexpected error occurred: {str(e)}", "user_id": -1}), 500

# if __name__ == '__main__':
#     print("=========starting API ========")
#     print("Server will be available at: http://localhost:5000")
#     print("Contact and User IDs reset to start from 1 for this session")
#     print("=" * 60)
    
#     # Run the Flask application
#     # debug=True allows for automatic reloading on code changes and provides a debugger
#     # host='0.0.0.0' makes the server accessible from any IP address, useful for hosting
#     try:
#         app.run(debug=True, host='0.0.0.0', port=5000)
#     except KeyboardInterrupt:
#         print("\n" + "=" * 60)
#         print("Server stopped by user")
#         print("All session data has been cleared")
#         print("Contact and User IDs will reset to 1 on next startup")
