# Import necessary modules from Flask
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import os
import sqlite3
import json
from datetime import datetime

# Create a Flask web application instance
app = Flask(__name__)
# Secret key for session management (important for security in production)
# In a real application, this should be a long, random string
app.secret_key = 'your_super_secret_key_here_please_change_this_for_production'

# Define the directory where HTML templates will be stored
# This assumes 'templates' folder is in the same directory as this Python script
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.template_folder = template_dir

# Database configuration
DATABASE = 'contacts.db'

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert initial contact data, ensuring their IDs match the user IDs
        # We explicitly set the ID here to match the user_id for seamless navigation
        for contact_id, name, email, phone, address, message in contact_entries_for_initial_users:
            cursor.execute('''
                INSERT INTO contacts (id, name, email, phone, address, message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (contact_id, name, email, phone, address, message))

        # Reset the SQLite sequence counter for contacts to ensure AUTOINCREMENT starts from the next available ID
        # after our explicit inserts. For example, if we inserted IDs 1, 2, 3, next autoinc will be 4.
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='contacts'") 
        
        conn.commit()
        print("Database initialized - Contacts and Users tables created and populated.")
        print("Contact and User IDs will start from 1 for this session.")


def get_db_connection():
    """
    Get a database connection with row factory for easier data access.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database when the app starts
init_db()

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
        print("email---", email)
        print("pwd--", password)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            print("cursor---",cursor)
            # In a real app, you'd hash the password and compare hashes
            cursor.execute("SELECT id, email FROM users WHERE email = ? AND password = ?", (email, password))
            user = cursor.fetchone()
            
            if user:
                # Store user ID in session upon successful login
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                # Redirect to the success page for this user's contact ID
                # The user['id'] from the users table now corresponds to a contact_id
                return redirect(url_for('success', contact_id=user['id']))
            else:
                error = 'Invalid Credentials. Please try again.'
    
    return render_template('login.html', error=error)

# --- Route for Register New User Form (index.html) ---
@app.route('/register', methods=['GET'])
def register_form():
    """
    Renders the index.html template for new user registration.
    This is now accessed via /register.
    """
    return render_template('index.html')

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
        
        # Validate required fields
        if not contact_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract contact information with default values
        name = contact_data.get('name', '')
        email = contact_data.get('email', '')
        phone = contact_data.get('phone', '') # Corrected typo here
        address = contact_data.get('address', '')
        message = contact_data.get('message', '')
        
        # Validate that at least name is provided
        if not name.strip():
            return jsonify({"error": "Name is required"}), 400
        
        # Save to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO contacts (name, email, phone, address, message)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, phone, address, message))
            
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
        }), 201
        
    except sqlite3.Error as e:
        # Handle database errors
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    
    except Exception as e:
        # Handle other unexpected errors
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """
    API endpoint to retrieve all contacts from the database.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM contacts ORDER BY created_at DESC')
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


@app.route('/success')
def success():
    """
    Route to display the success page after form submission or login.
    Expects contact_id as a query parameter to display the saved contact.
    Now includes navigation information for browsing between contacts.
    """
    contact_id = request.args.get('contact_id')
    
    if not contact_id:
        # If no contact_id provided, redirect to login page (the new landing page)
        return redirect(url_for('login'))
    
    try:
        contact_id = int(contact_id)
    except ValueError:
        # If contact_id is not a valid integer, redirect to login page
        return redirect(url_for('login'))
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all contacts ordered by ID to determine navigation
            cursor.execute('SELECT id FROM contacts ORDER BY id ASC')
            all_contact_ids = [row['id'] for row in cursor.fetchall()]
            
            # Check if the requested contact exists
            if contact_id not in all_contact_ids:
                return redirect(url_for('login'))
            
            # Get the specific contact
            cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
            contact = cursor.fetchone()
            
            # Find current position in the list
            current_index = all_contact_ids.index(contact_id)
            total_contacts = len(all_contact_ids)
            
            # Determine previous and next contact IDs
            prev_contact_id = all_contact_ids[current_index - 1] if current_index > 0 else None
            next_contact_id = all_contact_ids[current_index + 1] if current_index < total_contacts - 1 else None
            
            # Convert contact to dictionary for template
            contact_data = {
                "id": contact["id"],
                "name": contact["name"],
                "email": contact["email"],
                "phone": contact["phone"],
                "address": contact["address"],
                "message": contact["message"],
                "created_at": contact["created_at"]
            }
            
            # Navigation information
            navigation = {
                "current_position": current_index + 1,  # 1-based for display
                "total_contacts": total_contacts,
                "prev_contact_id": prev_contact_id,
                "next_contact_id": next_contact_id,
                "has_prev": prev_contact_id is not None,
                "has_next": next_contact_id is not None
            }
            
            return render_template('success.html', contact=contact_data, navigation=navigation)
            
    except sqlite3.Error as e:
        # On database error, redirect to login page
        print(f"Database error in success route: {e}")
        return redirect(url_for('login'))
    
    except Exception as e:
        # On any other error, redirect to login page
        print(f"An error occurred in success route: {e}")
        return redirect(url_for('login'))

# Main entry point of the application
# This block ensures the Flask app runs only when the script is executed directly
if __name__ == '__main__':
    print("Starting NetGen Contact Registration System...")
    print("Server will be available at: http://localhost:5000")
    print("Contact and User IDs reset to start from 1 for this session")
    print("=" * 60)
    
    # Run the Flask application
    # debug=True allows for automatic reloading on code changes and provides a debugger
    # host='0.0.0.0' makes the server accessible from any IP address, useful for hosting
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("Server stopped by user")
        print("All session data has been cleared")
        print("Contact and User IDs will reset to 1 on next startup")

# # Import necessary modules from Flask
# from flask import Flask, render_template, jsonify, request, redirect
# import os
# import sqlite3
# import json
# from datetime import datetime

# # Create a Flask web application instance
# app = Flask(__name__)

# # Define the directory where HTML templates will be stored
# # This assumes 'templates' folder is in the same directory as this Python script
# template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
# app.template_folder = template_dir

# # Database configuration
# DATABASE = 'contacts.db'

# def init_db():
#     """
#     Initialize the SQLite database and create the contacts table.
#     Clears existing data and resets ID counter to start fresh each session.
#     """
#     with sqlite3.connect(DATABASE) as conn:
#         cursor = conn.cursor()
        
#         # Drop the table if it exists (this clears all data)
#         cursor.execute('DROP TABLE IF EXISTS contacts')
        
#         # Create the table fresh
#         cursor.execute('''
#             CREATE TABLE contacts (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 name TEXT NOT NULL,
#                 email TEXT,
#                 phone TEXT,
#                 address TEXT,
#                 message TEXT,
#                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#             )
#         ''')
        
#         # Reset the SQLite sequence counter to start from 1
#         cursor.execute("DELETE FROM sqlite_sequence WHERE name='contacts'")
        
#         conn.commit()
#         print("Database initialized - Contact IDs will start from 1")

# def get_db_connection():
#     """
#     Get a database connection with row factory for easier data access.
#     """
#     conn = sqlite3.connect(DATABASE)
#     conn.row_factory = sqlite3.Row
#     return conn

# # Initialize the database when the app starts (resets contact IDs to start from 1)
# init_db()

# # Route to serve the index.html file
# # When a user accesses the root URL '/', this function will be called
# @app.route('/')
# def index():
#     """
#     Renders the index.html template.
#     """
#     # render_template looks for 'index.html' in the configured template folder
#     return render_template('index.html')

# # Define a simple API endpoint
# # When a user accesses '/api/hello', this function will be called
# @app.route('/api/hello', methods=['GET'])
# def hello_api():
#     """
#     A simple API endpoint that returns a greeting message.
#     It can optionally take a 'name' query parameter.
#     """
#     # Get the 'name' parameter from the URL query string, default to 'World' if not provided
#     name = request.args.get('name', 'World')
#     # Return a JSON response
#     return jsonify({"message": f"Hello, {name}!"})


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
        
#         # Validate required fields
#         if not contact_data:
#             return jsonify({"error": "No data provided"}), 400
        
#         # Extract contact information with default values
#         name = contact_data.get('name', '')
#         email = contact_data.get('email', '')
#         phone = contact_data.get('phone', '')
#         address = contact_data.get('address', '')
#         message = contact_data.get('message', '')
        
#         # Validate that at least name is provided
#         if not name.strip():
#             return jsonify({"error": "Name is required"}), 400
        
#         # Save to database
#         with get_db_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('''
#                 INSERT INTO contacts (name, email, phone, address, message)
#                 VALUES (?, ?, ?, ?, ?)
#             ''', (name, email, phone, address, message))
            
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
#         }), 201
        
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
#         with get_db_connection() as conn:
#             cursor = conn.cursor()
#             cursor.execute('SELECT * FROM contacts ORDER BY created_at DESC')
#             contacts = cursor.fetchall()
            
#             # Convert rows to dictionaries
#             contacts_list = []
#             for contact in contacts:
#                 contacts_list.append({
#                     "id": contact["id"],
#                     "name": contact["name"],
#                     "email": contact["email"],
#                     "phone": contact["phone"],
#                     "address": contact["address"],
#                     "message": contact["message"],
#                     "created_at": contact["created_at"]
#                 })
            
#             return jsonify({
#                 "success": True,
#                 "contacts": contacts_list,
#                 "count": len(contacts_list)
#             })
            
#     except sqlite3.Error as e:
#         return jsonify({"error": f"Database error: {str(e)}"}), 500
    
#     except Exception as e:
#         return jsonify({"error": f"An error occurred: {str(e)}"}), 500


# @app.route('/success')
# def success():
#     """
#     Route to display the success page after form submission.
#     Expects contact_id as a query parameter to display the saved contact.
#     Now includes navigation information for browsing between contacts.
#     """
#     contact_id = request.args.get('contact_id')
    
#     if not contact_id:
#         # If no contact_id provided, redirect to home page
#         return redirect('/')
    
#     try:
#         contact_id = int(contact_id)
#     except ValueError:
#         # If contact_id is not a valid integer, redirect to home page
#         return redirect('/')
    
#     try:
#         with get_db_connection() as conn:
#             cursor = conn.cursor()
            
#             # Get all contacts ordered by ID to determine navigation
#             cursor.execute('SELECT id FROM contacts ORDER BY id ASC')
#             all_contact_ids = [row['id'] for row in cursor.fetchall()]
            
#             # Check if the requested contact exists
#             if contact_id not in all_contact_ids:
#                 return redirect('/')
            
#             # Get the specific contact
#             cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
#             contact = cursor.fetchone()
            
#             # Find current position in the list
#             current_index = all_contact_ids.index(contact_id)
#             total_contacts = len(all_contact_ids)
            
#             # Determine previous and next contact IDs
#             prev_contact_id = all_contact_ids[current_index - 1] if current_index > 0 else None
#             next_contact_id = all_contact_ids[current_index + 1] if current_index < total_contacts - 1 else None
            
#             # Convert contact to dictionary for template
#             contact_data = {
#                 "id": contact["id"],
#                 "name": contact["name"],
#                 "email": contact["email"],
#                 "phone": contact["phone"],
#                 "address": contact["address"],
#                 "message": contact["message"],
#                 "created_at": contact["created_at"]
#             }
            
#             # Navigation information
#             navigation = {
#                 "current_position": current_index + 1,  # 1-based for display
#                 "total_contacts": total_contacts,
#                 "prev_contact_id": prev_contact_id,
#                 "next_contact_id": next_contact_id,
#                 "has_prev": prev_contact_id is not None,
#                 "has_next": next_contact_id is not None
#             }
            
#             return render_template('success.html', contact=contact_data, navigation=navigation)
            
#     except sqlite3.Error as e:
#         # On database error, redirect to home page
#         return redirect('/')
    
#     except Exception as e:
#         # On any other error, redirect to home page
#         return redirect('/')

# # Main entry point of the application
# # This block ensures the Flask app runs only when the script is executed directly
# if __name__ == '__main__':
#     print("Starting NetGen Contact Registration System...")
#     print("Server will be available at: http://localhost:5000")
#     print("Contact IDs reset to start from 1 for this session")
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
#         print("Contact IDs will reset to 1 on next startup")
