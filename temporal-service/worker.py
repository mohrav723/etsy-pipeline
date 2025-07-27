"""
Temporal worker that replaces your current backend/app.py
"""
import asyncio
import os
from temporalio import Worker
from temporalio.client import Client

from simple_workflow import SimpleImageWorkflow, generate_and_store_image, update_firestore_job

async def main():
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    
    # Create worker
    worker = Worker(
        client,
        task_queue="image-generation-queue",
        workflows=[SimpleImageWorkflow],
        activities=[generate_and_store_image, update_firestore_job],
    )
    
    print("🚀 Temporal worker started - listening for image generation jobs...")
    print("📊 Temporal UI available at: http://localhost:8080")
    
    # Run the worker
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())