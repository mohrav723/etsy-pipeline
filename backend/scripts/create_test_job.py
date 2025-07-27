"""
Create a test job in Firestore to test the complete Temporal flow
"""
from dotenv import load_dotenv
import google.cloud.firestore as firestore
from datetime import datetime

load_dotenv()

def create_test_job():
    """Create a test job that the Temporal system will pick up"""
    db = firestore.Client()
    
    # Create a test job
    test_job = {
        'status': 'pending_art_generation',
        'prompt': 'A beautiful mountain sunset with vibrant colors',
        'createdAt': firestore.SERVER_TIMESTAMP,
        'aspectRatio': '16:9',
        'steps': 10,  # Low steps for quick test
        'guidance': 3.0,
        'seed': 42,
        'promptUpsampling': False,
        'safetyTolerance': 2,
        'generationCount': 0,
    }
    
    # Add to Firestore
    doc_ref = db.collection('jobs').add(test_job)
    job_id = doc_ref[1].id
    
    print(f"✅ Test job created: {job_id}")
    print(f"📝 Prompt: {test_job['prompt']}")
    print(f"📊 Watch progress at: http://localhost:8080")
    print(f"🎯 The Temporal job starter should pick this up automatically!")
    
    return job_id

if __name__ == "__main__":
    print("🧪 Creating test job for Temporal...")
    create_test_job()