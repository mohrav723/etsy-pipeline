"""
Optimized Intelligent Mockup Generation Workflow

This workflow orchestrates the intelligent mockup generation process using
object detection and perspective transformation for realistic artwork placement.

Optimizations:
1. Reduced gRPC message sizes by storing intermediate results in Firebase Storage
2. Increased timeouts for AI processing
3. Better error handling and logging
4. More efficient data passing between activities
"""
import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import io
import uuid

@dataclass
class IntelligentMockupJob:
    """Data class for intelligent mockup generation job"""
    job_id: str
    artwork_url: str
    mockup_template: str
    original_job_id: Optional[str] = None

@activity.defn
async def update_intelligent_job_status(job_id: str, updates: Dict[str, Any]) -> None:
    """
    Update intelligent mockup job status in Firestore
    """
    import os
    from dotenv import load_dotenv
    import google.cloud.firestore as firestore
    from google.cloud.firestore import SERVER_TIMESTAMP
    
    load_dotenv()
    
    activity.logger.info(f"Updating intelligent mockup job {job_id} with: {updates}")
    
    try:
        db = firestore.Client()
        job_ref = db.collection('intelligent_mockup_jobs').document(job_id)
        
        # Add timestamp for tracking
        updates_with_timestamp = {**updates, 'updated_at': SERVER_TIMESTAMP}
        
        # Add processing timestamps based on status
        if updates.get('status') == 'processing' and 'processing_started_at' not in updates:
            updates_with_timestamp['processing_started_at'] = SERVER_TIMESTAMP
        elif updates.get('status') in ['completed', 'failed'] and 'processing_completed_at' not in updates:
            updates_with_timestamp['processing_completed_at'] = SERVER_TIMESTAMP
        
        job_ref.update(updates_with_timestamp)
        activity.logger.info(f"Successfully updated intelligent mockup job {job_id}")
        
    except Exception as e:
        activity.logger.error(f"Failed to update intelligent mockup job status: {str(e)}")
        raise

@activity.defn
async def download_and_process_images(artwork_url: str, mockup_template: str, job_id: str) -> Dict[str, Any]:
    """
    Download artwork and mockup template, detect regions, and store intermediate results
    Returns URLs and metadata instead of raw bytes to avoid gRPC size limits
    """
    import os
    import sys
    from dotenv import load_dotenv
    import requests
    import google.cloud.firestore as firestore
    from google.cloud import storage
    from PIL import Image
    
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from src.services.object_detection_optimized import ObjectDetectionService, NoSuitableRegionsError
    from src.cost_tracker import CostTracker
    
    activity.logger.info(f"Processing images for job {job_id}")
    cost_tracker = CostTracker()
    
    try:
        # Download artwork
        artwork_response = requests.get(artwork_url, timeout=30)
        artwork_response.raise_for_status()
        artwork_bytes = artwork_response.content
        activity.logger.info(f"Downloaded artwork: {len(artwork_bytes)} bytes")
        
        # Get mockup template URL from Firestore
        db = firestore.Client()
        mockups_collection = db.collection('mockups')
        
        # Try to find mockup by ID first, then by name
        mockup_doc = mockups_collection.document(mockup_template).get()
        if not mockup_doc.exists:
            # Search by name
            mockups_query = mockups_collection.where(
                filter=firestore.FieldFilter('name', '==', mockup_template)
            ).limit(1)
            mockup_docs = list(mockups_query.stream())
            if not mockup_docs:
                raise ValueError(f"Mockup template '{mockup_template}' not found")
            mockup_doc = mockup_docs[0]
        
        mockup_data = mockup_doc.to_dict()
        template_url = mockup_data.get('url')
        if not template_url:
            raise ValueError(f"Mockup template '{mockup_template}' has no URL")
        
        # Download mockup template
        template_response = requests.get(template_url, timeout=30)
        template_response.raise_for_status()
        template_bytes = template_response.content
        activity.logger.info(f"Downloaded template: {len(template_bytes)} bytes")
        
        # Convert to PIL Image for object detection
        template_image = Image.open(io.BytesIO(template_bytes))
        template_size = template_image.size
        activity.logger.info(f"Template image size: {template_size}")
        
        # Initialize object detection service with lightweight settings
        detection_service = ObjectDetectionService()
        
        # Find suitable regions
        detected_regions = detection_service.find_suitable_regions(template_image)
        
        if not detected_regions:
            activity.logger.warning("No suitable regions found")
            return {
                'success': False,
                'error': 'No suitable regions detected in mockup template'
            }
        
        activity.logger.info(f"Found {len(detected_regions)} suitable regions")
        
        # Convert to serializable format
        regions_data = []
        for region in detected_regions:
            region_dict = region.to_dict()
            regions_data.append(region_dict)
            activity.logger.info(
                f"Region: {region.label} at ({region.x}, {region.y}) "
                f"size {region.width}x{region.height} confidence {region.confidence:.3f}"
            )
        
        # Store artwork temporarily in Firebase Storage to avoid passing large bytes
        storage_client = storage.Client()
        BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
        bucket = storage_client.bucket(BUCKET_NAME)
        
        temp_artwork_name = f"intelligent-mockups/temp/{job_id}_artwork.png"
        artwork_blob = bucket.blob(temp_artwork_name)
        artwork_blob.upload_from_string(artwork_bytes, content_type='image/png')
        temp_artwork_url = artwork_blob.public_url
        
        temp_template_name = f"intelligent-mockups/temp/{job_id}_template.png"
        template_blob = bucket.blob(temp_template_name)
        template_blob.upload_from_string(template_bytes, content_type='image/png')
        temp_template_url = template_blob.public_url
        
        # Log processing cost
        processing_cost = cost_tracker.log_storage_cost(
            job_id=job_id,
            image_size_bytes=len(template_bytes),
            operation_type='object_detection'
        )
        activity.logger.info(f"Object detection cost logged: ${processing_cost:.6f}")
        
        return {
            'success': True,
            'temp_artwork_url': temp_artwork_url,
            'temp_template_url': temp_template_url,
            'template_size': template_size,
            'regions': regions_data,
            'best_region': max(regions_data, key=lambda r: r['confidence'])
        }
        
    except Exception as e:
        activity.logger.error(f"Failed to process images: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@activity.defn
async def create_intelligent_mockup(
    temp_artwork_url: str,
    temp_template_url: str,
    region_data: Dict[str, Any],
    template_size: Tuple[int, int],
    job_id: str
) -> str:
    """
    Create the final intelligent mockup by transforming and compositing the artwork
    Returns the URL of the final mockup
    """
    import os
    import sys
    from dotenv import load_dotenv
    import requests
    from PIL import Image
    from google.cloud import storage
    
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from src.services.perspective_transform import PerspectiveTransformService
    from src.services.object_detection_optimized import BoundingBox
    from src.cost_tracker import CostTracker
    
    activity.logger.info(f"Creating intelligent mockup for job {job_id}")
    cost_tracker = CostTracker()
    
    try:
        # Download temporary images
        artwork_response = requests.get(temp_artwork_url, timeout=30)
        artwork_response.raise_for_status()
        artwork_image = Image.open(io.BytesIO(artwork_response.content))
        
        template_response = requests.get(temp_template_url, timeout=30)
        template_response.raise_for_status()
        template_image = Image.open(io.BytesIO(template_response.content))
        
        # Recreate BoundingBox from region data
        region = BoundingBox(
            x=region_data['x'],
            y=region_data['y'],
            width=region_data['width'],
            height=region_data['height'],
            confidence=region_data['confidence'],
            label=region_data['label']
        )
        
        # Initialize perspective transformation service
        transform_service = PerspectiveTransformService()
        
        # Transform artwork to fit region
        result = transform_service.transform_artwork_to_region(
            artwork_image, region, template_size
        )
        
        activity.logger.info(
            f"Artwork transformed from {result.original_size} to {result.target_size}"
        )
        
        # Compose final mockup
        final_mockup = transform_service.compose_mockup(
            template_image, result.transformed_image, region
        )
        
        # Save final mockup to Firebase Storage
        storage_client = storage.Client()
        BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
        bucket = storage_client.bucket(BUCKET_NAME)
        
        final_name = f"intelligent-mockups/{job_id}_{uuid.uuid4()}.png"
        final_blob = bucket.blob(final_name)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        final_mockup.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        final_blob.upload_from_string(img_bytes.getvalue(), content_type='image/png')
        final_blob.make_public()
        
        public_url = final_blob.public_url
        activity.logger.info(f"Upload complete. Public URL: {public_url}")
        
        # Log storage cost
        storage_cost = cost_tracker.log_storage_cost(
            job_id=job_id,
            image_size_bytes=img_bytes.tell(),
            operation_type='intelligent_mockup_upload'
        )
        activity.logger.info(f"Storage cost logged: ${storage_cost:.6f}")
        
        # Clean up temporary files
        try:
            bucket.blob(f"intelligent-mockups/temp/{job_id}_artwork.png").delete()
            bucket.blob(f"intelligent-mockups/temp/{job_id}_template.png").delete()
        except Exception as e:
            activity.logger.warning(f"Failed to clean up temp files: {e}")
        
        return public_url
        
    except Exception as e:
        activity.logger.error(f"Failed to create intelligent mockup: {str(e)}")
        raise

@workflow.defn
class IntelligentMockupGenerationWorkflow:
    """
    Optimized workflow that orchestrates intelligent mockup generation using AI-based
    object detection and perspective transformation for realistic artwork placement.
    """
    
    @workflow.run
    async def run(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the intelligent mockup generation workflow
        
        Args:
            job_data: Dictionary containing:
                - job_id: Unique job identifier
                - artwork_url: URL of the artwork image
                - mockup_template: Name/ID of the mockup template
                - original_job_id: Optional reference to original art generation job
        
        Returns:
            Dictionary with workflow results and metadata
        """
        job_id = job_data['job_id']
        artwork_url = job_data['artwork_url']
        mockup_template = job_data['mockup_template']
        
        workflow.logger.info(f"Starting optimized intelligent mockup generation workflow for job {job_id}")
        workflow.logger.info(f"Artwork URL: {artwork_url}")
        workflow.logger.info(f"Mockup template: {mockup_template}")
        
        try:
            # Step 1: Update status to processing
            await workflow.execute_activity(
                update_intelligent_job_status,
                args=[job_id, {'status': 'processing'}],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # Step 2: Download, detect regions, and prepare images
            # This combines multiple steps to reduce gRPC calls
            processing_result = await workflow.execute_activity(
                download_and_process_images,
                args=[artwork_url, mockup_template, job_id],
                start_to_close_timeout=timedelta(minutes=5),  # Increased timeout for AI processing
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    backoff_coefficient=2.0,
                    initial_interval=timedelta(seconds=1),
                    maximum_interval=timedelta(seconds=30)
                )
            )
            
            if not processing_result['success']:
                # Failed to process images
                await workflow.execute_activity(
                    update_intelligent_job_status,
                    args=[job_id, {
                        'status': 'failed',
                        'error_message': processing_result.get('error', 'Unknown error during image processing')
                    }],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=1)
                )
                
                return {
                    'job_id': job_id,
                    'status': 'failed',
                    'error': processing_result.get('error', 'Unknown error')
                }
            
            # Step 3: Create the final mockup
            result_url = await workflow.execute_activity(
                create_intelligent_mockup,
                args=[
                    processing_result['temp_artwork_url'],
                    processing_result['temp_template_url'],
                    processing_result['best_region'],
                    processing_result['template_size'],
                    job_id
                ],
                start_to_close_timeout=timedelta(minutes=3),  # Increased timeout
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    backoff_coefficient=2.0
                )
            )
            
            # Step 4: Update final status
            await workflow.execute_activity(
                update_intelligent_job_status,
                args=[job_id, {
                    'status': 'completed',
                    'result_url': result_url,
                    'detected_regions': len(processing_result['regions']),
                    'selected_region': processing_result['best_region']['label']
                }],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            workflow.logger.info(f"Intelligent mockup generation completed for job {job_id}")
            
            return {
                'job_id': job_id,
                'status': 'completed',
                'result_url': result_url,
                'detected_regions': len(processing_result['regions']),
                'selected_region': processing_result['best_region']
            }
            
        except Exception as e:
            workflow.logger.error(f"Workflow failed for job {job_id}: {str(e)}")
            
            # Update status to failed
            try:
                await workflow.execute_activity(
                    update_intelligent_job_status,
                    args=[job_id, {
                        'status': 'failed',
                        'error_message': str(e)
                    }],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=1)
                )
            except Exception as update_error:
                workflow.logger.error(f"Failed to update job status: {update_error}")
            
            raise