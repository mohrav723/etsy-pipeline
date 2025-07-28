"""
Optimized Temporal Job Starter with intelligent mockup improvements
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
from src.temporal.intelligent_mockup_generation_workflow_optimized import IntelligentMockupGenerationWorkflow

# Load environment variables like your current worker
load_dotenv()

class TemporalJobStarter:
    def __init__(self):
        self.db = firestore.Client()
        self.temporal_client = None
        
    async def start(self):
        print("🚀 Starting Optimized Temporal Job Starter...")
        
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
        
        # Listen for mockup jobs
        mockup_jobs_collection_ref = self.db.collection('mockup_jobs')
        mockup_jobs_query_ref = mockup_jobs_collection_ref.where(filter=firestore.FieldFilter('status', '==', 'pending_mockup_generation'))
        mockup_jobs_query_ref.on_snapshot(self.handle_mockup_changes)
        
        # Listen for intelligent mockup jobs
        intelligent_mockup_jobs_collection_ref = self.db.collection('intelligent_mockup_jobs')
        intelligent_mockup_jobs_query_ref = intelligent_mockup_jobs_collection_ref.where(filter=firestore.FieldFilter('status', '==', 'pending'))
        intelligent_mockup_jobs_query_ref.on_snapshot(self.handle_intelligent_mockup_changes)
        
        print("🔥 Listening for Firestore changes...")
        print("📋 Watching for jobs with status: 'pending_art_generation'")
        print("🎨 Watching for mockup_jobs with status: 'pending_mockup_generation'")
        print("🧠 Watching for intelligent_mockup_jobs with status: 'pending' (OPTIMIZED)")
        print("🌐 Temporal UI: http://localhost:8080")
        print("✨ Optimizations enabled for intelligent mockups")
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
    
    def handle_intelligent_mockup_changes(self, collection_snapshot, changes, read_time):
        """Handle Firestore intelligent mockup job changes"""
        for change in changes:
            if change.type.name == 'ADDED':
                # Schedule the async task in the main event loop
                asyncio.run_coroutine_threadsafe(
                    self.process_intelligent_mockup_job(change.document),
                    self.loop
                )
    
    async def process_job(self, document):
        """Process a new job document"""
        job_id = document.id
        data = document.to_dict()
        print(f"\n🎨 Processing new job: {job_id}")
        
        # Convert Firestore timestamps to strings
        for key, value in data.items():
            if hasattr(value, 'isoformat'):
                data[key] = value.isoformat()
        
        # Start the workflow
        workflow_id = f"art-gen-{job_id}"
        await self.temporal_client.start_workflow(
            SimpleImageWorkflow.run,
            data,
            id=workflow_id,
            task_queue="image-generation-queue",
        )
        print(f"✅ Started workflow: {workflow_id}")
    
    async def process_mockup_job(self, document):
        """Process a new mockup job document"""
        job_id = document.id
        data = document.to_dict()
        print(f"\n📷 Processing new mockup job: {job_id}")
        
        # Convert Firestore timestamps to strings
        for key, value in data.items():
            if hasattr(value, 'isoformat'):
                data[key] = value.isoformat()
        
        # Add the job ID to the data
        data['job_id'] = job_id
        
        # Start the workflow
        workflow_id = f"mockup-gen-{job_id}"
        await self.temporal_client.start_workflow(
            MockupGenerationWorkflow.run,
            data,
            id=workflow_id,
            task_queue="image-generation-queue",
        )
        print(f"✅ Started mockup workflow: {workflow_id}")
    
    async def process_intelligent_mockup_job(self, document):
        """Process a new intelligent mockup job document"""
        job_id = document.id
        data = document.to_dict()
        print(f"\n🧠 Processing new intelligent mockup job: {job_id} (OPTIMIZED)")
        print(f"📸 Artwork URL: {data.get('artwork_url', 'N/A')}")
        print(f"🖼️  Mockup template: {data.get('mockup_template', 'N/A')}")
        
        # Convert Firestore timestamps to strings to make them JSON serializable
        for key, value in data.items():
            if hasattr(value, 'isoformat'):
                data[key] = value.isoformat()
        
        # Add the job ID to the data if not present
        if 'job_id' not in data:
            data['job_id'] = job_id
        
        # Start the optimized workflow
        workflow_id = f"intelligent-mockup-{job_id}"
        try:
            await self.temporal_client.start_workflow(
                IntelligentMockupGenerationWorkflow.run,
                data,
                id=workflow_id,
                task_queue="image-generation-queue",
            )
            print(f"✅ Started optimized intelligent mockup workflow: {workflow_id}")
        except Exception as e:
            print(f"❌ Failed to start workflow for job {job_id}: {e}")
            # Update job status to failed
            try:
                self.db.collection('intelligent_mockup_jobs').document(job_id).update({
                    'status': 'failed',
                    'error': f'Failed to start workflow: {str(e)}'
                })
            except Exception as update_error:
                print(f"❌ Failed to update job status: {update_error}")

async def main():
    starter = TemporalJobStarter()
    await starter.start()

if __name__ == "__main__":
    asyncio.run(main())