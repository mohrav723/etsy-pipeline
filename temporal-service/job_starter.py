"""
Service that watches Firestore and starts Temporal workflows
This replaces the Firestore listener in your current worker
"""
import asyncio
import google.cloud.firestore as firestore
from temporalio.client import Client
from simple_workflow import SimpleImageWorkflow

class TemporalJobStarter:
    def __init__(self):
        self.db = firestore.Client()
        self.temporal_client = None
        
    async def start(self):
        # Connect to Temporal
        self.temporal_client = await Client.connect("localhost:7233")
        
        # Set up Firestore listener
        collection_ref = self.db.collection('jobs')
        query_ref = collection_ref.where('status', '==', 'pending_art_generation')
        
        # Start listening for new jobs
        query_ref.on_snapshot(self.handle_job_changes)
        
        print("🔥 Job starter listening for Firestore changes...")
        print("📋 Watching for jobs with status: 'pending_art_generation'")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    def handle_job_changes(self, collection_snapshot, changes, read_time):
        """Handle Firestore changes - same as your current callback"""
        for change in changes:
            if change.type.name == 'ADDED':
                asyncio.create_task(self.process_job(change.document))
    
    async def process_job(self, doc_snapshot):
        """Process a single job by starting a Temporal workflow"""
        job_id = doc_snapshot.id
        job_data = doc_snapshot.to_dict()
        job_data['job_id'] = job_id  # Add job_id to data
        
        print(f"🆕 Starting Temporal workflow for job {job_id}")
        
        try:
            # Start the workflow
            handle = await self.temporal_client.start_workflow(
                SimpleImageWorkflow.run,
                job_data,
                id=f"image-gen-{job_id}",  # Unique workflow ID
                task_queue="image-generation-queue",
            )
            
            print(f"✅ Workflow started for job {job_id}: {handle.id}")
            
        except Exception as e:
            print(f"❌ Failed to start workflow for job {job_id}: {e}")
            
            # Update job with error
            try:
                job_ref = self.db.collection('jobs').document(job_id)
                job_ref.update({
                    'status': 'error',
                    'errorMessage': f"Failed to start workflow: {str(e)}"
                })
            except:
                pass  # Don't fail if we can't update the error

async def main():
    starter = TemporalJobStarter()
    await starter.start()

if __name__ == "__main__":
    asyncio.run(main())