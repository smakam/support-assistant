#!/bin/bash

# Set environment variables for production simulation
export ENVIRONMENT=production
export USE_SQLITE=false
export DEBUG=false

# Start the backend server in production mode
echo "Starting backend server in production mode..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start the frontend with production settings
echo "Starting frontend with production settings..."
cd frontend
streamlit run production_app.py &
FRONTEND_PID=$!

# Function to handle script termination
function cleanup {
  echo "Shutting down servers..."
  kill $BACKEND_PID
  kill $FRONTEND_PID
  exit
}

# Trap Ctrl+C and call cleanup
trap cleanup INT

# Keep script running
echo "Application is running in PRODUCTION MODE!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo "Press Ctrl+C to stop"
wait 