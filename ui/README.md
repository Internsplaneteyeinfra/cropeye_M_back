# Farm Management System - Simple UI

This is a simple HTML, CSS, and JavaScript UI for testing the Farm Management System backend. It provides a basic interface to visualize and test the functionality of the backend API.

## Features

- OTP-based authentication with real API integration
- Dashboard with statistics and recent items
- List views for users, tasks, equipment, and bookings
- Basic search functionality for each list
- Responsive design that works on mobile and desktop

## Instructions

1. Make sure the backend server is running: `python manage.py runserver`
2. Start the UI server: `cd ui && python -m http.server 8080`
3. Open your browser and navigate to: `http://localhost:8080`
4. Use the login form with a valid email from the system
5. Enter the OTP sent to that email (check console logs if using a development environment)
6. Navigate between different sections using the top menu

## API Integration

This UI is now connected to the real backend API at these endpoints:

- OTP Request: `http://localhost:8000/api/otp/`
- OTP Verification: `http://localhost:8000/api/verify-otp/`
- User Profile: `http://localhost:8000/api/users/me/`

The authentication process:
1. Enter your email and request an OTP
2. The backend will send an OTP to that email (if it exists in the system)
3. Enter the received OTP to verify
4. Upon successful verification, a JWT token is stored in localStorage
5. The token is used for all subsequent API requests

## Files

- `index.html` - The main HTML structure
- `styles.css` - All styling for the UI
- `script.js` - JavaScript for interactivity and API connections

## Testing the API

To test the backend API with this UI, you would need to:

1. Update the endpoints in `script.js` to point to your actual API endpoints
2. Replace the simulated authentication with actual API calls
3. Implement proper error handling for API responses

## Note

This is a simplified UI for testing purposes only. For a production application, consider using a more robust framework like React, Vue, or Angular, along with proper state management and API integration. 