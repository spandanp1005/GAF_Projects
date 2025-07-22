# Import necessary modules from Flask
from flask import Flask, render_template, jsonify, request
import os

# Create a Flask web application instance
app = Flask(__name__)

# Define the directory where HTML templates will be stored
# This assumes 'templates' folder is in the same directory as this Python script
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app.template_folder = template_dir

# Route to serve the index.html file
# When a user accesses the root URL '/', this function will be called
@app.route('/')
def index():
    """
    Renders the index.html template.
    """
    # render_template looks for 'index.html' in the configured template folder
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
def savecontact(contactinfo: str):
    UserContactInfo = request.args.get('name', 'World') #left off on this and read on it, recieve in JSON and extract into a database, SQL lite as a database

# Main entry point of the application
# This block ensures the Flask app runs only when the script is executed directly
if __name__ == '__main__':
    # Run the Flask application
    # debug=True allows for automatic reloading on code changes and provides a debugger
    # host='0.0.0.0' makes the server accessible from any IP address, useful for hosting
    app.run(debug=True, host='0.0.0.0', port=5000)
