#!/usr/bin/env python3
"""
Reset processing mockup jobs back to pending so they can be reprocessed
"""
import os
import sys
from dotenv import load_dotenv

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

load_dotenv()

import google.cloud.firestore as firestore

def reset_processing_jobs():
    print("🔄 Resetting processing mockup jobs to pending")
    print("=" * 40)
    
    db = firestore.Client()
    
    # Find processing mockup jobs
    mockup_jobs = db.collection('mockup_jobs').where(filter=firestore.FieldFilter('status', '==', 'processing')).get()
    
    reset_count = 0
    for job_doc in mockup_jobs:
        job_data = job_doc.to_dict()
        source_job = job_data.get('sourceJobId', 'Unknown')[:8]
        
        print(f"🔄 Resetting job {job_doc.id[:8]}... (source: {source_job}...)")
        
        # Reset to pending so job starter will pick it up again
        job_doc.reference.update({
            'status': 'pending_mockup_generation'
        })
        reset_count += 1
    
    print(f"✅ Reset {reset_count} jobs back to pending")
    print("💡 The job starter should pick these up shortly")

if __name__ == "__main__":
    reset_processing_jobs()