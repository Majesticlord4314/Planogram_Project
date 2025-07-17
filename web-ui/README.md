# Planogram Web UI

This is the web UI for the Planogram Optimization System. It consists of a Flask backend and a React frontend.

## Project Structure

- `backend/`: Flask backend with WebSocket support
- `frontend/`: React frontend with TypeScript

## Running the Application

### Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Flask server:
   ```
   python app.py
   ```

The backend will be available at http://localhost:5000.

### Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm start
   ```

The frontend will be available at http://localhost:3000.

## WebSocket Testing

You can test the WebSocket connection using the built-in test page:

1. Start the backend server
2. Open http://localhost:5000/socket-test in your browser

## Docker Deployment

You can also run the entire application using Docker Compose:

```
docker-compose up
```

This will start both the backend and frontend services.

## Troubleshooting

If you encounter connection issues:

1. Make sure both the backend and frontend are running
2. Check that the REACT_APP_API_URL environment variable is set correctly in the frontend
3. Verify that CORS is properly configured in the backend
4. Check the browser console for any error messages