#!/bin/bash
# Start the backend and create a dev tunnel

echo "Starting backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"
echo ""
echo "Now create a Dev Tunnel in VS Code:"
echo "1. Open Command Palette (Cmd+Shift+P)"
echo "2. Type 'Dev Tunnels: Create Tunnel'"
echo "3. Select port 8000"
echo "4. Make it public"
echo "5. Copy the URL (e.g., https://abc123.devtunnels.ms)"
echo ""
echo "Then rebuild frontend images with:"
echo "  cd ../deployment"
echo "  ./update-frontend-images.sh"
echo ""
echo "Press Ctrl+C to stop backend"
wait $BACKEND_PID
