#!/usr/bin/env python3
"""
Auto cleanup script for stuck mockup generation processes
"""
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

load_dotenv()

import google.cloud.firestore as firestore

def auto_cleanup():
    """Automatically clean up stuck processes"""
    print("🧹 Auto Cleanup - Mockup Process Cleanup")
    print("=" * 40)
    
    db = firestore.Client()
    total_cleaned = 0
    
    # Clean up stuck drafts (older than 20 minutes)
    print("🔍 Checking for stuck drafts...")
    cutoff_time = datetime.now() - timedelta(minutes=20)
    
    drafts_collection = db.collection('drafts')
    processing_drafts = drafts_collection.where('status', '==', 'processing').get()
    
    stuck_drafts = 0
    for draft_doc in processing_drafts:
        draft_data = draft_doc.to_dict()
        created_at = draft_data.get('createdAt')
        
        if created_at:
            # Convert Firestore timestamp to datetime
            if hasattr(created_at, 'timestamp'):
                created_datetime = datetime.fromtimestamp(created_at.timestamp())
            else:
                created_datetime = created_at.replace(tzinfo=None) if hasattr(created_at, 'replace') else created_at
            
            if created_datetime < cutoff_time:
                mockup_name = draft_data.get('mockupName', 'Unknown')
                print(f"❌ Cleaning stuck draft: {draft_doc.id[:8]}... ({mockup_name}) - stuck since {created_datetime}")
                
                # Mark as failed
                draft_doc.reference.update({
                    'status': 'failed',
                    'errorMessage': 'Process timed out after 20+ minutes - auto cleaned'
                })
                stuck_drafts += 1
    
    print(f"✅ Cleaned up {stuck_drafts} stuck drafts")
    total_cleaned += stuck_drafts
    
    # Clean up stuck mockup jobs (older than 30 minutes)
    print("🔍 Checking for stuck mockup jobs...")
    cutoff_time = datetime.now() - timedelta(minutes=30)
    
    mockup_jobs_collection = db.collection('mockup_jobs')
    processing_jobs = mockup_jobs_collection.where('status', '==', 'processing').get()
    
    stuck_jobs = 0
    for job_doc in processing_jobs:
        job_data = job_doc.to_dict()
        created_at = job_data.get('createdAt')
        
        if created_at:
            # Convert Firestore timestamp to datetime
            if hasattr(created_at, 'timestamp'):
                created_datetime = datetime.fromtimestamp(created_at.timestamp())
            else:
                created_datetime = created_at.replace(tzinfo=None) if hasattr(created_at, 'replace') else created_at
            
            if created_datetime < cutoff_time:
                source_job = job_data.get('sourceJobId', 'Unknown')
                print(f"❌ Cleaning stuck mockup job: {job_doc.id[:8]}... (source: {source_job[:8]}...) - stuck since {created_datetime}")
                
                # Mark as failed
                job_doc.reference.update({
                    'status': 'failed',
                    'errorMessage': 'Process timed out after 30+ minutes - auto cleaned'
                })
                stuck_jobs += 1
    
    print(f"✅ Cleaned up {stuck_jobs} stuck mockup jobs")
    total_cleaned += stuck_jobs
    
    # Also clean up old pending mockup generation jobs (older than 1 hour)
    print("🔍 Checking for old pending mockup jobs...")
    cutoff_time = datetime.now() - timedelta(hours=1)
    
    pending_jobs = mockup_jobs_collection.where('status', '==', 'pending_mockup_generation').get()
    
    old_pending = 0
    for job_doc in pending_jobs:
        job_data = job_doc.to_dict()
        created_at = job_data.get('createdAt')
        
        if created_at:
            # Convert Firestore timestamp to datetime
            if hasattr(created_at, 'timestamp'):
                created_datetime = datetime.fromtimestamp(created_at.timestamp())
            else:
                created_datetime = created_at.replace(tzinfo=None) if hasattr(created_at, 'replace') else created_at
            
            if created_datetime < cutoff_time:
                source_job = job_data.get('sourceJobId', 'Unknown')
                print(f"❌ Cleaning old pending job: {job_doc.id[:8]}... (source: {source_job[:8]}...) - pending since {created_datetime}")
                
                # Mark as failed
                job_doc.reference.update({
                    'status': 'failed',
                    'errorMessage': 'Job was pending for over 1 hour - auto cleaned'
                })
                old_pending += 1
    
    print(f"✅ Cleaned up {old_pending} old pending jobs")
    total_cleaned += old_pending
    
    print("=" * 40)
    if total_cleaned > 0:
        print(f"🎉 Cleanup complete! Cleaned up {total_cleaned} total stuck processes")
        print("💡 These processes should now show as 'failed' in the Drafts tab")
    else:
        print("✨ No stuck processes found - everything looks good!")

if __name__ == "__main__":
    auto_cleanup()