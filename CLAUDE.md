# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The Etsy Pipeline is a **monorepo** containing an image generation and mockup creation system with:
- **Frontend**: TypeScript React app with Vite and Ant Design
- **Backend**: Python service using Temporal workflows for async processing
- **Architecture**: Event-driven system using Firestore as message queue

## Core Architecture

### Temporal Workflow System
The system is built around **Temporal workflows** for reliable async processing:

- **Job Starter** (`src/temporal/temporal_job_starter.py`): Watches Firestore collections and triggers workflows
- **Workers** (`src/temporal/temporal_worker.py`): Execute workflow activities  
- **Workflows**: Define business logic for image generation and mockup creation
  - `simple_workflow.py`: Basic image generation via BFL API
  - `mockup_generation_workflow.py`: Simple mockup creation pipeline
  - `intelligent_mockup_generation_workflow.py`: AI-powered mockup creation with object detection and perspective transformation

### Firestore Collections
The system uses Firestore as both database and message queue:
- `jobs`: Art generation requests (status: `pending_art_generation` → `processing` → `completed`/`failed`)
- `mockup_jobs`: Mockup generation requests (status: `pending_mockup_generation` → `processing` → `completed`/`failed`) 
- `costs`: Cost tracking for BFL API and Google Cloud Storage usage
- `intelligent_mockup_jobs`: AI-powered mockup placement with object detection (status: `pending` → `processing` → `completed`/`failed`)

### Service Integration
- **BFL API** (`services/bfl_api.py`): Black Forest Labs image generation
- **Google Cloud Storage** (`storage.py`): Image upload and hosting
- **Cost Tracker** (`cost_tracker.py`): Automatic cost monitoring and reporting

### Intelligent Mockup Generation
Advanced mockup system using AI for automatic artwork placement:
- **Object Detection** (`services/object_detection.py`): DETR-based region detection in mockup templates
- **Perspective Transform** (`services/perspective_transform.py`): OpenCV-based artwork warping for realistic placement
- **Intelligent Workflow** (`intelligent_mockup_generation_workflow.py`): Complete orchestration pipeline

## Development Commands

### Quick Start
```bash
# Start all services (recommended)
./start.sh

# Access URLs:
# Frontend: http://localhost:5173
# Temporal UI: http://localhost:8080
```

### Backend Development
```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run individual services
python -m src.temporal.temporal_worker
python -m src.temporal.temporal_job_starter

# Testing
python -m pytest tests/ -v
python -m pytest tests/test_object_detection.py -v  # Specific test file
python -m pytest tests/test_perspective_transform.py::TestPerspectiveTransformService::test_initialization -v  # Specific test

# Utility scripts
python scripts/create_test_job.py  # Create test job
python scripts/get_cost_summary.py  # View cost reports
python scripts/auto_cleanup.py  # Clean stuck processes
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Testing Commands
```bash
# Backend tests (run from backend/)
python -m pytest tests/test_existing_workflows_integration.py -v  # Regression tests
python -m pytest tests/test_simple_mockup_compatibility.py -v    # Compatibility tests
python -m pytest tests/test_storage_perspective_compatibility.py -v  # Storage integration

# Test object detection service
python -m pytest tests/test_object_detection.py -v

# Test perspective transformation
python -m pytest tests/test_perspective_transform.py -v

# Test intelligent mockup workflow
python -m pytest tests/test_intelligent_mockup_workflow.py -v
```

## Key Development Patterns

### Firestore Query Syntax
**Always use the new FieldFilter syntax** to avoid deprecation warnings:
```python
# ✅ Correct (new syntax)
collection.where(filter=firestore.FieldFilter('status', '==', 'pending'))

# ❌ Deprecated (old syntax)  
collection.where('status', '==', 'pending')
```

### Temporal Workflow Structure
Workflows follow a consistent pattern:
```python
@workflow.defn
class WorkflowName:
    @workflow.run
    async def run(self, job_data: Dict[str, Any]) -> str:
        # Update status to processing
        await workflow.execute_activity(update_job_status, ...)
        
        # Execute business logic activities
        result = await workflow.execute_activity(main_activity, ...)
        
        # Update final status and return
        await workflow.execute_activity(update_final_status, ...)
        return result
```

### Cost Tracking Integration
All workflows should track costs:
```python
from src.cost_tracker import CostTracker

cost_tracker = CostTracker()
# Track BFL API costs
cost = cost_tracker.log_bfl_cost(job_id, model='flux_pro', steps=28, success=True)
# Track storage costs  
cost_tracker.log_storage_cost(job_id, image_size_bytes, 'upload')
# Track intelligent mockup processing costs
cost_tracker.log_storage_cost(job_id, image_size_bytes, 'object_detection')
cost_tracker.log_storage_cost(job_id, image_size_bytes, 'perspective_transform')
```

### Service Isolation Pattern
New services must not interfere with existing ones:
- Use mock services for testing: `create_mock_detection_service()`, `create_mock_perspective_service()`
- Write isolation tests: `test_service_isolation()`, `test_no_import_side_effects()`
- Ensure backward compatibility with storage patterns

### Intelligent Mockup Workflow Pattern
The intelligent mockup workflow follows a 6-step orchestration pattern:
```python
@workflow.defn
class IntelligentMockupGenerationWorkflow:
    @workflow.run
    async def run(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Update status to processing
        await workflow.execute_activity(update_intelligent_job_status, ...)
        
        # 2. Download artwork and mockup template
        artwork_bytes, template_bytes, template_url = await workflow.execute_activity(
            download_artwork_and_template, ...)
        
        # 3. Detect suitable regions using AI
        detected_regions = await workflow.execute_activity(detect_suitable_regions, ...)
        
        # 4. Transform artwork with perspective correction
        transformed_bytes = await workflow.execute_activity(transform_artwork_to_region, ...)
        
        # 5. Compose final mockup
        final_bytes = await workflow.execute_activity(compose_final_mockup, ...)
        
        # 6. Store result and update status
        result_url = await workflow.execute_activity(store_intelligent_mockup_result, ...)
        await workflow.execute_activity(update_intelligent_job_status, ...)
```

## Project Structure Notes

### Module Organization
- `src/services/`: External API integrations and utility services
- `src/temporal/`: Temporal workflow definitions and workers
- `scripts/`: Operational utilities (testing, monitoring, cleanup)
- `tests/`: Comprehensive test suite with integration and regression tests

### Configuration Files
- `backend/requirements.txt`: Python dependencies including ML libraries (transformers, torch, opencv)
- `frontend/package.json`: Node.js dependencies with React and Ant Design
- Environment variables managed via `.env` files (not in repo)

### Log Management  
- All services log to `backend/logs/` directory
- Log files: `temporal_worker.log`, `temporal_job_starter.log`
- Frontend logs: `frontend/frontend.log`

## Important Implementation Details

### Virtual Environment Usage
The backend uses a Python virtual environment in `backend/venv/`. Always activate it before running Python commands:
```bash
source venv/bin/activate  # Required for all backend operations
```

### Temporal Server Requirements
The system requires a local Temporal server running on ports 7233 (server) and 8080 (UI). The startup script handles this automatically.

### Intelligent Mockup Pipeline Status
Implementation progress for intelligent mockup generation:
- ✅ Story 1: Dependencies and infrastructure 
- ✅ Story 2: Object detection service (DETR-based)
- ✅ Story 3: Perspective transformation service (OpenCV-based)
- ✅ Story 4: Intelligent mockup workflow (orchestration complete)
- ✅ Story 5: Temporal job starter integration (complete with known issues)
- 🚧 Story 6: Frontend Integration (reinterpreted - no API needed)

### Story 5 Completion Notes
The backend intelligent mockup generation is functional but has reliability issues:
- **Working**: Workflow triggers, status updates, AI processing pipeline
- **Issues**: gRPC message size limits, timeout errors, detection failures
- **Optimizations Created**: `*_optimized.py` files address these issues but need migration strategy

### Story 6: Frontend Integration Plan
Since the project uses Firestore-based communication (no REST APIs needed):
1. Add "Intelligent Mockup" option to MockupTab component
2. Create function to write to `intelligent_mockup_jobs` collection
3. Implement status polling for intelligent mockup jobs
4. Display results in the UI when generation completes

### Service Dependencies
- **Object Detection**: Requires `transformers`, `torch` (can use CUDA if available)
- **Perspective Transform**: Requires `opencv-python-headless`, `numpy`
- **Storage**: Requires Google Cloud credentials and Firebase config
- **BFL API**: Requires BFL API key in environment variables
- **Scipy**: Required for fallback detection in optimized version

### Known Issues & Optimizations

#### Current Issues (Original Implementation)
- gRPC message size exceeded (8MB vs 4MB limit) when passing images between activities
- Activity timeouts during AI model processing (especially object detection)
- "No suitable regions detected" errors with high confidence thresholds
- Lack of fallback options when AI detection fails

#### Available Optimizations
Optimized versions created but not yet in production:
- `intelligent_mockup_generation_workflow_optimized.py`: Stores intermediate images in Firebase Storage
- `object_detection_optimized.py`: Lower confidence thresholds, expanded target classes, fallback detection
- `temporal_worker_optimized.py` & `temporal_job_starter_optimized.py`: Use optimized components
- Increased timeouts: Object detection (5 min), Perspective transform (3 min)

To use optimizations: `./restart_optimized.sh` (requires careful migration to avoid workflow conflicts)

### Testing Philosophy
- **Integration Tests**: Ensure new features don't break existing workflows
- **Regression Tests**: Verify backward compatibility after changes
- **Isolation Tests**: Confirm services don't interfere with each other
- **Mock Services**: Enable fast testing without heavy dependencies
- **Workflow Tests**: Test complete end-to-end workflow execution with proper error handling
- **Compatibility Tests**: Verify all workflow types can run in parallel without conflicts

### Workflow Testing Patterns
```bash
# Test all workflows work together
python -m pytest tests/test_existing_workflows_integration.py -v

# Test specific workflow components
python -m pytest tests/test_intelligent_mockup_workflow.py::TestIntelligentMockupActivities -v

# Test workflow compatibility
python -m pytest tests/test_intelligent_mockup_workflow.py::TestWorkflowIntegration -v
```