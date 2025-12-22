

## Quick Start Script Features:

**Commands:**
- `./dev-restart.sh` or `./dev-restart.sh all` - Restart both backend and frontend
- `./dev-restart.sh backend` - Restart only backend
- `./dev-restart.sh frontend` - Restart only frontend  
- `./dev-restart.sh stop` - Stop all services
- `./dev-restart.sh status` - Check running status
- `./dev-restart.sh logs backend` - Tail backend logs
- `./dev-restart.sh logs frontend` - Tail frontend logs

**What it does:**
- Automatically stops existing processes on ports 8000 (backend) and 5173 (frontend)
- Starts backend (FastAPI/uvicorn) on http://localhost:8000
- Starts frontend (Vite/React) on http://localhost:5173
- Runs both in background with log files
- Color-coded output for easy reading
- Shows API docs link at http://localhost:8000/docs
- Tracks PIDs for easy process management

**Usage:**
```bash
cd frontend-react
./dev-restart.sh          # Restart everything
./dev-restart.sh backend  # Just backend
./dev-restart.sh status   # Check what's running
```

The logs are saved to:
- Backend: `backend/backend.log`
- Frontend: `frontend.log`

This should significantly speed up your testing workflow! 🚀

