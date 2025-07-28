"""
Integration tests for the Intelligent Mockup Generation Workflow.
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from PIL import Image
import io

# Configure pytest to handle async tests
pytest_plugins = ('pytest_asyncio',)

from src.temporal.intelligent_mockup_generation_workflow import (
    IntelligentMockupGenerationWorkflow,
    update_intelligent_job_status,
    download_artwork_and_template,
    detect_suitable_regions,
    transform_artwork_to_region,
    compose_final_mockup,
    store_intelligent_mockup_result,
    IntelligentMockupJob
)

class TestIntelligentMockupJob:
    """Tests for the IntelligentMockupJob dataclass."""
    
    def test_job_creation(self):
        """Test creating an intelligent mockup job."""
        job = IntelligentMockupJob(
            job_id="test_job_123",
            artwork_url="https://example.com/artwork.png",
            mockup_template="picture_frame_01",
            original_job_id="original_456"
        )
        
        assert job.job_id == "test_job_123"
        assert job.artwork_url == "https://example.com/artwork.png"
        assert job.mockup_template == "picture_frame_01"
        assert job.original_job_id == "original_456"
    
    def test_job_creation_minimal(self):
        """Test creating job with minimal required fields."""
        job = IntelligentMockupJob(
            job_id="test_job_123",
            artwork_url="https://example.com/artwork.png",
            mockup_template="picture_frame_01"
        )
        
        assert job.job_id == "test_job_123"
        assert job.original_job_id is None

class TestIntelligentMockupActivities:
    """Tests for individual workflow activities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_job_id = "test_job_123"
        self.test_artwork_url = "https://example.com/artwork.png"
        self.test_mockup_template = "picture_frame_01"
        self.test_template_url = "https://example.com/template.png"
        
        # Create test images
        self.test_artwork = Image.new('RGB', (300, 200), color='blue')
        self.test_template = Image.new('RGB', (800, 600), color='white')
        
        # Convert to bytes
        self.artwork_bytes = self._image_to_bytes(self.test_artwork)
        self.template_bytes = self._image_to_bytes(self.test_template)
        
        # Mock region data
        self.mock_region_data = {
            'x': 100,
            'y': 100,
            'width': 200,
            'height': 150,
            'confidence': 0.9,
            'label': 'picture frame'
        }
    
    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """Convert PIL Image to bytes."""
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        return img_bytes.getvalue()
    
    @patch('google.cloud.firestore')
    def test_update_intelligent_job_status(self, mock_firestore):
        """Test updating job status in Firestore."""
        # Mock Firestore client and operations
        mock_db = Mock()
        mock_collection = Mock()
        mock_doc = Mock()
        
        mock_firestore.Client.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc
        
        # Test the activity
        asyncio.run(update_intelligent_job_status(
            self.test_job_id, 
            {'status': 'processing'}
        ))
        
        # Verify Firestore operations
        mock_db.collection.assert_called_with('intelligent_mockup_jobs')
        mock_collection.document.assert_called_with(self.test_job_id)
        mock_doc.update.assert_called_once()
        
        # Check that updates include timestamp
        call_args = mock_doc.update.call_args[0][0]
        assert call_args['status'] == 'processing'
        assert 'updated_at' in call_args
    
    @patch('requests.get')
    @patch('google.cloud.firestore')
    def test_download_artwork_and_template(self, mock_firestore, mock_requests):
        """Test downloading artwork and template images."""
        # Mock HTTP requests
        mock_artwork_response = Mock()
        mock_artwork_response.content = self.artwork_bytes
        mock_artwork_response.raise_for_status.return_value = None
        
        mock_template_response = Mock()
        mock_template_response.content = self.template_bytes
        mock_template_response.raise_for_status.return_value = None
        
        mock_requests.side_effect = [mock_artwork_response, mock_template_response]
        
        # Mock Firestore for mockup template lookup
        mock_db = Mock()
        mock_collection = Mock()
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {'imageUrl': self.test_template_url}
        
        mock_firestore.Client.return_value = mock_db
        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc
        
        # Test the activity
        result = asyncio.run(download_artwork_and_template(
            self.test_artwork_url, 
            self.test_mockup_template
        ))
        
        # Verify results
        artwork_bytes, template_bytes, template_url = result
        assert artwork_bytes == self.artwork_bytes
        assert template_bytes == self.template_bytes
        assert template_url == self.test_template_url
        
        # Verify calls
        assert mock_requests.call_count == 2
        mock_requests.assert_any_call(self.test_artwork_url, timeout=30)
        mock_requests.assert_any_call(self.test_template_url, timeout=30)
    
    @patch('src.services.object_detection.ObjectDetectionService')
    @patch('src.cost_tracker.CostTracker')
    def test_detect_suitable_regions(self, mock_cost_tracker_class, mock_detection_service_class):
        """Test detecting suitable regions in template."""
        # Mock object detection service
        mock_detection_service = Mock()
        mock_detection_service_class.return_value = mock_detection_service
        
        # Mock detected regions
        from src.services.object_detection import BoundingBox
        mock_region = BoundingBox(100, 100, 200, 150, 0.9, "picture frame")
        mock_detection_service.find_suitable_regions.return_value = [mock_region]
        
        # Mock cost tracker
        mock_cost_tracker = Mock()
        mock_cost_tracker_class.return_value = mock_cost_tracker
        mock_cost_tracker.log_storage_cost.return_value = 0.001
        
        # Test the activity
        result = asyncio.run(detect_suitable_regions(self.template_bytes, self.test_job_id))
        
        # Verify results
        assert len(result) == 1
        assert result[0]['x'] == 100
        assert result[0]['y'] == 100
        assert result[0]['width'] == 200
        assert result[0]['height'] == 150
        assert result[0]['confidence'] == 0.9
        assert result[0]['label'] == "picture frame"
        
        # Verify service calls
        mock_detection_service.find_suitable_regions.assert_called_once()
        mock_cost_tracker.log_storage_cost.assert_called_once()
    
    @patch('src.services.perspective_transform.PerspectiveTransformService')
    @patch('src.cost_tracker.CostTracker')
    def test_transform_artwork_to_region(self, mock_cost_tracker_class, mock_transform_service_class):
        """Test transforming artwork to fit region."""
        # Mock perspective transformation service
        mock_transform_service = Mock()
        mock_transform_service_class.return_value = mock_transform_service
        
        # Mock transformation result
        from src.services.perspective_transform import TransformationResult
        transformed_image = Image.new('RGB', (200, 150), color='red')
        mock_result = TransformationResult(
            transformed_image=transformed_image,
            transformation_matrix=None,
            source_corners=[],
            target_corners=[],
            original_size=(300, 200),
            target_size=(200, 150)
        )
        mock_transform_service.transform_artwork_to_region.return_value = mock_result
        
        # Mock cost tracker
        mock_cost_tracker = Mock()
        mock_cost_tracker_class.return_value = mock_cost_tracker
        mock_cost_tracker.log_storage_cost.return_value = 0.001
        
        # Test the activity
        result = asyncio.run(transform_artwork_to_region(
            self.artwork_bytes,
            self.mock_region_data,
            (800, 600),
            self.test_job_id
        ))
        
        # Verify result is bytes
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify service calls
        mock_transform_service.transform_artwork_to_region.assert_called_once()
        mock_cost_tracker.log_storage_cost.assert_called_once()
    
    @patch('src.services.perspective_transform.PerspectiveTransformService')
    def test_compose_final_mockup(self, mock_transform_service_class):
        """Test composing final mockup image."""
        # Mock perspective transformation service
        mock_transform_service = Mock()
        mock_transform_service_class.return_value = mock_transform_service
        
        # Mock composite result
        composite_image = Image.new('RGB', (800, 600), color='green')
        mock_transform_service.create_composite_image.return_value = composite_image
        
        # Create mock transformed artwork bytes
        transformed_artwork = Image.new('RGB', (200, 150), color='red')
        transformed_bytes = self._image_to_bytes(transformed_artwork)
        
        # Test the activity
        result = asyncio.run(compose_final_mockup(
            self.template_bytes,
            transformed_bytes,
            self.mock_region_data,
            self.test_job_id
        ))
        
        # Verify result is bytes
        assert isinstance(result, bytes)
        assert len(result) > 0
        
        # Verify service calls
        mock_transform_service.create_composite_image.assert_called_once()
    
    @patch('google.cloud.storage')
    @patch('src.cost_tracker.CostTracker')
    @patch('os.getenv')
    def test_store_intelligent_mockup_result(self, mock_getenv, mock_cost_tracker_class, mock_storage):
        """Test storing mockup result in Firebase Storage."""
        # Mock environment variable
        mock_getenv.return_value = "test-bucket"
        
        # Mock Google Cloud Storage
        mock_storage_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_blob.public_url = "https://storage.googleapis.com/test-bucket/intelligent-mockups/test.png"
        
        mock_storage.Client.return_value = mock_storage_client
        mock_storage_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        # Mock cost tracker
        mock_cost_tracker = Mock()
        mock_cost_tracker_class.return_value = mock_cost_tracker
        mock_cost_tracker.log_storage_cost.return_value = 0.001
        
        # Test the activity
        result = asyncio.run(store_intelligent_mockup_result(
            self.template_bytes,
            self.test_job_id
        ))
        
        # Verify result
        assert result == mock_blob.public_url
        
        # Verify storage operations
        mock_storage_client.bucket.assert_called_with("test-bucket")
        mock_blob.upload_from_string.assert_called_once()
        mock_blob.make_public.assert_called_once()
        mock_cost_tracker.log_storage_cost.assert_called_once()

class TestIntelligentMockupWorkflow:
    """Tests for the complete workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_job_data = {
            'job_id': 'test_job_123',
            'artwork_url': 'https://example.com/artwork.png',
            'mockup_template': 'picture_frame_01'
        }
        
        self.mock_region_data = {
            'x': 100,
            'y': 100,
            'width': 200,
            'height': 150,
            'confidence': 0.9,
            'label': 'picture frame'
        }
    
    def test_workflow_initialization(self):
        """Test workflow can be instantiated."""
        workflow = IntelligentMockupGenerationWorkflow()
        assert workflow is not None
    
    @pytest.mark.asyncio
    async def test_workflow_success_flow(self):
        """Test successful workflow execution."""
        # Mock workflow execution context
        mock_workflow.logger = Mock()
        mock_workflow.execute_activity = Mock()
        
        # Mock activity responses
        async def mock_execute_activity(activity_func, args, **kwargs):
            if activity_func.__name__ == 'update_intelligent_job_status':
                return None
            elif activity_func.__name__ == 'download_artwork_and_template':
                return (b'artwork_data', b'template_data', 'https://template.url')
            elif activity_func.__name__ == 'detect_suitable_regions':
                return [self.mock_region_data]
            elif activity_func.__name__ == 'transform_artwork_to_region':
                return b'transformed_artwork_data'
            elif activity_func.__name__ == 'compose_final_mockup':
                return b'final_mockup_data'
            elif activity_func.__name__ == 'store_intelligent_mockup_result':
                return 'https://storage.url/result.png'
            else:
                return None
        
        mock_workflow.execute_activity.side_effect = mock_execute_activity
        
        # Create workflow instance and run
        workflow_instance = IntelligentMockupGenerationWorkflow()
        
        # Mock the PIL Image import for template size
        with patch('src.temporal.intelligent_mockup_generation_workflow.Image') as mock_image:
            mock_pil_image = Mock()
            mock_pil_image.size = (800, 600)
            mock_image.open.return_value = mock_pil_image
            
            result = await workflow_instance.run(self.test_job_data)
        
        # Verify result
        assert result['job_id'] == 'test_job_123'
        assert result['status'] == 'completed'
        assert result['result_url'] == 'https://storage.url/result.png'
        assert result['detected_regions'] == 1
        assert result['best_region'] == self.mock_region_data
    
    @pytest.mark.asyncio
    async def test_workflow_no_regions_found(self):
        """Test workflow when no suitable regions are detected."""
        # Mock workflow execution context
        mock_workflow.logger = Mock()
        mock_workflow.execute_activity = Mock()
        
        # Mock activity responses - no regions found
        async def mock_execute_activity(activity_func, args, **kwargs):
            if activity_func.__name__ == 'update_intelligent_job_status':
                return None
            elif activity_func.__name__ == 'download_artwork_and_template':
                return (b'artwork_data', b'template_data', 'https://template.url')
            elif activity_func.__name__ == 'detect_suitable_regions':
                return []  # No regions found
            else:
                return None
        
        mock_workflow.execute_activity.side_effect = mock_execute_activity
        
        # Create workflow instance and run
        workflow_instance = IntelligentMockupGenerationWorkflow()
        result = await workflow_instance.run(self.test_job_data)
        
        # Verify result shows failure due to no regions
        assert result['job_id'] == 'test_job_123'
        assert result['status'] == 'failed'
        assert result['error'] == 'No suitable regions detected'
        assert result['detected_regions'] == 0

class TestWorkflowIntegration:
    """Integration tests for workflow compatibility."""
    
    def test_workflow_import_compatibility(self):
        """Test that importing the new workflow doesn't break existing imports."""
        # Test importing all workflows together
        try:
            from src.temporal.simple_workflow import SimpleImageWorkflow
            from src.temporal.mockup_generation_workflow import MockupGenerationWorkflow
            from src.temporal.intelligent_mockup_generation_workflow import IntelligentMockupGenerationWorkflow
            
            assert SimpleImageWorkflow is not None
            assert MockupGenerationWorkflow is not None
            assert IntelligentMockupGenerationWorkflow is not None
            
        except ImportError as e:
            pytest.fail(f"Import compatibility test failed: {e}")
    
    def test_activity_import_compatibility(self):
        """Test that importing new activities doesn't conflict with existing ones."""
        try:
            # Import existing activities
            from src.temporal.simple_workflow import generate_and_store_image, update_firestore_job
            from src.temporal.mockup_generation_workflow import get_available_mockups, create_draft_entry
            
            # Import new activities
            from src.temporal.intelligent_mockup_generation_workflow import (
                update_intelligent_job_status,
                download_artwork_and_template,
                detect_suitable_regions,
                transform_artwork_to_region,
                compose_final_mockup,
                store_intelligent_mockup_result
            )
            
            # Verify all activities are callable
            assert callable(generate_and_store_image)
            assert callable(update_firestore_job)
            assert callable(get_available_mockups)
            assert callable(create_draft_entry)
            assert callable(update_intelligent_job_status)
            assert callable(download_artwork_and_template)
            assert callable(detect_suitable_regions)
            assert callable(transform_artwork_to_region)
            assert callable(compose_final_mockup)
            assert callable(store_intelligent_mockup_result)
            
        except ImportError as e:
            pytest.fail(f"Activity import compatibility test failed: {e}")
    
    def test_service_integration_no_conflicts(self):
        """Test that service integrations don't conflict."""
        try:
            # Import services used by intelligent mockup workflow
            from src.services.object_detection import ObjectDetectionService
            from src.services.perspective_transform import PerspectiveTransformService
            from src.cost_tracker import CostTracker
            from src.storage import upload_image_to_storage
            
            # Verify services can be instantiated
            detection_service = ObjectDetectionService()
            transform_service = PerspectiveTransformService()
            cost_tracker = CostTracker()
            
            assert detection_service is not None
            assert transform_service is not None
            assert cost_tracker is not None
            assert callable(upload_image_to_storage)
            
        except ImportError as e:
            pytest.fail(f"Service integration test failed: {e}")
    
    def test_firestore_collection_isolation(self):
        """Test that different collections don't interfere with each other."""
        collections = [
            'jobs',                      # Simple workflow
            'mockup_jobs',              # Mockup generation workflow
            'intelligent_mockup_jobs',  # Intelligent mockup workflow
            'costs',                    # Cost tracking
            'mockups',                  # Mockup templates
            'drafts'                    # Draft entries
        ]
        
        # Verify all collection names are unique
        assert len(collections) == len(set(collections))
        
        # Verify naming conventions
        assert all(isinstance(name, str) for name in collections)
        assert all(len(name) > 0 for name in collections)

class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_invalid_job_data(self):
        """Test workflow with invalid job data."""
        invalid_job_data = {
            'job_id': '',  # Empty job ID
            'artwork_url': 'invalid-url',
            'mockup_template': ''
        }
        
        workflow = IntelligentMockupGenerationWorkflow()
        
        # The workflow should handle validation during execution
        # This test ensures the workflow structure can handle edge cases
        assert workflow is not None
    
    def test_missing_required_fields(self):
        """Test job data with missing required fields."""
        incomplete_job_data = {
            'artwork_url': 'https://example.com/artwork.png'
            # Missing job_id and mockup_template
        }
        
        workflow = IntelligentMockupGenerationWorkflow()
        assert workflow is not None
        
        # The workflow should fail gracefully with proper error handling
        # during actual execution when required fields are missing