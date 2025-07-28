"""
Tests for OpenCV detection integration with workflows.
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.services.object_detection import (
    ObjectDetectionConfig,
    BoundingBox,
    NoSuitableRegionsError
)
from src.services.opencv_detection.compatibility_wrapper import (
    ObjectDetectionCompatibilityWrapper,
    create_object_detection_service
)
from src.services.feature_flags import FeatureFlags


class TestWorkflowIntegration:
    """Test OpenCV detection integration with existing workflows."""
    
    def test_compatibility_wrapper_interface(self):
        """Test that wrapper provides exact same interface as original service."""
        # Create wrapper
        wrapper = ObjectDetectionCompatibilityWrapper(use_opencv=True)
        
        # Check all required methods exist
        assert hasattr(wrapper, 'detect_objects')
        assert hasattr(wrapper, 'find_suitable_regions')
        assert hasattr(wrapper, 'config')
        
        # Check config is correct type
        assert isinstance(wrapper.config, ObjectDetectionConfig)
        
    def test_factory_function_with_feature_flag(self):
        """Test factory function respects feature flags."""
        # Mock feature flag to return True
        with patch('src.services.feature_flags.should_use_opencv_detection', return_value=True):
            service = create_object_detection_service(job_id='test-job-123')
            assert service.use_opencv is True
            
        # Mock feature flag to return False
        with patch('src.services.feature_flags.should_use_opencv_detection', return_value=False):
            service = create_object_detection_service(job_id='test-job-456')
            assert service.use_opencv is False
            
    def test_bounding_box_compatibility(self):
        """Test that returned BoundingBox objects are compatible."""
        # Create test image
        image = Image.new('RGB', (400, 300), 'white')
        
        # Create wrapper with OpenCV
        wrapper = ObjectDetectionCompatibilityWrapper(use_opencv=True)
        
        # Mock the OpenCV service to return predictable results
        mock_opencv_box = Mock()
        mock_opencv_box.x = 10
        mock_opencv_box.y = 20
        mock_opencv_box.width = 100
        mock_opencv_box.height = 150
        mock_opencv_box.confidence = 0.85
        mock_opencv_box.label = "test_region"
        
        wrapper._service.detect_objects = Mock(return_value=[mock_opencv_box])
        
        # Get results
        results = wrapper.detect_objects(image)
        
        # Verify BoundingBox format
        assert len(results) == 1
        box = results[0]
        assert isinstance(box, BoundingBox)
        assert box.x == 10
        assert box.y == 20
        assert box.width == 100
        assert box.height == 150
        assert box.confidence == 0.85
        assert box.label == "test_region"
        assert hasattr(box, 'to_dict')
        assert hasattr(box, 'get_corners')
        
    def test_error_compatibility(self):
        """Test that errors are properly converted."""
        from src.services.opencv_detection.opencv_detection_service import (
            NoSuitableRegionsError as OpenCVNoSuitableRegionsError
        )
        
        # Create wrapper with OpenCV
        wrapper = ObjectDetectionCompatibilityWrapper(use_opencv=True)
        
        # Mock to raise OpenCV error
        wrapper._service.find_suitable_regions = Mock(
            side_effect=OpenCVNoSuitableRegionsError("No regions found")
        )
        
        # Verify it's converted to DETR error type
        image = Image.new('RGB', (100, 100), 'white')
        with pytest.raises(NoSuitableRegionsError):
            wrapper.find_suitable_regions(image)
            
    def test_workflow_activity_mock(self):
        """Test workflow activity integration pattern."""
        # Simulate workflow activity usage
        job_id = "test-job-789"
        
        # Mock image bytes (as would come from workflow)
        image = Image.new('RGB', (400, 300), 'white')
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        template_bytes = img_byte_arr.getvalue()
        
        # Simulate activity code pattern
        template_image = Image.open(io.BytesIO(template_bytes))
        
        # Create service with feature flag
        with patch('src.services.feature_flags.should_use_opencv_detection', return_value=True):
            detection_service = create_object_detection_service(job_id=job_id)
            
        # Verify service type
        assert detection_service.use_opencv is True
        
        # Mock detection results
        mock_regions = [
            BoundingBox(50, 50, 300, 200, 0.9, "mockup_region")
        ]
        detection_service.find_suitable_regions = Mock(return_value=mock_regions)
        
        # Run detection (as workflow would)
        detected_regions = detection_service.find_suitable_regions(template_image)
        
        # Verify results format (as workflow expects)
        assert len(detected_regions) == 1
        region = detected_regions[0]
        assert hasattr(region, 'to_dict')
        region_dict = region.to_dict()
        assert 'x' in region_dict
        assert 'y' in region_dict
        assert 'width' in region_dict
        assert 'height' in region_dict
        assert 'confidence' in region_dict
        assert 'label' in region_dict
        
    def test_config_conversion(self):
        """Test DETR config to OpenCV config conversion."""
        # Create DETR config with specific settings
        detr_config = ObjectDetectionConfig(
            confidence_threshold=0.8,
            max_detections=5,
            target_classes=["picture frame", "tv", "laptop"]
        )
        
        # Create wrapper
        wrapper = ObjectDetectionCompatibilityWrapper(config=detr_config, use_opencv=True)
        
        # Verify OpenCV config was created correctly
        opencv_config = wrapper.opencv_config
        assert opencv_config.confidence_threshold == 0.8
        assert opencv_config.max_detections == 5
        assert 'template' in opencv_config.enabled_detectors  # Should enable template detector
        
    def test_feature_flag_percentage_rollout(self):
        """Test percentage-based rollout."""
        flags = FeatureFlags()
        
        # Test 0% rollout
        flags.update(FeatureFlags.OPENCV_DETECTION_PERCENTAGE, 0)
        assert flags.should_use_opencv_detection("job-1") is False
        
        # Test 100% rollout
        flags.update(FeatureFlags.OPENCV_DETECTION_PERCENTAGE, 100)
        assert flags.should_use_opencv_detection("job-2") is True
        
        # Test 50% rollout (deterministic based on job ID)
        flags.update(FeatureFlags.OPENCV_DETECTION_PERCENTAGE, 50)
        # Some jobs should use OpenCV, some shouldn't
        job_results = [flags.should_use_opencv_detection(f"job-{i}") for i in range(20)]
        assert any(job_results)  # At least some True
        assert not all(job_results)  # Not all True