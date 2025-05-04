#!/bin/bash

# Set environment variables for local development
export ENVIRONMENT=development
export USE_SQLITE=true
export DEBUG=true

# Start the backend server
echo "Starting backend server..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Start the frontend
echo "Starting frontend..."
cd frontend
streamlit run streamlit_app.py &
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
echo "Application is running!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo "Press Ctrl+C to stop"
wait 