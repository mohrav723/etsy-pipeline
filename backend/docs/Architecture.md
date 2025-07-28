# Backend Architecture

## Overview

The Etsy Pipeline backend is a Python-based service built on Temporal workflows for reliable asynchronous processing. It handles image generation, mockup creation, and cost tracking through an event-driven architecture using Firestore as both database and message queue.

## Directory Structure

```
backend/
├── src/                          # Source code
│   ├── services/                 # External service integrations
│   │   ├── bfl_api.py           # BFL API client
│   │   ├── object_detection.py  # AI object detection service
│   │   └── perspective_transform.py # Image transformation service
│   ├── temporal/                 # Temporal workflow components
│   │   ├── simple_workflow.py   # Main workflow definition
│   │   ├── mockup_generation_workflow.py # Simple mockup workflow
│   │   ├── intelligent_mockup_generation_workflow.py # AI mockup workflow
│   │   ├── temporal_worker.py   # Temporal worker process
│   │   └── temporal_job_starter.py # Firestore listener
│   ├── cost_tracker.py          # Cost tracking and monitoring
│   └── storage.py               # Google Cloud Storage utilities
├── scripts/                      # Utility scripts
│   ├── create_test_job.py       # Create test jobs for testing
│   └── get_cost_summary.py      # Generate cost reports
├── tests/                        # Test files
├── logs/                         # Log files (gitignored)
├── venv/                         # Python virtual environment
└── requirements.txt              # Python dependencies
```

## Core Components

### Temporal Workflow System

The system uses Temporal for reliable distributed workflow execution:

1. **Job Starter** (`temporal_job_starter.py`)
   - Monitors Firestore collections for new jobs
   - Triggers appropriate workflows based on job type
   - Handles multiple collections: `jobs`, `mockup_jobs`, `intelligent_mockup_jobs`

2. **Worker** (`temporal_worker.py`)
   - Executes workflow activities
   - Manages concurrent workflow processing
   - Handles all workflow types in a single worker instance

3. **Workflows**
   - `simple_workflow.py`: Basic image generation via BFL API
   - `mockup_generation_workflow.py`: Simple mockup overlay
   - `intelligent_mockup_generation_workflow.py`: AI-powered mockup placement

### Service Layer

#### BFL API Integration (`services/bfl_api.py`)
- Handles image generation requests to Black Forest Labs
- Supports multiple models (flux_pro, flux_dev, etc.)
- Includes retry logic and error handling

#### Object Detection Service (`services/object_detection.py`)
- Uses DETR model for detecting suitable regions in mockups
- Identifies frames, screens, and other placement areas
- Configurable confidence thresholds

#### Perspective Transform Service (`services/perspective_transform.py`)
- OpenCV-based image warping and transformation
- Creates realistic perspective effects
- Handles artwork composition onto mockups

### Storage Integration (`storage.py`)
- Google Cloud Storage operations
- Image upload and retrieval
- Public URL generation

### Cost Tracking (`cost_tracker.py`)
- Tracks BFL API usage costs
- Monitors storage operations
- Generates cost summaries and reports

## Data Flow

### Simple Image Generation
1. Job created in `jobs` collection with status `pending_art_generation`
2. Job starter detects and triggers `SimpleImageWorkflow`
3. Workflow calls BFL API to generate image
4. Result stored in GCS, URL saved to job document
5. Status updated to `completed` or `failed`

### Mockup Generation
1. Job created in `mockup_jobs` collection with status `pending_mockup_generation`
2. Job starter triggers `MockupGenerationWorkflow`
3. Workflow downloads artwork and mockup template
4. Overlays artwork onto mockup using PIL
5. Stores result and updates status

### Intelligent Mockup Generation
1. Job created in `intelligent_mockup_jobs` collection with status `pending`
2. Job starter triggers `IntelligentMockupGenerationWorkflow`
3. Workflow orchestrates:
   - Download artwork and template
   - Detect suitable regions using AI
   - Transform artwork with perspective correction
   - Compose final mockup
   - Store result
4. Status updated with result URL and metadata

## Firestore Collections

### `jobs` Collection
- Art generation requests
- Status flow: `pending_art_generation` → `processing` → `completed`/`failed`
- Fields: `job_id`, `prompt`, `model`, `status`, `result_url`, `created_at`

### `mockup_jobs` Collection  
- Simple mockup generation requests
- Status flow: `pending_mockup_generation` → `processing` → `completed`/`failed`
- Fields: `job_id`, `artwork_job_id`, `mockup_id`, `status`, `result_url`

### `intelligent_mockup_jobs` Collection
- AI-powered mockup placement requests
- Status flow: `pending` → `processing` → `completed`/`failed`
- Fields: `job_id`, `artwork_url`, `mockup_template`, `status`, `result_url`, `detection_confidence`, `detected_objects`

### `costs` Collection
- Cost tracking records
- Types: `bfl_generation`, `storage_upload`, `object_detection`, `perspective_transform`
- Fields: `job_id`, `cost_type`, `amount`, `timestamp`, `metadata`

## Security & Configuration

### Environment Variables
- `BFL_API_KEY`: Black Forest Labs API key
- `GOOGLE_APPLICATION_CREDENTIALS`: GCS service account
- Firebase configuration for Firestore access

### Error Handling
- Comprehensive try-catch blocks in all activities
- Retry policies with exponential backoff
- Graceful degradation for non-critical failures
- Detailed error logging and status updates

## Performance Considerations

### Scalability
- Temporal handles workflow orchestration and scaling
- Worker processes can be scaled horizontally
- Firestore queries use indexed fields for performance

### Optimization
- Lazy loading of ML models
- Image size limits to prevent memory issues
- Batch processing capabilities for multiple jobs
- Connection pooling for external services

### Monitoring
- Comprehensive logging to `logs/` directory
- Cost tracking for budget monitoring
- Temporal UI for workflow visibility
- Status tracking in Firestore documents