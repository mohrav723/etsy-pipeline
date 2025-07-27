"""
Temporal worker that replaces your current backend/app.py
"""
import asyncio
import os
import sys
from temporalio.client import Client
from temporalio.worker import Worker

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.temporal.simple_workflow import SimpleImageWorkflow, generate_and_store_image, update_firestore_job
from src.temporal.mockup_generation_workflow import (
    MockupGenerationWorkflow, 
    get_available_mockups, 
    create_draft_entry, 
    generate_mockup_image, 
    update_draft_with_mockup, 
    mark_draft_failed
)

async def main():
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    
    # Create worker
    worker = Worker(
        client,
        task_queue="image-generation-queue",
        workflows=[SimpleImageWorkflow, MockupGenerationWorkflow],
        activities=[
            generate_and_store_image, 
            update_firestore_job,
            get_available_mockups,
            create_draft_entry,
            generate_mockup_image,
            update_draft_with_mockup,
            mark_draft_failed
        ],
    )
    
    print("🚀 Temporal worker started - listening for image generation jobs...")
    print("📊 Temporal UI available at: http://localhost:8080")
    
    # Run the worker
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())