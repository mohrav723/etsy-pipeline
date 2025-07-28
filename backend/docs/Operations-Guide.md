# Operations Guide

## Deployment

### Starting Services

**Production Start:**
```bash
# From project root
./start.sh

# Verify all services are running
ps aux | grep temporal
ps aux | grep python
```

**Using Optimized Services:**
```bash
# Deploy intelligent mockup optimizations
./backend/restart_optimized.sh
```

### Service Health Checks

**Check Temporal:**
```bash
# Temporal server
curl http://localhost:7233/health

# Temporal UI
curl http://localhost:8080
```

**Check Workers:**
```bash
# List running workflows
temporal workflow list

# Check worker status
ps aux | grep temporal_worker
ps aux | grep temporal_job_starter
```

### Monitoring

**Log Monitoring:**
```bash
# Watch worker logs
tail -f backend/logs/temporal_worker.log

# Watch job starter logs  
tail -f backend/logs/temporal_job_starter.log

# Search for errors
grep ERROR backend/logs/*.log
```

**Cost Monitoring:**
```bash
# Generate cost report
cd backend
python scripts/get_cost_summary.py

# Check specific job costs
python scripts/get_cost_summary.py --job-id <job_id>
```

## Known Issues

### gRPC Message Size Exceeded

**Problem:** Intelligent mockup workflow fails with "message larger than max (8388608 vs 4194304)"

**Root Cause:** Passing large image data between Temporal activities exceeds 4MB limit

**Solution:** Use optimized workflow that stores intermediate images:
```bash
./backend/restart_optimized.sh
```

**Prevention:** 
- Always check image sizes before processing
- Use Firebase Storage for intermediate results
- Compress images when possible

### AI Model Loading Timeouts

**Problem:** Object detection times out during first run

**Root Cause:** DETR model download and initialization takes >2 minutes

**Solution:**
1. Pre-load models on worker startup
2. Increase activity timeouts:
   ```python
   start_to_close_timeout=timedelta(minutes=5)
   ```
3. Use mock service for development

### Detection Failures

**Problem:** "No suitable regions detected" errors

**Root Cause:** High confidence thresholds miss valid regions

**Solutions:**
1. Lower confidence threshold in config:
   ```python
   config = ObjectDetectionConfig(confidence_threshold=0.5)
   ```
2. Use optimized version with fallback detection
3. Expand target object classes

### Memory Issues

**Problem:** Worker crashes with out-of-memory errors

**Solutions:**
1. Limit concurrent workflows:
   ```python
   worker = Worker(
       client,
       task_queue="etsy-pipeline-queue",
       max_concurrent_activities=2
   )
   ```
2. Clear model cache periodically
3. Use smaller batch sizes

## Common Errors

### Firestore Errors

**"Missing or insufficient permissions"**
```bash
# Check service account
echo $GOOGLE_APPLICATION_CREDENTIALS
cat $GOOGLE_APPLICATION_CREDENTIALS | jq .project_id

# Verify Firestore rules allow access
```

**"Deadline exceeded"**
- Add indexes for frequently queried fields
- Limit query result size
- Use pagination for large datasets

### Storage Errors

**"403 Forbidden" on upload**
```bash
# Check bucket permissions
gsutil iam get gs://your-bucket

# Grant storage admin role
gsutil iam ch serviceAccount:your-sa@project.iam.gserviceaccount.com:roles/storage.admin gs://your-bucket
```

**"Bucket not found"**
- Verify bucket name in storage.py
- Check project ID matches
- Ensure bucket exists in correct region

### BFL API Errors

**"Invalid API key"**
```bash
# Verify API key is set
echo $BFL_API_KEY

# Test API directly
curl -X POST https://api.bfl.ai/generate \
  -H "Authorization: Bearer $BFL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

**"Rate limit exceeded"**
- Implement exponential backoff
- Track API usage in cost tracker
- Consider request queuing

## Performance Optimization

### Workflow Optimization

**Reduce Activity Calls:**
```python
# Bad: Multiple small activities
result1 = await workflow.execute_activity(download_image, url1)
result2 = await workflow.execute_activity(download_image, url2)

# Good: Batch operations
results = await workflow.execute_activity(download_images, [url1, url2])
```

**Parallel Execution:**
```python
# Execute independent activities in parallel
results = await workflow.gather(
    workflow.execute_activity(detect_objects, image1),
    workflow.execute_activity(detect_objects, image2)
)
```

### Database Optimization

**Index Critical Queries:**
```bash
# Create composite index for status + created_at
firebase firestore:indexes:create \
  --collection intelligent_mockup_jobs \
  --field status,ASCENDING \
  --field created_at,DESCENDING
```

**Batch Operations:**
```python
# Bad: Individual writes
for item in items:
    doc_ref.set(item)

# Good: Batch write
batch = db.batch()
for item in items:
    batch.set(doc_ref, item)
batch.commit()
```

### Image Processing Optimization

**Resize Before Processing:**
```python
# Reduce image size for AI processing
MAX_DIMENSION = 1024
image.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
```

**Use Appropriate Formats:**
```python
# PNG for transparency
if has_transparency:
    image.save(output, format='PNG', optimize=True)
# JPEG for photos
else:
    image.save(output, format='JPEG', quality=85, optimize=True)
```

## Troubleshooting

### Debug Workflow Issues

**Enable Debug Logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspect Workflow History:**
```bash
# Get workflow execution history
temporal workflow show --workflow-id <workflow_id>

# Query workflows by status
temporal workflow list --query 'ExecutionStatus="Failed"'
```

### Memory Profiling

**Monitor Memory Usage:**
```python
import tracemalloc
tracemalloc.start()

# Your code here

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 10**6:.1f} MB")
print(f"Peak memory usage: {peak / 10**6:.1f} MB")
tracemalloc.stop()
```

**Find Memory Leaks:**
```python
import gc
import objgraph

# Before operation
gc.collect()
objgraph.show_most_common_types(limit=10)

# After operation
gc.collect()
objgraph.show_growth(limit=10)
```

### Network Issues

**Test Connectivity:**
```bash
# Test Firestore
python -c "from google.cloud import firestore; db = firestore.Client(); print('Connected')"

# Test Storage
python -c "from google.cloud import storage; client = storage.Client(); print('Connected')"

# Test BFL API
curl -I https://api.bfl.ai
```

## Maintenance

### Regular Tasks

**Daily:**
- Check log files for errors
- Monitor cost tracking
- Verify all services running

**Weekly:**
- Clean up old log files
- Review cost summaries
- Check for stuck workflows

**Monthly:**
- Update dependencies
- Review and optimize indexes
- Audit security rules

### Cleanup Scripts

**Clean Stuck Jobs:**
```python
# scripts/cleanup_stuck_jobs.py
import firebase_admin
from firebase_admin import firestore
from datetime import datetime, timedelta

db = firestore.client()

# Find jobs stuck in processing for >1 hour
cutoff = datetime.now() - timedelta(hours=1)
stuck_jobs = db.collection('intelligent_mockup_jobs')\
    .where('status', '==', 'processing')\
    .where('processing_started_at', '<', cutoff)\
    .get()

for job in stuck_jobs:
    job.reference.update({
        'status': 'failed',
        'error_message': 'Job timeout - stuck in processing'
    })
```

**Archive Old Jobs:**
```python
# Archive completed jobs older than 30 days
cutoff = datetime.now() - timedelta(days=30)
old_jobs = db.collection('intelligent_mockup_jobs')\
    .where('status', 'in', ['completed', 'failed'])\
    .where('created_at', '<', cutoff)\
    .get()

for job in old_jobs:
    # Archive to cold storage
    archive_job(job.to_dict())
    job.reference.delete()
```

### Backup Strategy

**Firestore Backup:**
```bash
# Export Firestore data
gcloud firestore export gs://your-backup-bucket/firestore-backup

# Schedule daily exports
gcloud scheduler jobs create app-engine backup-firestore \
    --schedule="0 2 * * *" \
    --time-zone="America/Los_Angeles"
```

**Code Backup:**
- Use Git tags for releases
- Maintain version history
- Document deployment procedures

## Security

### API Security

**Rate Limiting:**
```python
from functools import wraps
from time import time

def rate_limit(calls_per_minute):
    def decorator(func):
        last_called = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"{args}{kwargs}"
            now = time()
            
            if key in last_called:
                elapsed = now - last_called[key]
                if elapsed < 60 / calls_per_minute:
                    raise Exception("Rate limit exceeded")
            
            last_called[key] = now
            return func(*args, **kwargs)
        
        return wrapper
    return decorator
```

**Input Validation:**
```python
def validate_image_url(url: str) -> bool:
    # Validate URL format
    # Check allowed domains
    # Verify image content type
    pass
```

### Access Control

**Service Account Permissions:**
- Minimal required permissions
- Separate accounts for different services
- Regular permission audits

**Firestore Security Rules:**
```javascript
// Only allow backend service to modify jobs
match /intelligent_mockup_jobs/{job} {
  allow read: if request.auth != null;
  allow write: if request.auth.token.admin == true;
}
```