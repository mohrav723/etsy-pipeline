#!/bin/bash

# Etsy Pipeline Startup Script
echo "🚀 Starting Etsy Pipeline..."

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down services..."
    pkill -f "temporal server start-dev"
    pkill -f "python.*temporal"
    pkill -f "npm.*dev"
    pkill -f "vite"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if Temporal CLI exists
if [ ! -f "/Users/mohitravindran/.temporalio/bin/temporal" ]; then
    echo "❌ Temporal CLI not found. Please install it first:"
    echo "curl -sSf https://temporal.download/cli.sh | sh"
    exit 1
fi

# Start Temporal server
echo "1️⃣ Starting Temporal server..."
/Users/mohitravindran/.temporalio/bin/temporal server start-dev --port 7233 --ui-port 8088 > backend/logs/temporal_server.log 2>&1 &
TEMPORAL_PID=$!

# Wait for Temporal to be ready
echo "⏳ Waiting for Temporal server to start..."
sleep 5

# Start backend worker (optimized)
echo "2️⃣ Starting Temporal worker (Optimized)..."
cd backend
source venv/bin/activate && python -m src.temporal.temporal_worker_optimized > logs/temporal_worker.log 2>&1 &
WORKER_PID=$!

# Wait a moment for worker to start
sleep 2

# Start job starter (optimized)
echo "3️⃣ Starting job starter (Optimized)..."
source venv/bin/activate && python -m src.temporal.temporal_job_starter_optimized > logs/temporal_job_starter.log 2>&1 &
JOB_STARTER_PID=$!

# Wait a moment for job starter to start
sleep 2

# Start frontend
echo "4️⃣ Starting frontend..."
cd ../frontend
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "✅ All services started!"
echo ""
echo "🌐 Frontend:    http://localhost:5173"
echo "📊 Temporal UI: http://localhost:8088"
echo ""
echo "📝 Logs are being written to:"
echo "   - backend/logs/temporal_server.log"
echo "   - backend/logs/temporal_worker.log"
echo "   - backend/logs/temporal_job_starter.log"
echo "   - frontend/frontend.log"
echo ""
echo "🧪 Test the system:"
echo "   1. Go to http://localhost:5173"
echo "   2. Generate an image and click 'Create Mockup'"
echo ""
echo "🛑 Press Ctrl+C to stop all services"

# Keep script running and wait for user to stop
while true; do
    sleep 1
done