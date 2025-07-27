#!/usr/bin/env python3
"""
Quick status check for mockup jobs and drafts
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

load_dotenv()

import google.cloud.firestore as firestore

def check_status():
    print("📊 Current Status Check")
    print("=" * 30)
    
    db = firestore.Client()
    
    # Check mockup jobs
    print("🔍 Mockup Jobs:")
    mockup_jobs = db.collection('mockup_jobs').order_by('createdAt', direction=firestore.Query.DESCENDING).limit(5).get()
    
    for job_doc in mockup_jobs:
        job_data = job_doc.to_dict()
        status = job_data.get('status', 'unknown')
        source_job = job_data.get('sourceJobId', 'Unknown')[:8]
        created_at = job_data.get('createdAt')
        
        if created_at and hasattr(created_at, 'timestamp'):
            time_str = datetime.fromtimestamp(created_at.timestamp()).strftime('%H:%M:%S')
        else:
            time_str = 'Unknown'
        
        status_emoji = {
            'pending_mockup_generation': '⏳',
            'processing': '🔄', 
            'completed': '✅',
            'failed': '❌'
        }.get(status, '❓')
        
        print(f"  {status_emoji} {job_doc.id[:8]}... - {status} - Source: {source_job}... - {time_str}")
    
    # Check drafts
    print("\n🎨 Draft Status:")
    drafts = db.collection('drafts').order_by('createdAt', direction=firestore.Query.DESCENDING).limit(5).get()
    
    for draft_doc in drafts:
        draft_data = draft_doc.to_dict()
        status = draft_data.get('status', 'unknown')
        mockup_name = draft_data.get('mockupName', 'Unknown')
        created_at = draft_data.get('createdAt')
        
        if created_at and hasattr(created_at, 'timestamp'):
            time_str = datetime.fromtimestamp(created_at.timestamp()).strftime('%H:%M:%S')
        else:
            time_str = 'Unknown'
        
        status_emoji = {
            'processing': '⏳',
            'completed': '✅',
            'failed': '❌'
        }.get(status, '❓')
        
        print(f"  {status_emoji} {draft_doc.id[:8]}... - {status} - {mockup_name} - {time_str}")

if __name__ == "__main__":
    check_status()