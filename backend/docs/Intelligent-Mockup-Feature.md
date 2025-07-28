# Intelligent Mockup Generation Feature

## Overview

The Intelligent Mockup Generation feature uses AI to automatically detect suitable regions in mockup templates and place artwork with realistic perspective transformation. This advanced system provides professional-quality mockups without manual positioning.

## Implementation Status

### ✅ Completed (Backend)
- **Story 1**: Dependencies and infrastructure setup
- **Story 2**: Object detection service implementation
- **Story 3**: Perspective transformation service
- **Story 4**: Intelligent mockup workflow orchestration
- **Story 5**: Temporal job starter integration

### 🚧 Pending (Frontend)
- **Story 6**: Frontend integration for user access

## Technical Architecture

### Object Detection Service

Located in `src/services/object_detection.py`, this service uses the DETR (Detection Transformer) model to identify suitable regions:

**Key Features:**
- Pre-trained model from Hugging Face (`facebook/detr-resnet-50`)
- Detects frames, screens, and other suitable surfaces
- Configurable confidence thresholds (default: 0.7)
- Returns bounding boxes with confidence scores

**Supported Object Types:**
- Picture frames
- TV/laptop/phone screens
- Books, bottles, cups
- Furniture surfaces

**Usage Example:**
```python
service = ObjectDetectionService()
regions = service.find_suitable_regions(mockup_image)
best_region = max(regions, key=lambda r: r.confidence)
```

### Perspective Transformation Service

Located in `src/services/perspective_transform.py`, this service handles realistic artwork placement:

**Key Features:**
- OpenCV-based perspective warping
- Automatic perspective calculation
- High-quality interpolation (LANCZOS4)
- Aspect ratio preservation

**Transformation Process:**
1. Calculate transformation matrix from region corners
2. Warp artwork to match perspective
3. Composite onto mockup with proper blending
4. Maintain image quality throughout

### Intelligent Mockup Workflow

The workflow (`intelligent_mockup_generation_workflow.py`) orchestrates the complete process:

**Workflow Steps:**
1. **Status Update**: Mark job as `processing`
2. **Download Assets**: Fetch artwork and mockup template
3. **Detect Regions**: Use AI to find suitable placement areas
4. **Transform Artwork**: Apply perspective transformation
5. **Compose Result**: Create final mockup image
6. **Store & Update**: Upload result and update job status

**Error Handling:**
- Graceful degradation for detection failures
- Retry policies for transient errors
- Comprehensive logging for debugging

## Firestore Schema

### `intelligent_mockup_jobs` Collection

```json
{
  "job_id": "intelligent_mockup_12345",
  "artwork_url": "https://storage.../artwork.png",
  "mockup_template": "picture_frame_01",
  "status": "completed",
  "result_url": "https://storage.../result.png",
  "created_at": "2025-01-27T10:30:00Z",
  "updated_at": "2025-01-27T10:32:15Z",
  "processing_started_at": "2025-01-27T10:30:05Z",
  "processing_completed_at": "2025-01-27T10:32:15Z",
  "detection_confidence": 0.95,
  "detected_objects": [{
    "object_type": "picture frame",
    "confidence": 0.95,
    "bounding_box": {
      "x": 100, "y": 150,
      "width": 300, "height": 400
    }
  }]
}
```

## Known Issues & Solutions

### Current Issues
1. **gRPC Message Size**: Images >4MB exceed Temporal's limit
   - **Solution**: Store intermediate images in Firebase Storage
   
2. **Processing Timeouts**: AI model loading can exceed activity timeouts
   - **Solution**: Increased timeouts (5min for detection, 3min for transform)
   
3. **Detection Failures**: Some mockups lack detectable regions
   - **Solution**: Lower confidence thresholds and fallback detection

### Optimized Versions Available

Located in `*_optimized.py` files:
- Firebase Storage for intermediate results (fixes gRPC issue)
- Extended timeouts for AI processing
- Fallback detection for generic rectangular regions
- Better error handling and recovery

**To Deploy Optimizations:**
```bash
./restart_optimized.sh
```

## Frontend Integration Plan (Story 6)

Since the system uses Firestore-based communication, the frontend integration is straightforward:

### Implementation Steps

1. **Add UI Option**
   ```typescript
   // In MockupTab component
   const mockupTypes = ['simple', 'intelligent'];
   ```

2. **Create Job Function**
   ```typescript
   const createIntelligentMockupJob = async (
     artworkUrl: string, 
     mockupTemplate: string
   ) => {
     const jobId = `intelligent-${uuidv4()}`;
     await addDoc(collection(db, 'intelligent_mockup_jobs'), {
       job_id: jobId,
       artwork_url: artworkUrl,
       mockup_template: mockupTemplate,
       status: 'pending',
       created_at: serverTimestamp()
     });
     return jobId;
   };
   ```

3. **Poll for Results**
   ```typescript
   onSnapshot(
     doc(db, 'intelligent_mockup_jobs', jobId), 
     (doc) => {
       const data = doc.data();
       if (data.status === 'completed') {
         showResult(data.result_url);
       }
     }
   );
   ```

### User Experience
- Clear "Intelligent Mockup" option
- Progress indicator during AI processing
- Graceful error handling with retry option
- Display confidence scores and detected regions

## Testing

### Backend Testing
```bash
# Unit tests
python -m pytest tests/test_object_detection.py -v
python -m pytest tests/test_perspective_transform.py -v
python -m pytest tests/test_intelligent_mockup_workflow.py -v

# Integration tests
python -m pytest tests/test_existing_workflows_integration.py -v

# Create test job
python scripts/create_real_intelligent_job.py
```

### Expected Test Flow
1. Job created with `pending` status
2. Job starter detects and triggers workflow
3. Status updates to `processing`
4. AI analyzes mockup and places artwork
5. Status updates to `completed` with result URL

## Cost Tracking

All operations are tracked in the `costs` collection:
- Object detection processing time
- Perspective transformation operations
- Storage uploads for results
- Integrated with existing cost reporting

## Performance Metrics

### Processing Times
- Object Detection: 10-30 seconds (model loading + inference)
- Perspective Transform: 1-3 seconds
- Total Workflow: 30-60 seconds typical

### Resource Usage
- Memory: 500MB-1GB during AI processing
- CPU: Spike during model inference
- GPU: Automatically used if available

## Migration Path

When ready to deploy optimizations:
1. Ensure no active workflows: `ps aux | grep temporal`
2. Stop all services: `pkill -f temporal`
3. Deploy optimized versions: `./restart_optimized.sh`
4. Monitor logs for issues
5. Test with sample jobs

## Future Enhancements

### Potential Improvements
- Multiple artwork placement in single mockup
- Style transfer for artistic effects
- 3D mockup support
- Batch processing API
- Caching for repeated templates

### Performance Optimizations
- Model quantization for faster inference
- Template-specific fine-tuning
- Edge deployment for reduced latency
- WebAssembly for client-side preview