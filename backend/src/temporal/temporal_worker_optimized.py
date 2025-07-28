"""
Optimized Temporal worker with intelligent mockup improvements
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
from src.temporal.intelligent_mockup_generation_workflow_optimized import (
    IntelligentMockupGenerationWorkflow,
    update_intelligent_job_status,
    get_all_mockup_templates,
    download_and_process_images,
    create_intelligent_mockup,
    store_multiple_mockup_results
)

async def main():
    # Connect to Temporal server
    client = await Client.connect("localhost:7233")
    
    # Create worker
    worker = Worker(
        client,
        task_queue="image-generation-queue",
        workflows=[
            SimpleImageWorkflow, 
            MockupGenerationWorkflow, 
            IntelligentMockupGenerationWorkflow
        ],
        activities=[
            # Simple workflow activities
            generate_and_store_image, 
            update_firestore_job,
            # Mockup generation workflow activities
            get_available_mockups,
            create_draft_entry,
            generate_mockup_image,
            update_draft_with_mockup,
            mark_draft_failed,
            # Optimized intelligent mockup workflow activities
            update_intelligent_job_status,
            get_all_mockup_templates,
            download_and_process_images,
            create_intelligent_mockup,
            store_multiple_mockup_results
        ],
    )
    
    print("🚀 Optimized Temporal worker started - listening for image generation jobs...")
    print("📊 Temporal UI available at: http://localhost:8080")
    print("🎯 Registered workflows:")
    print("   - SimpleImageWorkflow (simple art generation)")
    print("   - MockupGenerationWorkflow (simple mockup creation)")
    print("   - IntelligentMockupGenerationWorkflow (AI-powered mockup creation - OPTIMIZED)")
    print("🔧 Task queue: image-generation-queue")
    print("✨ Optimizations:")
    print("   - Reduced gRPC message sizes")
    print("   - Increased AI processing timeouts")
    print("   - Better error handling")
    
    # Run the worker
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())