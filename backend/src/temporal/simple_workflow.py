"""
Simple Temporal workflow that matches your current setup exactly
"""
import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SimpleJob:
    job_id: str
    prompt: str
    aspect_ratio: str = "16:9"
    steps: int = 28
    guidance: float = 3.0
    seed: int = 42
    prompt_upsampling: bool = False
    safety_tolerance: int = 2

@activity.defn
async def generate_and_store_image(job_data: Dict[str, Any]) -> str:
    """
    Activity that does exactly what your current worker does:
    1. Generate image with BFL API
    2. Upload to Firebase Storage  
    3. Return public URL
    """
    import os
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables like your current worker  
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    # Import your existing services
    from src.services.bfl_api import generate_art_image
    from src.storage import upload_image_to_storage
    
    activity.logger.info(f"Generating image for job {job_data['job_id']}")
    
    job_id = job_data['job_id']
    
    try:
        # Use your existing BFL API function
        steps = job_data.get('steps', 28)
        activity.logger.info(f"Calling BFL API with {steps} steps")
        
        image_data = generate_art_image(
            prompt=job_data['prompt'],
            aspect_ratio=job_data.get('aspectRatio', '16:9'),
            steps=steps,
            guidance=job_data.get('guidance', 3.0),
            seed=job_data.get('seed', 42),
            prompt_upsampling=job_data.get('promptUpsampling', False),
            safety_tolerance=job_data.get('safetyTolerance', 2)
        )
        
        # Use your existing upload function
        public_url = upload_image_to_storage(image_data)
        
        activity.logger.info(f"Image uploaded successfully: {public_url}")
        return public_url
        
    except Exception as e:
        activity.logger.error(f"Failed to generate/upload image: {str(e)}")
        raise

@activity.defn
async def update_firestore_job(job_id: str, updates: Dict[str, Any]) -> None:
    """
    Update job in Firestore - keeps your existing database structure
    """
    import os
    from dotenv import load_dotenv
    import google.cloud.firestore as firestore
    
    # Load environment variables like your current worker
    load_dotenv()
    
    activity.logger.info(f"Updating Firestore job {job_id}")
    
    try:
        db = firestore.Client()
        job_ref = db.collection('jobs').document(job_id)
        job_ref.update(updates)
        
        activity.logger.info(f"Successfully updated job {job_id}")
        
    except Exception as e:
        activity.logger.error(f"Failed to update Firestore: {str(e)}")
        raise

@workflow.defn
class SimpleImageWorkflow:
    """
    Simple workflow that replaces your current Python worker
    """
    
    @workflow.run
    async def run(self, job_data: Dict[str, Any]) -> str:
        """
        Run the simple image generation workflow
        """
        # Add validation and logging for debugging
        from src.utils.workflow_log_sanitizer import sanitize_for_workflow
        sanitized_data = sanitize_for_workflow(job_data)
        workflow.logger.info(f"SimpleImageWorkflow started with job_data: {sanitized_data}")
        workflow.logger.info(f"job_data type: {type(job_data)}")
        
        if not isinstance(job_data, dict):
            error_msg = f"Expected job_data to be a dict, got {type(job_data).__name__}"
            workflow.logger.error(error_msg)
            raise ValueError(error_msg)
            
        if 'job_id' not in job_data:
            error_msg = f"Missing 'job_id' in job_data. Keys present: {list(job_data.keys())}"
            workflow.logger.error(error_msg)
            raise KeyError(error_msg)
            
        job_id = job_data['job_id']
        
        try:
            # Update status to processing
            await workflow.execute_activity(
                update_firestore_job,
                args=[job_id, {'status': 'processing'}],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # Generate and upload image
            image_url = await workflow.execute_activity(
                generate_and_store_image,
                args=[job_data],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # Update job with results
            await workflow.execute_activity(
                update_firestore_job,
                args=[job_id, {
                    'generatedImageUrl': image_url,
                    'status': 'pending_review',
                    'generationCount': job_data.get('generationCount', 0) + 1
                }],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            return image_url
            
        except Exception as e:
            # Update job with error
            await workflow.execute_activity(
                update_firestore_job,
                args=[job_id, {
                    'status': 'error',
                    'errorMessage': str(e)
                }],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=1)  # Don't retry error updates
            )
            raise