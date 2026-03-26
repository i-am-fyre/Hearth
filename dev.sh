#!/bin/bash

# Exit on error
set -e

# Setup cleanup on script exit
trap 'cleanup' SIGINT SIGTERM

function cleanup() {
    echo -e "\nShutting down all services..."
    kill $MKDOCS_PID $FRONTEND_PID 2>/dev/null
    sudo docker compose stop
    echo "Services stopped gracefully."
    exit 0
}

echo "======================================"
echo " Starting Hearth Dev Environment  "
echo "======================================"

# 1. Start Database and Backend via Docker
echo "[1/3] Starting Database & Backend on port 8000..."
sudo docker compose up -d

# 2. Start MkDocs Docs
echo "[2/3] Starting MkDocs on port 8001..."
if [ -f "./.venv/bin/activate" ]; then
    source ./.venv/bin/activate
fi
mkdocs serve -a 127.0.0.1:8001 > mkdocs.log 2>&1 &
MKDOCS_PID=$!

# 3. Start Frontend Svelte app
echo "[3/3] Starting Frontend on port 5173..."
cd frontend
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "======================================"
echo -e "✓ All services are running!\n"
echo "🟢 Frontend : http://localhost:5173"
echo "🔵 Backend  : http://localhost:8000"
echo "🟣 Docs     : http://localhost:8001"
echo "======================================"
echo "Logs are being written to frontend.log and mkdocs.log"
echo "Backend logs can be viewed with 'sudo docker compose logs -f'"
echo -e "\nPress [CTRL+C] to stop all services."

# Wait forever until trap catches SIGINT
wait
