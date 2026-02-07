#!/bin/bash

# Talisman Healthcare Analytics - Quick Start Script

echo "🏥 Talisman Healthcare Analytics - Setup"
echo "=========================================="

# Backend Setup
echo ""
echo "📦 Setting up Backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "✅ Backend dependencies installed!"

# Frontend Setup
echo ""
echo "📦 Setting up Frontend..."
cd ../frontend
npm install

echo ""
echo "✅ Frontend dependencies installed!"

echo ""
echo "=========================================="
echo "🎉 Setup Complete!"
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then visit: http://localhost:5173"
echo "=========================================="
