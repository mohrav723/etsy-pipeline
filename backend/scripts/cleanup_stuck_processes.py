#!/usr/bin/env python3
"""
Script to clean up stuck mockup generation processes
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
from google.cloud.firestore import FieldFilter

def cleanup_stuck_drafts():
    """Clean up drafts that have been processing for too long"""
    print("🔍 Checking for stuck drafts...")
    
    db = firestore.Client()
    drafts_collection = db.collection('drafts')
    
    # Get drafts that have been processing for more than 30 minutes
    cutoff_time = datetime.now() - timedelta(minutes=30)
    
    # Query for processing drafts
    processing_drafts = drafts_collection.where('status', '==', 'processing').get()
    
    stuck_count = 0
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
                print(f"❌ Found stuck draft: {draft_doc.id} (created {created_datetime})")
                
                # Mark as failed
                draft_doc.reference.update({
                    'status': 'failed',
                    'errorMessage': 'Process timed out - cleaned up by script'
                })
                stuck_count += 1
    
    print(f"✅ Cleaned up {stuck_count} stuck drafts")
    return stuck_count

def cleanup_stuck_mockup_jobs():
    """Clean up mockup jobs that have been processing for too long"""
    print("🔍 Checking for stuck mockup jobs...")
    
    db = firestore.Client()
    mockup_jobs_collection = db.collection('mockup_jobs')
    
    # Get mockup jobs that have been processing for more than 30 minutes
    cutoff_time = datetime.now() - timedelta(minutes=30)
    
    # Query for processing mockup jobs
    processing_jobs = mockup_jobs_collection.where('status', '==', 'processing').get()
    
    stuck_count = 0
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
                print(f"❌ Found stuck mockup job: {job_doc.id} (created {created_datetime})")
                
                # Mark as failed
                job_doc.reference.update({
                    'status': 'failed',
                    'errorMessage': 'Process timed out - cleaned up by script'
                })
                stuck_count += 1
    
    print(f"✅ Cleaned up {stuck_count} stuck mockup jobs")
    return stuck_count

def list_recent_drafts():
    """List recent drafts to see current status"""
    print("📋 Recent drafts status:")
    
    db = firestore.Client()
    drafts_collection = db.collection('drafts')
    
    # Get recent drafts
    recent_drafts = drafts_collection.order_by('createdAt', direction=firestore.Query.DESCENDING).limit(10).get()
    
    for draft_doc in recent_drafts:
        draft_data = draft_doc.to_dict()
        status = draft_data.get('status', 'unknown')
        mockup_name = draft_data.get('mockupName', 'Unknown')
        created_at = draft_data.get('createdAt')
        
        if created_at:
            if hasattr(created_at, 'timestamp'):
                created_datetime = datetime.fromtimestamp(created_at.timestamp())
            else:
                created_datetime = created_at.replace(tzinfo=None) if hasattr(created_at, 'replace') else created_at
            time_str = created_datetime.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = 'Unknown time'
        
        status_emoji = {
            'processing': '⏳',
            'completed': '✅',
            'failed': '❌'
        }.get(status, '❓')
        
        print(f"  {status_emoji} {draft_doc.id[:8]}... - {mockup_name} - {status} - {time_str}")

def list_recent_mockup_jobs():
    """List recent mockup jobs to see current status"""
    print("📋 Recent mockup jobs status:")
    
    db = firestore.Client()
    mockup_jobs_collection = db.collection('mockup_jobs')
    
    # Get recent mockup jobs
    recent_jobs = mockup_jobs_collection.order_by('createdAt', direction=firestore.Query.DESCENDING).limit(10).get()
    
    for job_doc in recent_jobs:
        job_data = job_doc.to_dict()
        status = job_data.get('status', 'unknown')
        source_job_id = job_data.get('sourceJobId', 'Unknown')
        created_at = job_data.get('createdAt')
        
        if created_at:
            if hasattr(created_at, 'timestamp'):
                created_datetime = datetime.fromtimestamp(created_at.timestamp())
            else:
                created_datetime = created_at.replace(tzinfo=None) if hasattr(created_at, 'replace') else created_at
            time_str = created_datetime.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = 'Unknown time'
        
        status_emoji = {
            'pending_mockup_generation': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(status, '❓')
        
        print(f"  {status_emoji} {job_doc.id[:8]}... - Source: {source_job_id[:8]}... - {status} - {time_str}")

def main():
    print("🧹 Mockup Process Cleanup Tool")
    print("=" * 40)
    
    # Show current status
    list_recent_mockup_jobs()
    print()
    list_recent_drafts()
    print()
    
    # Ask user what to do
    print("Options:")
    print("1. Clean up stuck processes (older than 30 minutes)")
    print("2. Just show status (done above)")
    print("3. Exit")
    
    choice = input("\nWhat would you like to do? (1/2/3): ").strip()
    
    if choice == "1":
        print("\n🧹 Starting cleanup...")
        stuck_jobs = cleanup_stuck_mockup_jobs()
        stuck_drafts = cleanup_stuck_drafts()
        
        total_cleaned = stuck_jobs + stuck_drafts
        if total_cleaned > 0:
            print(f"\n✅ Cleanup complete! Cleaned up {total_cleaned} stuck processes")
        else:
            print("\n✨ No stuck processes found - everything looks good!")
            
    elif choice == "2":
        print("\n✅ Status shown above")
        
    elif choice == "3":
        print("\n👋 Goodbye!")
        
    else:
        print("\n❌ Invalid choice")

if __name__ == "__main__":
    main()