"""
Test the Temporal workflow by starting a simple job
"""
import asyncio
import sys
import os
from temporalio.client import Client

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.temporal.simple_workflow import SimpleImageWorkflow

async def test_workflow():
    """Test starting a workflow"""
    print("🧪 Testing Temporal workflow...")
    
    try:
        # Connect to Temporal server
        client = await Client.connect("localhost:7233")
        print("✅ Connected to Temporal server")
        
        # Sample job data
        job_data = {
            'job_id': 'test_temporal_123',
            'prompt': 'A simple test image',
            'aspectRatio': '1:1',
            'steps': 10,  # Low steps for quick test
            'guidance': 3.0,
            'seed': 42,
            'promptUpsampling': False,
            'safetyTolerance': 2,
            'generationCount': 0
        }
        
        print(f"🚀 Starting workflow for job: {job_data['job_id']}")
        
        # Start the workflow
        handle = await client.start_workflow(
            SimpleImageWorkflow.run,
            job_data,
            id=f"test-workflow-{job_data['job_id']}",
            task_queue="image-generation-queue",
        )
        
        print(f"✅ Workflow started: {handle.id}")
        print(f"🔗 View in Temporal UI: http://localhost:8080/namespaces/default/workflows/{handle.id}")
        
        # Wait a bit for it to start
        await asyncio.sleep(2)
        
        # Check workflow status
        try:
            describe = await handle.describe()
            print(f"📊 Workflow status: {describe.status}")
        except Exception as e:
            print(f"⚠️  Could not describe workflow: {e}")
        
        print("\n🎉 Workflow test completed! Check Temporal UI for details.")
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_workflow())