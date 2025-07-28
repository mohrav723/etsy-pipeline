#!/bin/bash

echo "🛑 Stopping current services..."

# Find and kill existing temporal worker and job starter
pkill -f "temporal_worker"
pkill -f "temporal_job_starter"

echo "⏳ Waiting for services to stop..."
sleep 2

echo "🚀 Starting optimized services..."

# Activate virtual environment
source venv/bin/activate

# Start optimized worker in background
echo "Starting optimized temporal worker..."
python -m src.temporal.temporal_worker_optimized &
WORKER_PID=$!
echo "Worker PID: $WORKER_PID"

# Wait a bit for worker to start
sleep 3

# Start optimized job starter in background
echo "Starting optimized job starter..."
python -m src.temporal.temporal_job_starter_optimized &
STARTER_PID=$!
echo "Job Starter PID: $STARTER_PID"

echo "✅ Optimized services started!"
echo "📊 Temporal UI: http://localhost:8080"
echo "🛑 Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo '🛑 Stopping services...'; kill $WORKER_PID $STARTER_PID; exit" INT

# Keep script running
wait