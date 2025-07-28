# Development Guide

## Setup

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- Temporal server (auto-started by scripts)
- Google Cloud credentials
- Firebase project configuration

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd etsy-pipeline/backend
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Always activate before working
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create `.env` file with:
   ```env
   BFL_API_KEY=your-bfl-api-key
   GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
   ```

5. **Firebase Setup**
   - Add Firebase config to environment
   - Ensure Firestore collections are created
   - Set up appropriate security rules

## Running Services

### Quick Start (Recommended)
```bash
# From project root
./start.sh

# This starts:
# - Temporal server (port 7233)
# - Temporal UI (port 8080)
# - Backend worker
# - Job starter
# - Frontend dev server (port 5173)
```

### Individual Services

**Temporal Worker:**
```bash
cd backend
source venv/bin/activate
python -m src.temporal.temporal_worker
```

**Job Starter:**
```bash
cd backend
source venv/bin/activate
python -m src.temporal.temporal_job_starter
```

**Cost Summary:**
```bash
python scripts/get_cost_summary.py
```

### Using Optimized Services
```bash
# For intelligent mockup with fixes
./backend/restart_optimized.sh
```

## Testing

### Running Tests

**All Tests:**
```bash
cd backend
python -m pytest tests/ -v
```

**Specific Test Files:**
```bash
# Object detection tests
python -m pytest tests/test_object_detection.py -v

# Perspective transform tests
python -m pytest tests/test_perspective_transform.py -v

# Workflow integration tests
python -m pytest tests/test_intelligent_mockup_workflow.py -v
```

**Specific Test Functions:**
```bash
python -m pytest tests/test_perspective_transform.py::TestPerspectiveTransformService::test_initialization -v
```

### Test Categories

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test service interactions
3. **Regression Tests**: Ensure backward compatibility
4. **Isolation Tests**: Verify no service interference

### Creating Test Jobs

**Simple Art Generation:**
```bash
python scripts/create_test_job.py
```

**Intelligent Mockup Test:**
```bash
python scripts/create_real_intelligent_job.py
```

### Mock Services

Use mock services for testing without heavy dependencies:

```python
from src.services.object_detection import create_mock_detection_service
from src.services.perspective_transform import create_mock_perspective_service

mock_detection = create_mock_detection_service()
mock_transform = create_mock_perspective_service()
```

## Code Style & Patterns

### Python Code Style

**Imports:**
```python
# Standard library
import os
import json
from typing import Dict, List, Optional

# Third-party
import numpy as np
from PIL import Image

# Local
from src.services.storage import upload_image
from src.cost_tracker import CostTracker
```

**Function Signatures:**
```python
def process_image(
    image_path: str,
    options: Optional[Dict[str, Any]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Process an image with given options.
    
    Args:
        image_path: Path to the image file
        options: Optional processing options
        
    Returns:
        Tuple of (result_url, metadata)
    """
```

### Temporal Workflow Patterns

**Activity Definition:**
```python
@activity.defn
async def process_artwork(
    artwork_url: str,
    config: Dict[str, Any]
) -> str:
    # Download image
    # Process with error handling
    # Upload result
    # Return URL
```

**Workflow Structure:**
```python
@workflow.defn
class IntelligentMockupWorkflow:
    @workflow.run
    async def run(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        # Update status to processing
        await workflow.execute_activity(
            update_job_status,
            args=[job_data["job_id"], {"status": "processing"}],
            start_to_close_timeout=timedelta(seconds=30)
        )
        
        try:
            # Execute main logic
            result = await workflow.execute_activity(
                main_processing_activity,
                args=[job_data],
                start_to_close_timeout=timedelta(minutes=5)
            )
            
            # Update success status
            await workflow.execute_activity(
                update_job_status,
                args=[job_data["job_id"], {"status": "completed", "result": result}],
                start_to_close_timeout=timedelta(seconds=30)
            )
            
            return {"status": "success", "result": result}
            
        except Exception as e:
            # Handle failure
            await workflow.execute_activity(
                update_job_status,
                args=[job_data["job_id"], {"status": "failed", "error": str(e)}],
                start_to_close_timeout=timedelta(seconds=30)
            )
            raise
```

### Firestore Query Patterns

**Always use new FieldFilter syntax:**
```python
# ✅ Correct
from google.cloud.firestore import FieldFilter

query = collection.where(
    filter=FieldFilter('status', '==', 'pending')
)

# ❌ Deprecated
query = collection.where('status', '==', 'pending')
```

### Error Handling

**Service Layer:**
```python
class ServiceError(Exception):
    """Base exception for service errors"""
    pass

class DetectionError(ServiceError):
    """Raised when object detection fails"""
    pass

def detect_objects(image: Image) -> List[BoundingBox]:
    try:
        # Detection logic
        return results
    except ModelLoadError as e:
        logger.error(f"Failed to load model: {e}")
        raise DetectionError("Model initialization failed") from e
    except Exception as e:
        logger.error(f"Unexpected error in detection: {e}")
        raise ServiceError("Detection service error") from e
```

### Cost Tracking Integration

**Always track costs for external operations:**
```python
from src.cost_tracker import CostTracker

cost_tracker = CostTracker()

# Track BFL API usage
cost = cost_tracker.log_bfl_cost(
    job_id=job_id,
    model='flux_pro',
    steps=28,
    success=True
)

# Track storage operations
cost_tracker.log_storage_cost(
    job_id=job_id,
    size_bytes=image_size,
    operation='upload'
)

# Track AI processing
cost_tracker.log_storage_cost(
    job_id=job_id,
    size_bytes=image_size,
    operation='object_detection'
)
```

## Debugging

### Log Files

All services log to `backend/logs/`:
- `temporal_worker.log`: Worker activity logs
- `temporal_job_starter.log`: Job detection logs

**View logs:**
```bash
tail -f backend/logs/temporal_worker.log
tail -f backend/logs/temporal_job_starter.log
```

### Temporal UI

Access at http://localhost:8080 when running:
- View workflow executions
- Check activity failures
- Inspect workflow history
- Debug retry attempts

### Common Issues

**Model Loading Errors:**
```python
# Add to beginning of service
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
```

**Firestore Permission Errors:**
- Check service account permissions
- Verify collection security rules
- Ensure indexes are created

**Memory Issues:**
```python
# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
```

## Performance Optimization

### Profile Code
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
result = expensive_operation()

profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats(10)  # Top 10 time consumers
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Your code here
    pass
```

### Optimize Image Processing
```python
# Use PIL's thumbnail for quick resize
image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

# Process in chunks for large images
def process_large_image(image_path):
    with Image.open(image_path) as img:
        # Process tiles instead of full image
        for tile in image_tiles(img, tile_size=512):
            process_tile(tile)
```

## Deployment Considerations

### Production Checklist
- [ ] Environment variables configured
- [ ] Proper logging levels set
- [ ] Error alerting configured
- [ ] Cost tracking enabled
- [ ] Security rules updated
- [ ] Indexes created in Firestore
- [ ] SSL certificates valid
- [ ] Backup strategy in place

### Scaling Considerations
- Multiple worker instances for high load
- Firestore connection pooling
- CDN for static assets
- Rate limiting on APIs
- Monitoring and alerting setup