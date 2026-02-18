#!/bin/bash

# Kill any existing processes on ports 8000 (API) and 5173 (Web)
echo "Stopping existing services..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Activate Virtual Environment
source .venv/bin/activate

# Create log files
touch backend.log frontend.log

# Start Backend
echo "Starting Backend API (Port 8000)..."
export PYTHONPATH=$PYTHONPATH:$(pwd)/apps/api
nohup python -m uvicorn app.main:app --app-dir apps/api --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

# Start Frontend
echo "Starting Frontend Web App (Port 5173)..."
cd apps/web
nohup npm run dev -- --host > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID $FRONTEND_PID"

echo "------------------------------------------------"
echo "Talisman Development Environment Restored!"
echo "Backend: http://localhost:8000/api/health"
echo "Frontend: http://localhost:5173"
echo "Logs: backend.log, frontend.log"
echo "------------------------------------------------"
