import os
from dotenv import load_dotenv
import google.cloud.firestore as firestore
from google.cloud.firestore import SERVER_TIMESTAMP

# Load environment
load_dotenv()

# Connect to Firestore
db = firestore.Client()

# Create test job data
test_job_data = {
    'status': 'pending',
    'artwork_url': 'https://storage.googleapis.com/flux-image-generator.appspot.com/generated-images/A_vibrant_illustration_of_a_vintage_74e12d73-d3e5-4ecb-9c07-d659b6bb966f.png',
    'mockup_template': 'default',
    'original_job_id': 'test_original_job_123',
    'sourcePrompt': 'Test prompt for debugging',
    'createdAt': SERVER_TIMESTAMP,
    'processingStartTime': None,
    'completionTime': None,
    'error': None,
    'resultUrl': None,
    'detectedRegions': None,
}

# Add the job to Firestore
print("Creating test intelligent mockup job...")
doc_ref = db.collection('intelligent_mockup_jobs').add(test_job_data)
job_id = doc_ref[1].id
print(f"✅ Created job with ID: {job_id}")
print(f"Status: pending")
print(f"Check Temporal UI at http://localhost:8080 for workflow")
print(f"Workflow ID should be: intelligent-mockup-{job_id}")