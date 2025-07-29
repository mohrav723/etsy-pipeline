"""
Temporal Job Starter - Replaces your current app.py
Watches Firestore and starts Temporal workflows
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
import google.cloud.firestore as firestore
from temporalio.client import Client

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.temporal.simple_workflow import SimpleImageWorkflow
from src.temporal.intelligent_mockup_generation_workflow import IntelligentMockupGenerationWorkflow

# Load environment variables like your current worker
load_dotenv()

class TemporalJobStarter:
    def __init__(self):
        self.db = firestore.Client()
        self.temporal_client = None
        
    async def start(self):
        print("🚀 Starting Temporal Job Starter...")
        
        # Store the event loop for use in Firestore callbacks
        self.loop = asyncio.get_event_loop()
        
        # Connect to Temporal
        try:
            self.temporal_client = await Client.connect("localhost:7233")
            print("✅ Connected to Temporal server")
        except Exception as e:
            print(f"❌ Failed to connect to Temporal: {e}")
            print("💡 Make sure Temporal server is running!")
            return
        
        # Set up Firestore listeners
        # Listen for jobs
        jobs_collection_ref = self.db.collection('jobs')
        jobs_query_ref = jobs_collection_ref.where(filter=firestore.FieldFilter('status', '==', 'pending_art_generation'))
        jobs_query_ref.on_snapshot(self.handle_job_changes)
        
        # Listen for intelligent mockup jobs
        intelligent_mockup_jobs_collection_ref = self.db.collection('intelligent_mockup_jobs')
        intelligent_mockup_jobs_query_ref = intelligent_mockup_jobs_collection_ref.where(filter=firestore.FieldFilter('status', '==', 'pending'))
        intelligent_mockup_jobs_query_ref.on_snapshot(self.handle_intelligent_mockup_changes)
        
        print("🔥 Listening for Firestore changes...")
        print("📋 Watching for jobs with status: 'pending_art_generation'")
        print("🧠 Watching for intelligent_mockup_jobs with status: 'pending'")
        print("🌐 Temporal UI: http://localhost:8080")
        print("🛑 Press Ctrl+C to stop")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
    
    def handle_job_changes(self, collection_snapshot, changes, read_time):
        """Handle Firestore job changes"""
        for change in changes:
            if change.type.name == 'ADDED':
                # Schedule the async task in the main event loop
                asyncio.run_coroutine_threadsafe(
                    self.process_job(change.document),
                    self.loop
                )
    
    def handle_intelligent_mockup_changes(self, collection_snapshot, changes, read_time):
        """Handle Firestore intelligent mockup job changes"""
        for change in changes:
            if change.type.name == 'ADDED':
                # Schedule the async task in the main event loop
                asyncio.run_coroutine_threadsafe(
                    self.process_intelligent_mockup_job(change.document),
                    self.loop
                )
    
    async def process_job(self, doc_snapshot):
        """Process a single job by starting a Temporal workflow"""
        job_id = doc_snapshot.id
        job_data = doc_snapshot.to_dict()
        job_data['job_id'] = job_id  # Add job_id to data
        
        # Debug logging
        print(f"DEBUG: job_id = {job_id}")
        print(f"DEBUG: job_data keys before processing = {list(job_data.keys())}")
        print(f"DEBUG: 'job_id' in job_data = {'job_id' in job_data}")
        
        # Convert Firestore timestamps to ISO strings for JSON serialization
        if 'createdAt' in job_data and job_data['createdAt']:
            job_data['createdAt'] = job_data['createdAt'].isoformat()
        if 'updatedAt' in job_data and job_data['updatedAt']:
            job_data['updatedAt'] = job_data['updatedAt'].isoformat()
        
        print(f"\n🆕 New job detected: {job_id}")
        print(f"📝 Prompt: {job_data.get('prompt', 'No prompt')}")
        
        # Final debug check before workflow start
        print(f"DEBUG: Final job_data keys = {list(job_data.keys())}")
        print(f"DEBUG: Final 'job_id' in job_data = {'job_id' in job_data}")
        
        try:
            # Start the workflow
            handle = await self.temporal_client.start_workflow(
                SimpleImageWorkflow.run,
                job_data,
                id=f"image-gen-{job_id}",  # Unique workflow ID
                task_queue="image-generation-queue",
            )
            
            print(f"✅ Temporal workflow started: {handle.id}")
            print(f"🔗 View progress: http://localhost:8080/namespaces/default/workflows/{handle.id}")
            
        except Exception as e:
            print(f"❌ Failed to start workflow for job {job_id}: {e}")
            
            # Update job with error
            try:
                job_ref = self.db.collection('jobs').document(job_id)
                job_ref.update({
                    'status': 'error',
                    'errorMessage': f"Failed to start workflow: {str(e)}"
                })
                print(f"📝 Updated job {job_id} with error status")
            except Exception as update_error:
                print(f"❌ Failed to update job error status: {update_error}")
    
    async def process_intelligent_mockup_job(self, doc_snapshot):
        """Process an intelligent mockup job by starting the AI-powered Temporal workflow"""
        intelligent_job_id = doc_snapshot.id
        intelligent_job_data = doc_snapshot.to_dict()
        
        # Prepare data for the intelligent mockup generation workflow
        workflow_data = {
            'job_id': intelligent_job_id,
            'artwork_url': intelligent_job_data.get('artwork_url'),
            'mockup_template': intelligent_job_data.get('mockup_template'),
            'original_job_id': intelligent_job_data.get('original_job_id')
        }
        
        print(f"\n🧠 New intelligent mockup job detected: {intelligent_job_id}")
        print(f"🎨 Artwork URL: {workflow_data['artwork_url']}")
        print(f"🖼️  Mockup template: {workflow_data['mockup_template']}")
        
        try:
            # Start the intelligent mockup generation workflow
            handle = await self.temporal_client.start_workflow(
                IntelligentMockupGenerationWorkflow.run,
                workflow_data,
                id=f"intelligent-mockup-{intelligent_job_id}",  # Unique workflow ID
                task_queue="image-generation-queue",
            )
            
            print(f"✅ Intelligent mockup workflow started: {handle.id}")
            print(f"🔗 View progress: http://localhost:8080/namespaces/default/workflows/{handle.id}")
            
        except Exception as e:
            print(f"❌ Failed to start intelligent mockup workflow for {intelligent_job_id}: {e}")
            
            # Update intelligent mockup job with error
            try:
                intelligent_job_ref = self.db.collection('intelligent_mockup_jobs').document(intelligent_job_id)
                intelligent_job_ref.update({
                    'status': 'failed',
                    'error_message': f"Failed to start workflow: {str(e)}"
                })
                print(f"📝 Updated intelligent mockup job {intelligent_job_id} with error status")
            except Exception as update_error:
                print(f"❌ Failed to update intelligent mockup job error status: {update_error}")

async def main():
    starter = TemporalJobStarter()
    await starter.start()

if __name__ == "__main__":
    print("🎯 Temporal Job Starter - Replaces backend/app.py")
    print("=" * 50)
    asyncio.run(main())