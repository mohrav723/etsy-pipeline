"""
Mockup generation workflow that creates product mockups from any image
"""
import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class MockupGenerationJob:
    source_job_id: str
    source_image_url: str
    source_prompt: str

@activity.defn
async def get_available_mockups() -> List[Dict[str, Any]]:
    """
    Activity that fetches all available mockup templates
    """
    import os
    import sys
    from dotenv import load_dotenv
    import google.cloud.firestore as firestore
    
    # Load environment variables
    load_dotenv()
    
    activity.logger.info("Fetching available mockup templates")
    
    try:
        db = firestore.Client()
        
        # Fetch all mockup templates
        mockups_collection = db.collection('mockups')
        mockups_snapshot = mockups_collection.get()
        
        mockup_data = []
        for mockup_doc in mockups_snapshot:
            mockup_info = mockup_doc.to_dict()
            mockup_data.append({
                'mockup_id': mockup_doc.id,
                'mockup_name': mockup_info.get('name', 'Unknown'),
                'mockup_template_url': mockup_info.get('imageUrl', ''),
            })
        
        activity.logger.info(f"Found {len(mockup_data)} mockup templates")
        return mockup_data
        
    except Exception as e:
        activity.logger.error(f"Failed to fetch mockups: {str(e)}")
        raise

@activity.defn
async def create_draft_entry(job_data: Dict[str, Any], mockup_data: Dict[str, Any]) -> str:
    """
    Create a draft entry in Firestore
    """
    import os
    from dotenv import load_dotenv
    import google.cloud.firestore as firestore
    from google.cloud.firestore import SERVER_TIMESTAMP
    
    load_dotenv()
    
    activity.logger.info(f"Creating draft entry for job {job_data['source_job_id']} with mockup {mockup_data['mockup_name']}")
    
    try:
        db = firestore.Client()
        
        draft_data = {
            'originalImageUrl': job_data['source_image_url'],
            'originalJobId': job_data['source_job_id'],
            'sourcePrompt': job_data.get('source_prompt', ''),
            'mockupId': mockup_data['mockup_id'],
            'mockupName': mockup_data['mockup_name'],
            'mockupTemplateUrl': mockup_data['mockup_template_url'],
            'status': 'processing',
            'createdAt': SERVER_TIMESTAMP,
        }
        
        # Add the draft document
        draft_ref = db.collection('drafts').add(draft_data)
        draft_id = draft_ref[1].id
        
        activity.logger.info(f"Created draft entry: {draft_id}")
        return draft_id
        
    except Exception as e:
        activity.logger.error(f"Failed to create draft entry: {str(e)}")
        raise

@activity.defn
async def generate_mockup_image(job_data: Dict[str, Any], mockup_data: Dict[str, Any], draft_id: str) -> str:
    """
    Generate mockup image by overlaying the original image onto the mockup template
    """
    import os
    import sys
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from src.storage import upload_image_to_storage
    from src.cost_tracker import CostTracker
    
    activity.logger.info(f"Generating mockup for draft {draft_id}")
    
    cost_tracker = CostTracker()
    
    try:
        # Import here to avoid Temporal restrictions
        import requests
        import io
        from PIL import Image
        
        # Download the source image
        source_response = requests.get(job_data['source_image_url'])
        source_response.raise_for_status()
        source_image = Image.open(io.BytesIO(source_response.content))
        
        # Download the mockup template
        template_response = requests.get(mockup_data['mockup_template_url'])
        template_response.raise_for_status()
        template_image = Image.open(io.BytesIO(template_response.content))
        
        # Generate the mockup
        mockup_image = create_simple_mockup(source_image, template_image)
        
        # Convert to bytes for upload
        img_byte_arr = io.BytesIO()
        mockup_image.save(img_byte_arr, format='PNG')
        image_data = img_byte_arr.getvalue()
        
        # Use a custom upload function for mockups
        import uuid
        public_url = upload_mockup_to_storage(image_data, draft_id)
        
        # Log storage cost
        storage_cost = cost_tracker.log_storage_cost(
            job_id=draft_id,
            image_size_bytes=len(image_data),
            operation_type='mockup_upload'
        )
        activity.logger.info(f"Mockup storage cost logged: ${storage_cost:.6f}")
        
        activity.logger.info(f"Mockup generated successfully: {public_url}")
        return public_url
        
    except Exception as e:
        activity.logger.error(f"Failed to generate mockup: {str(e)}")
        raise

def upload_mockup_to_storage(image_data: bytes, draft_id: str) -> str:
    """Upload mockup image to Firebase Storage and return public URL"""
    import os
    import uuid
    from google.cloud import storage
    
    storage_client = storage.Client()
    BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
    
    if not BUCKET_NAME:
        raise ValueError("FIREBASE_STORAGE_BUCKET not found in .env file.")
    
    bucket = storage_client.bucket(BUCKET_NAME)
    image_name = f"mockups-generated/{draft_id}_{uuid.uuid4()}.png"
    blob = bucket.blob(image_name)
    
    print(f"--- Uploading mockup to: {image_name}")
    blob.upload_from_string(image_data, content_type='image/png')
    blob.make_public()
    
    print(f"--- Upload complete. Public URL: {blob.public_url}")
    return blob.public_url

def create_simple_mockup(original_image, template_image):
    """
    Create a simple mockup by overlaying the original image onto the template
    """
    from PIL import Image
    
    # Convert to RGBA if needed
    if original_image.mode != 'RGBA':
        original_image = original_image.convert('RGBA')
    if template_image.mode != 'RGBA':
        template_image = template_image.convert('RGBA')
    
    # Resize the original image to fit within the template (40% of template size)
    template_width, template_height = template_image.size
    target_width = int(template_width * 0.4)
    target_height = int(template_height * 0.4)
    
    # Maintain aspect ratio
    original_image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Create a new image based on the template
    result = template_image.copy()
    
    # Calculate position to center the original image on the template
    orig_width, orig_height = original_image.size
    x = (template_width - orig_width) // 2
    y = (template_height - orig_height) // 2
    
    # Paste the original image onto the template
    result.paste(original_image, (x, y), original_image)
    
    return result

@activity.defn
async def update_draft_with_mockup(draft_id: str, mockup_url: str) -> None:
    """
    Update draft with the generated mockup URL and mark as completed
    """
    import os
    from dotenv import load_dotenv
    import google.cloud.firestore as firestore
    
    load_dotenv()
    
    activity.logger.info(f"Updating draft {draft_id} with mockup URL")
    
    try:
        db = firestore.Client()
        draft_ref = db.collection('drafts').document(draft_id)
        draft_ref.update({
            'mockupImageUrl': mockup_url,
            'status': 'completed'
        })
        
        activity.logger.info(f"Successfully updated draft {draft_id}")
        
    except Exception as e:
        activity.logger.error(f"Failed to update draft: {str(e)}")
        raise

@activity.defn
async def mark_draft_failed(draft_id: str, error_message: str) -> None:
    """
    Mark draft as failed with error message
    """
    import os
    from dotenv import load_dotenv
    import google.cloud.firestore as firestore
    
    load_dotenv()
    
    activity.logger.info(f"Marking draft {draft_id} as failed")
    
    try:
        db = firestore.Client()
        draft_ref = db.collection('drafts').document(draft_id)
        draft_ref.update({
            'status': 'failed',
            'errorMessage': error_message
        })
        
        activity.logger.info(f"Successfully marked draft {draft_id} as failed")
        
    except Exception as e:
        activity.logger.error(f"Failed to update draft status: {str(e)}")
        # Don't raise here to avoid infinite loops

@workflow.defn
class MockupGenerationWorkflow:
    """
    Workflow that generates product mockups from any image
    """
    
    @workflow.run
    async def run(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the mockup generation workflow:
        1. Get available mockup templates
        2. Generate mockups for each template
        3. Create draft entries
        """
        source_job_id = job_data['source_job_id']
        source_image_url = job_data['source_image_url']
        
        workflow.logger.info(f"Starting mockup generation workflow for job {source_job_id}")
        
        try:
            # Step 1: Get available mockup templates
            mockup_templates = await workflow.execute_activity(
                get_available_mockups,
                args=[],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            if not mockup_templates:
                workflow.logger.info(f"No mockup templates available for job {source_job_id}")
                return {
                    'source_job_id': source_job_id,
                    'status': 'completed',
                    'mockups_generated': 0,
                    'message': 'No mockup templates available'
                }
            
            workflow.logger.info(f"Processing {len(mockup_templates)} mockup templates")
            
            # Step 2: Process each mockup template
            successful_mockups = 0
            failed_mockups = 0
            
            for mockup_data in mockup_templates:
                try:
                    # Create draft entry
                    draft_id = await workflow.execute_activity(
                        create_draft_entry,
                        args=[job_data, mockup_data],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(maximum_attempts=3)
                    )
                    
                    # Generate mockup image
                    mockup_url = await workflow.execute_activity(
                        generate_mockup_image,
                        args=[job_data, mockup_data, draft_id],
                        start_to_close_timeout=timedelta(minutes=3),
                        retry_policy=RetryPolicy(maximum_attempts=2)
                    )
                    
                    # Update draft with completed mockup
                    await workflow.execute_activity(
                        update_draft_with_mockup,
                        args=[draft_id, mockup_url],
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(maximum_attempts=3)
                    )
                    
                    successful_mockups += 1
                    workflow.logger.info(f"Successfully generated mockup for {mockup_data['mockup_name']}")
                    
                except Exception as e:
                    failed_mockups += 1
                    workflow.logger.error(f"Failed to generate mockup for {mockup_data['mockup_name']}: {str(e)}")
                    
                    # Try to mark the draft as failed if it was created
                    try:
                        if 'draft_id' in locals():
                            await workflow.execute_activity(
                                mark_draft_failed,
                                args=[draft_id, str(e)],
                                start_to_close_timeout=timedelta(seconds=30),
                                retry_policy=RetryPolicy(maximum_attempts=1)
                            )
                    except:
                        pass  # Don't fail the whole workflow if we can't update the draft
            
            return {
                'source_job_id': source_job_id,
                'status': 'completed',
                'mockups_generated': successful_mockups,
                'mockups_failed': failed_mockups,
                'total_templates': len(mockup_templates)
            }
            
        except Exception as e:
            workflow.logger.error(f"Mockup generation workflow failed for job {source_job_id}: {str(e)}")
            raise