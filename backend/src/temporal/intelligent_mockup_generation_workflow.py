"""
Intelligent Mockup Generation Workflow

This workflow orchestrates the intelligent mockup generation process using
object detection and perspective transformation for realistic artwork placement.
"""
import asyncio
from datetime import timedelta
from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import io

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
async def download_artwork_and_template(artwork_url: str, mockup_template: str) -> Tuple[bytes, bytes, str]:
    """
    Download artwork and mockup template images
    
    Returns:
        Tuple of (artwork_bytes, template_bytes, template_url)
    """
    import os
    import sys
    from dotenv import load_dotenv
    import requests
    import google.cloud.firestore as firestore
    
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    activity.logger.info(f"Downloading artwork from: {artwork_url}")
    activity.logger.info(f"Looking up mockup template: {mockup_template}")
    
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
        template_url = mockup_data.get('imageUrl', '')
        
        if not template_url:
            raise ValueError(f"No imageUrl found for mockup template '{mockup_template}'")
        
        activity.logger.info(f"Found mockup template URL: {template_url}")
        
        # Download mockup template
        template_response = requests.get(template_url, timeout=30)
        template_response.raise_for_status()
        template_bytes = template_response.content
        
        activity.logger.info(f"Downloaded template: {len(template_bytes)} bytes")
        
        return artwork_bytes, template_bytes, template_url
        
    except Exception as e:
        activity.logger.error(f"Failed to download images: {str(e)}")
        raise

@activity.defn
async def detect_suitable_regions(template_bytes: bytes, job_id: str) -> List[Dict[str, Any]]:
    """
    Use object detection service to find suitable regions in mockup template
    """
    import os
    import sys
    from dotenv import load_dotenv
    from PIL import Image
    
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from src.services.object_detection import NoSuitableRegionsError
    from src.services.opencv_detection.compatibility_wrapper import create_object_detection_service
    
    activity.logger.info(f"Starting object detection for job {job_id}")
    
    try:
        # Convert bytes to PIL Image
        template_image = Image.open(io.BytesIO(template_bytes))
        activity.logger.info(f"Template image size: {template_image.size}")
        
        # Initialize object detection service with feature flag support
        detection_service = create_object_detection_service(job_id=job_id)
        service_type = "OpenCV" if detection_service.use_opencv else "DETR"
        activity.logger.info(f"Using {service_type} detection service")
        
        # Find suitable regions
        detected_regions = detection_service.find_suitable_regions(template_image)
        
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
        
        return regions_data
        
    except NoSuitableRegionsError as e:
        activity.logger.warning(f"No suitable regions found: {str(e)}")
        return []
    except Exception as e:
        activity.logger.error(f"Object detection failed: {str(e)}")
        raise

@activity.defn
async def transform_artwork_to_region(
    artwork_bytes: bytes, 
    region_data: Dict[str, Any], 
    template_size: Tuple[int, int],
    job_id: str
) -> bytes:
    """
    Use perspective transformation service to warp artwork to fit detected region
    """
    import os
    import sys
    from dotenv import load_dotenv
    from PIL import Image
    
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from src.services.perspective_transform import PerspectiveTransformService
    from src.services.object_detection import BoundingBox
    
    activity.logger.info(f"Starting perspective transformation for job {job_id}")
    
    try:
        # Convert bytes to PIL Image
        artwork_image = Image.open(io.BytesIO(artwork_bytes))
        activity.logger.info(f"Artwork image size: {artwork_image.size}")
        
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
        
        # Convert result to bytes
        img_bytes = io.BytesIO()
        result.transformed_image.save(img_bytes, format='PNG')
        transformed_bytes = img_bytes.getvalue()
        
        return transformed_bytes
        
    except Exception as e:
        activity.logger.error(f"Perspective transformation failed: {str(e)}")
        raise

@activity.defn
async def compose_and_store_final_mockup(
    template_bytes: bytes,
    transformed_artwork_bytes: bytes,
    region_data: Dict[str, Any],
    job_id: str
) -> str:
    """
    Create final composite image and store it directly to Firebase Storage
    This avoids GRPC message size limits by not returning large image data
    """
    import os
    import sys
    import uuid
    from dotenv import load_dotenv
    from PIL import Image
    from google.cloud import storage
    
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from src.services.perspective_transform import PerspectiveTransformService
    from src.services.object_detection import BoundingBox
    
    activity.logger.info(f"Composing and storing final mockup for job {job_id}")
    
    cost_tracker = CostTracker()
    
    try:
        # Convert bytes to PIL Images
        template_image = Image.open(io.BytesIO(template_bytes))
        transformed_artwork = Image.open(io.BytesIO(transformed_artwork_bytes))
        
        # Recreate BoundingBox from region data
        region = BoundingBox(
            x=region_data['x'],
            y=region_data['y'],
            width=region_data['width'],
            height=region_data['height'],
            confidence=region_data['confidence'],
            label=region_data['label']
        )
        
        # Initialize perspective transformation service for composition
        transform_service = PerspectiveTransformService()
        
        # Create final composite
        composite_image = transform_service.create_composite_image(
            template_image, transformed_artwork, region, blend_mode="normal"
        )
        
        activity.logger.info(f"Final composite created: {composite_image.size}")
        
        # Convert to bytes for storage
        img_bytes = io.BytesIO()
        composite_image.save(img_bytes, format='PNG', quality=95)
        composite_bytes = img_bytes.getvalue()
        
        activity.logger.info(f"Final mockup size: {len(composite_bytes)} bytes")
        
        # Store directly to Firebase Storage
        storage_client = storage.Client()
        BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
        
        if not BUCKET_NAME:
            raise ValueError("FIREBASE_STORAGE_BUCKET not found in .env file.")
        
        bucket = storage_client.bucket(BUCKET_NAME)
        image_name = f"intelligent-mockups/{job_id}_{uuid.uuid4()}.png"
        blob = bucket.blob(image_name)
        
        activity.logger.info(f"Uploading intelligent mockup to: {image_name}")
        blob.upload_from_string(composite_bytes, content_type='image/png')
        blob.make_public()
        
        public_url = blob.public_url
        activity.logger.info(f"Upload complete. Public URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        activity.logger.error(f"Final composition and storage failed: {str(e)}")
        raise

@activity.defn
async def store_intelligent_mockup_result(mockup_bytes: bytes, job_id: str) -> str:
    """
    Store the final intelligent mockup result in Firebase Storage
    """
    import os
    import sys
    import uuid
    from dotenv import load_dotenv
    from google.cloud import storage
    
    load_dotenv()
    
    # Add the backend directory to Python path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    from src.cost_tracker import CostTracker
    
    activity.logger.info(f"Storing intelligent mockup result for job {job_id}")
    
    cost_tracker = CostTracker()
    
    try:
        storage_client = storage.Client()
        BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
        
        if not BUCKET_NAME:
            raise ValueError("FIREBASE_STORAGE_BUCKET not found in .env file.")
        
        bucket = storage_client.bucket(BUCKET_NAME)
        image_name = f"intelligent-mockups/{job_id}_{uuid.uuid4()}.png"
        blob = bucket.blob(image_name)
        
        activity.logger.info(f"Uploading intelligent mockup to: {image_name}")
        blob.upload_from_string(mockup_bytes, content_type='image/png')
        blob.make_public()
        
        public_url = blob.public_url
        activity.logger.info(f"Upload complete. Public URL: {public_url}")
        
        return public_url
        
    except Exception as e:
        activity.logger.error(f"Failed to store intelligent mockup result: {str(e)}")
        raise

@workflow.defn
class IntelligentMockupGenerationWorkflow:
    """
    Workflow that orchestrates intelligent mockup generation using AI-based
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
        
        workflow.logger.info(f"Starting intelligent mockup generation workflow for job {job_id}")
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
            
            # Step 2: Download artwork and mockup template
            artwork_bytes, template_bytes, template_url = await workflow.execute_activity(
                download_artwork_and_template,
                args=[artwork_url, mockup_template],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            # Step 3: Detect suitable regions in mockup template
            detected_regions = await workflow.execute_activity(
                detect_suitable_regions,
                args=[template_bytes, job_id],
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            if not detected_regions:
                # No suitable regions found - mark as failed
                await workflow.execute_activity(
                    update_intelligent_job_status,
                    args=[job_id, {
                        'status': 'failed',
                        'error_message': 'No suitable regions detected in mockup template for artwork placement'
                    }],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(maximum_attempts=1)
                )
                
                return {
                    'job_id': job_id,
                    'status': 'failed',
                    'error': 'No suitable regions detected',
                    'detected_regions': 0
                }
            
            # Use the best region (highest confidence)
            best_region = max(detected_regions, key=lambda r: r['confidence'])
            workflow.logger.info(
                f"Using best region: {best_region['label']} with confidence {best_region['confidence']:.3f}"
            )
            
            # Get template size from the downloaded template
            from PIL import Image
            template_image = Image.open(io.BytesIO(template_bytes))
            template_size = template_image.size
            
            # Step 4: Transform artwork to fit the detected region
            transformed_artwork_bytes = await workflow.execute_activity(
                transform_artwork_to_region,
                args=[artwork_bytes, best_region, template_size, job_id],
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            # Step 5: Compose final mockup and store result (combined to avoid GRPC size limits)
            result_url = await workflow.execute_activity(
                compose_and_store_final_mockup,
                args=[template_bytes, transformed_artwork_bytes, best_region, job_id],
                start_to_close_timeout=timedelta(minutes=3),
                retry_policy=RetryPolicy(maximum_attempts=2)
            )
            
            # Step 6: Update job with successful completion
            await workflow.execute_activity(
                update_intelligent_job_status,
                args=[job_id, {
                    'status': 'completed',
                    'result_url': result_url,
                    'detection_confidence': best_region['confidence'],
                    'detected_objects': detected_regions
                }],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=RetryPolicy(maximum_attempts=3)
            )
            
            workflow.logger.info(f"Intelligent mockup generation completed successfully for job {job_id}")
            
            return {
                'job_id': job_id,
                'status': 'completed',
                'result_url': result_url,
                'detected_regions': len(detected_regions),
                'best_region': best_region,
                'template_url': template_url
            }
            
        except Exception as e:
            workflow.logger.error(f"Intelligent mockup generation workflow failed for job {job_id}: {str(e)}")
            
            # Update job with error status
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
                workflow.logger.error(f"Failed to update job error status: {update_error}")
            
            # Re-raise the original exception
            raise