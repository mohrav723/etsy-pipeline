# Backend Structure

## Directory Organization

```
backend/
├── src/                          # Source code
│   ├── services/                 # External service integrations
│   │   └── bfl_api.py           # BFL API client
│   ├── temporal/                 # Temporal workflow components
│   │   ├── simple_workflow.py   # Main workflow definition
│   │   ├── temporal_worker.py   # Temporal worker process
│   │   └── temporal_job_starter.py # Firestore listener
│   ├── cost_tracker.py          # Cost tracking and monitoring
│   └── storage.py               # Google Cloud Storage utilities
├── scripts/                      # Utility scripts
│   ├── create_test_job.py       # Create test jobs for testing
│   └── get_cost_summary.py      # Generate cost reports
├── tests/                        # Test files
│   ├── test_api.py              # API integration tests
│   └── test_workflow.py         # Workflow tests
├── logs/                         # Log files (gitignored)
│   ├── temporal_worker.log      # Worker process logs
│   └── temporal_job_starter.log # Job starter logs
├── venv/                         # Python virtual environment
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
└── db.json                       # Local database file
```

## Key Components

### Core Services (`src/`)
- **`services/bfl_api.py`**: Black Forest Labs API integration
- **`storage.py`**: Google Cloud Storage operations
- **`cost_tracker.py`**: Cost monitoring and tracking

### Temporal Workflow (`src/temporal/`)
- **`simple_workflow.py`**: Main image generation workflow
- **`temporal_worker.py`**: Worker process that executes workflows
- **`temporal_job_starter.py`**: Watches Firestore and starts workflows

### Utilities (`scripts/`)
- **`create_test_job.py`**: Create test jobs for development
- **`get_cost_summary.py`**: Generate cost reports and summaries
- Historical data import scripts

### Testing (`tests/`)
- API integration tests
- Workflow tests

## Running Components

### Start Everything
```bash
# From project root
./start.sh
```

### Individual Components
```bash
# Worker
python -m src.temporal.temporal_worker

# Job Starter
python -m src.temporal.temporal_job_starter

# Cost Summary
python scripts/get_cost_summary.py

# Test Job
python scripts/create_test_job.py
```

## Logs

All log files are stored in `logs/` directory:
- Worker logs: `logs/temporal_worker.log`
- Job starter logs: `logs/temporal_job_starter.log`

## Development

1. **Virtual Environment**: All dependencies in `venv/`
2. **Environment Variables**: Configure in `.env` file
3. **Testing**: Run tests from `tests/` directory
4. **Scripts**: Utility scripts in `scripts/` directory