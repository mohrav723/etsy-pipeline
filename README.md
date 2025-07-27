# Etsy Pipeline

This project is structured as a monorepo with a TypeScript + Vite frontend and a Python backend using Temporal workflows for image generation.

## Structure

- `frontend/` - Vite + TypeScript React app
- `backend/`  - Python backend with Temporal workflows for image generation

## Prerequisites

- Node.js (for frontend)
- Python 3.x (for backend)
- Temporal CLI (for workflow orchestration)

## Getting Started

### 1. Install Temporal CLI
```bash
# Install Temporal CLI if not already installed
curl -sSf https://temporal.download/cli.sh | sh
```

### 2. Start the Application

#### Quick Start (Recommended)
```bash
# Start everything with one command
./start.sh
```

#### Manual Start (Alternative)

Run these commands in separate terminals:

#### Terminal 1: Start Temporal Server
```bash
# Start Temporal development server
/Users/mohitravindran/.temporalio/bin/temporal server start-dev --port 7233 --ui-port 8080
```

#### Terminal 2: Start Backend Worker
```bash
cd backend
python temporal_worker.py
```

#### Terminal 3: Start Job Starter (Firestore Listener)
```bash
cd backend
python temporal_job_starter.py
```

#### Terminal 4: Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Temporal UI**: http://localhost:8080
- **Backend logs**: Check terminal outputs

### 4. Testing

Create a test job to verify the system works:
```bash
cd backend
python scripts/create_test_job.py
```

## How It Works

1. **Job Creation**: Frontend creates jobs in Firestore with status `pending_art_generation`
2. **Job Detection**: The job starter (`temporal_job_starter.py`) watches Firestore for new jobs
3. **Workflow Execution**: When a job is detected, a Temporal workflow is started
4. **Image Generation**: The worker (`temporal_worker.py`) processes workflows by:
   - Generating images using the BFL API
   - Uploading to Firebase Storage
   - Logging costs for both BFL API and Google Storage
   - Updating job status in Firestore

## Cost Monitoring

The system automatically tracks costs for:
- **BFL API**: Per-image generation costs (varies by model and steps)
- **Google Cloud Storage**: Storage and operation costs

### Viewing Costs
- **Frontend**: Click the "💰 Costs" tab to see real-time cost breakdowns
- **Command Line**: Run `python scripts/get_cost_summary.py` for detailed cost reports
- **JSON API**: Use `python scripts/get_cost_summary.py --json` for programmatic access

### Cost Data
- All costs are stored in Firestore `costs` collection
- Real-time updates in the frontend
- 7-day, 30-day, and monthly estimates
- Per-job cost tracking

## Stopping the Application

To stop all services:
```bash
# Stop all processes
pkill -f "temporal server start-dev"
pkill -f "python.*temporal"
pkill -f "npm.*dev"
pkill -f "vite"
``` 