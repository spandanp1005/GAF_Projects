# Import necessary modules from Flask
from flask import Flask, render_template, jsonify, request, redirect
import os
import sqlite3
import json
from datetime import datetime

# Create a Flask web application instance
app = Flask(__name__)

# Define the directory where HTML templates will be stored
# This assumes 'templates' folder is in the same directory as this Python script
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.template_folder = template_dir

# Database configuration
DATABASE = 'contacts.db'

def init_db():
    """
    Initialize the SQLite database and create the contacts table.
    Clears existing data and resets ID counter to start fresh each session.
    """
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        
        # Drop the table if it exists (this clears all data)
        cursor.execute('DROP TABLE IF EXISTS contacts')
        
        # Create the table fresh
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
        
        # Reset the SQLite sequence counter to start from 1
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='contacts'")
        
        conn.commit()
        print("Database initialized - Contact IDs will start from 1")

def get_db_connection():
    """
    Get a database connection with row factory for easier data access.
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database when the app starts (resets contact IDs to start from 1)
init_db()

# Route to serve the login page as the landing page
# When a user accesses the root URL '/', this function will be called
@app.route('/')
def login_page():
    """
    Renders the login.html template as the landing page.
    """
    return render_template('login.html')

# Route to handle user login
@app.route('/login', methods=['POST'])
def login():
    """
    Handles user login authentication.
    """
    try:
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            return render_template('login.html', error='Please enter both email and password.')
        
        # Check credentials against Users table
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, email FROM Users WHERE email = ? AND password = ?', (email, password))
            user = cursor.fetchone()
            
            if user:
                # Login successful - redirect to user's contact info (success page with user ID)
                return redirect(f'/user/{user["id"]}')
            else:
                # Login failed
                return render_template('login.html', error='Invalid email or password. Please try again.')
                
    except Exception as e:
        return render_template('login.html', error='An error occurred during login. Please try again.')

# Route to serve the registration form (moved from root)
@app.route('/register')
def register():
    """
    Renders the index.html template for user registration.
    """
    return render_template('index.html')

# Define a simple API endpoint
# When a user accesses '/api/hello', this function will be called
@app.route('/api/hello', methods=['GET'])
def hello_api():
    """
    A simple API endpoint that returns a greeting message.
    It can optionally take a 'name' query parameter.
    """
    # Get the 'name' parameter from the URL query string, default to 'World' if not provided
    name = request.args.get('name', 'World')
    # Return a JSON response
    return jsonify({"message": f"Hello, {name}!"})


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
        phone = contact_data.get('phone', '')
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


# Route to display user information after successful login
@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """
    Route to display the user's information after successful login.
    Shows user details similar to the success page.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get the user information
            cursor.execute('SELECT * FROM Users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            
            if not user:
                # User not found, redirect to login
                return redirect('/')
            
            # Convert user to dictionary for template
            user_data = {
                "id": user["id"],
                "name": user["email"].split('@')[0].title(),  # Use email prefix as name
                "email": user["email"],
                "phone": "N/A",  # Users table doesn't have phone
                "address": "N/A",  # Users table doesn't have address
                "message": f"Welcome, {user['email']}!",
                "created_at": user["created_at"]
            }
            
            # Simple navigation (no prev/next for users)
            navigation = {
                "current_position": 1,
                "total_contacts": 1,
                "prev_contact_id": None,
                "next_contact_id": None,
                "has_prev": False,
                "has_next": False
            }
            
            return render_template('success.html', contact=user_data, navigation=navigation, is_user_profile=True)
            
    except sqlite3.Error as e:
        # On database error, redirect to login page
        return redirect('/')
    
    except Exception as e:
        # On any other error, redirect to login page
        return redirect('/')

@app.route('/success')
def success():
    """
    Route to display the success page after form submission.
    Expects contact_id as a query parameter to display the saved contact.
    Now includes navigation information for browsing between contacts.
    """
    contact_id = request.args.get('contact_id')
    
    if not contact_id:
        # If no contact_id provided, redirect to home page
        return redirect('/')
    
    try:
        contact_id = int(contact_id)
    except ValueError:
        # If contact_id is not a valid integer, redirect to home page
        return redirect('/')
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get all contacts ordered by ID to determine navigation
            cursor.execute('SELECT id FROM contacts ORDER BY id ASC')
            all_contact_ids = [row['id'] for row in cursor.fetchall()]
            
            # Check if the requested contact exists
            if contact_id not in all_contact_ids:
                return redirect('/')
            
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
        # On database error, redirect to home page
        return redirect('/')
    
    except Exception as e:
        # On any other error, redirect to home page
        return redirect('/')

# Main entry point of the application
# This block ensures the Flask app runs only when the script is executed directly
if __name__ == '__main__':
    print("Starting NetGen Contact Registration System...")
    print("Server will be available at: http://localhost:5000")
    print("Contact IDs reset to start from 1 for this session")
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
        print("Contact IDs will reset to 1 on next startup")
