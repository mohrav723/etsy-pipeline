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
from src.temporal.mockup_generation_workflow import MockupGenerationWorkflow

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
        jobs_query_ref = jobs_collection_ref.where('status', '==', 'pending_art_generation')
        jobs_query_ref.on_snapshot(self.handle_job_changes)
        
        # Listen for mockup jobs
        mockup_jobs_collection_ref = self.db.collection('mockup_jobs')
        mockup_jobs_query_ref = mockup_jobs_collection_ref.where('status', '==', 'pending_mockup_generation')
        mockup_jobs_query_ref.on_snapshot(self.handle_mockup_changes)
        
        print("🔥 Listening for Firestore changes...")
        print("📋 Watching for jobs with status: 'pending_art_generation'")
        print("🎨 Watching for mockup_jobs with status: 'pending_mockup_generation'")
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
    
    def handle_mockup_changes(self, collection_snapshot, changes, read_time):
        """Handle Firestore mockup job changes"""
        for change in changes:
            if change.type.name == 'ADDED':
                # Schedule the async task in the main event loop
                asyncio.run_coroutine_threadsafe(
                    self.process_mockup_job(change.document),
                    self.loop
                )
    
    async def process_job(self, doc_snapshot):
        """Process a single job by starting a Temporal workflow"""
        job_id = doc_snapshot.id
        job_data = doc_snapshot.to_dict()
        job_data['job_id'] = job_id  # Add job_id to data
        
        print(f"\n🆕 New job detected: {job_id}")
        print(f"📝 Prompt: {job_data.get('prompt', 'No prompt')}")
        
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
    
    async def process_mockup_job(self, doc_snapshot):
        """Process a mockup job by starting a Temporal mockup generation workflow"""
        mockup_job_id = doc_snapshot.id
        mockup_job_data = doc_snapshot.to_dict()
        
        # Prepare data for the mockup generation workflow
        workflow_data = {
            'source_job_id': mockup_job_data.get('sourceJobId'),
            'source_image_url': mockup_job_data.get('sourceImageUrl'),
            'source_prompt': mockup_job_data.get('sourcePrompt', ''),
            'mockup_job_id': mockup_job_id
        }
        
        print(f"\n🎨 New mockup job detected: {mockup_job_id}")
        print(f"📝 Source Job: {workflow_data['source_job_id']}")
        
        try:
            # Start the mockup generation workflow
            handle = await self.temporal_client.start_workflow(
                MockupGenerationWorkflow.run,
                workflow_data,
                id=f"mockup-gen-{mockup_job_id}",  # Unique workflow ID
                task_queue="image-generation-queue",
            )
            
            print(f"✅ Mockup generation workflow started: {handle.id}")
            print(f"🔗 View progress: http://localhost:8080/namespaces/default/workflows/{handle.id}")
            
            # Update mockup job status to processing
            try:
                mockup_job_ref = self.db.collection('mockup_jobs').document(mockup_job_id)
                mockup_job_ref.update({'status': 'processing'})
                print(f"📝 Updated mockup job {mockup_job_id} to processing")
            except Exception as update_error:
                print(f"⚠️ Failed to update mockup job status: {update_error}")
            
        except Exception as e:
            print(f"❌ Failed to start mockup workflow for {mockup_job_id}: {e}")
            
            # Update mockup job with error
            try:
                mockup_job_ref = self.db.collection('mockup_jobs').document(mockup_job_id)
                mockup_job_ref.update({
                    'status': 'failed',
                    'errorMessage': f"Failed to start workflow: {str(e)}"
                })
                print(f"📝 Updated mockup job {mockup_job_id} with error status")
            except Exception as update_error:
                print(f"❌ Failed to update mockup job error status: {update_error}")

async def main():
    starter = TemporalJobStarter()
    await starter.start()

if __name__ == "__main__":
    print("🎯 Temporal Job Starter - Replaces backend/app.py")
    print("=" * 50)
    asyncio.run(main())