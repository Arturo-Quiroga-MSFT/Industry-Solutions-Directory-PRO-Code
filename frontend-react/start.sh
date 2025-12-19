#!/bin/bash

# Start script for NL2SQL Chat Interface

echo "🚀 Starting NL2SQL Chat Interface..."

# Check if .env exists in backend
if [ ! -f "backend/.env" ]; then
    echo "⚠️  backend/.env not found. Copying from .env.example..."
    cp backend/.env.example backend/.env
    echo "📝 Please edit backend/.env with your credentials before continuing"
    exit 1
fi

# Start backend
echo "🔧 Starting FastAPI backend on port 8000..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to be ready..."
sleep 5

# Start frontend
echo "⚛️  Starting React frontend on port 5173..."
npm run dev &
FRONTEND_PID=$!

echo "✅ Both services started!"
echo ""
echo "📝 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services"

# Trap Ctrl+C and kill both processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait for both processes
wait
