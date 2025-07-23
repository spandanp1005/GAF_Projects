# NetGen Contact Registration System - Demo Instructions

## Overview
The system now has a complete two-page flow:
1. **Main Page** (`/`) - User registration form
2. **Success Page** (`/success`) - Displays submitted information in a table

## How to Run the Application

1. Start the Flask server:
   ```bash
   python3 TestAPIV2.py
   ```

2. Open your browser and go to: `http://localhost:5000`

## User Flow

### Step 1: Fill out the Registration Form
- **Full Name** (required)
- **Email Address** (optional)
- **Phone Number** (required)
- **Address** (required)
- **Additional Message** (optional)

### Step 2: Submit the Form
- Click the "Register" button
- The form data is sent to `/api/savecontact` via AJAX
- Data is saved to SQLite database (`contacts.db`)
- User is redirected to success page

### Step 3: View Success Page
- Displays all submitted information in a beautiful table
- Shows contact ID for reference
- Includes timestamp of submission
- Has "Add Another Contact" button to return to main page
- Has "Print Information" button for printing

## Features

### Frontend Features
- Modern, responsive Bootstrap 5 design
- Form validation
- Loading states during submission
- Error handling with user feedback
- Smooth animations and hover effects

### Backend Features
- SQLite database for persistent storage
- RESTful API endpoints
- Input validation and sanitization
- Error handling with proper HTTP status codes
- Secure database operations (parameterized queries)

### API Endpoints
- `GET /` - Main registration form
- `POST /api/savecontact` - Save contact information
- `GET /api/contacts` - Retrieve all contacts (for admin use)
- `GET /success?contact_id=X` - Success page with contact details

## Database Schema
```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Testing the API Directly
```bash
# Test saving a contact
curl -X POST http://localhost:5000/api/savecontact \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "123-456-7890",
    "address": "123 Main St",
    "message": "Test message"
  }'

# Test retrieving all contacts
curl http://localhost:5000/api/contacts
```

The system is now complete with a beautiful, user-friendly interface and robust backend functionality!
