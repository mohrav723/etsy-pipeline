"""
Unit tests for the Object Detection Service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import torch
import numpy as np

from src.services.object_detection import (
    ObjectDetectionService,
    ObjectDetectionConfig,
    BoundingBox,
    NoSuitableRegionsError,
    ObjectDetectionError,
    MockObjectDetectionService,
    create_mock_detection_service
)

class TestBoundingBox:
    """Tests for the BoundingBox class."""
    
    def test_bounding_box_creation(self):
        """Test creating a bounding box."""
        bbox = BoundingBox(10, 20, 100, 150, 0.85, "picture frame")
        
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 150
        assert bbox.confidence == 0.85
        assert bbox.label == "picture frame"
    
    def test_to_dict(self):
        """Test converting bounding box to dictionary."""
        bbox = BoundingBox(10, 20, 100, 150, 0.85, "picture frame")
        result = bbox.to_dict()
        
        expected = {
            'x': 10,
            'y': 20,
            'width': 100,
            'height': 150,
            'confidence': 0.85,
            'label': "picture frame"
        }
        
        assert result == expected
    
    def test_get_corners(self):
        """Test getting corner coordinates."""
        bbox = BoundingBox(10, 20, 100, 150, 0.85, "picture frame")
        corners = bbox.get_corners()
        
        expected = (
            (10, 20),      # top-left
            (110, 20),     # top-right
            (110, 170),    # bottom-right
            (10, 170)      # bottom-left
        )
        
        assert corners == expected

class TestObjectDetectionConfig:
    """Tests for the ObjectDetectionConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ObjectDetectionConfig()
        
        assert config.confidence_threshold == 0.7
        assert config.model_name == "facebook/detr-resnet-50"
        assert config.max_detections == 10
        assert "picture frame" in config.target_classes
        assert "tv" in config.target_classes
    
    def test_custom_config(self):
        """Test custom configuration values."""
        custom_classes = ["laptop", "phone"]
        config = ObjectDetectionConfig(
            confidence_threshold=0.8,
            model_name="custom-model",
            target_classes=custom_classes,
            max_detections=5
        )
        
        assert config.confidence_threshold == 0.8
        assert config.model_name == "custom-model"
        assert config.target_classes == custom_classes
        assert config.max_detections == 5

class TestObjectDetectionService:
    """Tests for the ObjectDetectionService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_image = Image.new('RGB', (800, 600), color='white')
        self.config = ObjectDetectionConfig(confidence_threshold=0.5)
    
    def test_initialization(self):
        """Test service initialization."""
        service = ObjectDetectionService(self.config)
        
        assert service.config == self.config
        assert service._processor is None
        assert service._model is None
    
    def test_initialization_with_default_config(self):
        """Test service initialization with default config."""
        service = ObjectDetectionService()
        
        assert service.config is not None
        assert service.config.confidence_threshold == 0.7
    
    @patch('src.services.object_detection.DetrImageProcessor')
    @patch('src.services.object_detection.DetrForObjectDetection')
    def test_load_model(self, mock_model_class, mock_processor_class):
        """Test model loading."""
        # Setup mocks
        mock_processor = Mock()
        mock_model = Mock()
        mock_processor_class.from_pretrained.return_value = mock_processor
        mock_model_class.from_pretrained.return_value = mock_model
        
        service = ObjectDetectionService(self.config)
        service._load_model()
        
        # Verify model and processor were loaded
        mock_processor_class.from_pretrained.assert_called_once_with(self.config.model_name)
        mock_model_class.from_pretrained.assert_called_once_with(self.config.model_name)
        mock_model.to.assert_called_once()
        mock_model.eval.assert_called_once()
        
        assert service._processor == mock_processor
        assert service._model == mock_model
    
    @patch('src.services.object_detection.DetrImageProcessor')
    @patch('src.services.object_detection.DetrForObjectDetection')
    def test_load_model_failure(self, mock_model_class, mock_processor_class):
        """Test model loading failure."""
        mock_processor_class.from_pretrained.side_effect = Exception("Model not found")
        
        service = ObjectDetectionService(self.config)
        
        with pytest.raises(Exception, match="Model not found"):
            service._load_model()
    
    @patch('src.services.object_detection.torch')
    def test_detect_objects_success(self, mock_torch):
        """Test successful object detection."""
        service = ObjectDetectionService(self.config)
        
        # Mock the model components
        mock_processor = Mock()
        mock_model = Mock()
        service._processor = mock_processor
        service._model = mock_model
        
        # Mock model config
        mock_model.config.id2label = {0: "picture frame", 1: "laptop"}
        
        # Mock processor inputs and outputs  
        mock_tensor = Mock()
        mock_tensor.to.return_value = mock_tensor
        mock_processor.return_value = {"input_ids": mock_tensor}
        
        # Mock model output
        mock_outputs = Mock()
        mock_model.return_value = mock_outputs
        
        # Mock post-processing results
        mock_results = {
            "scores": torch.tensor([0.85, 0.75]),
            "labels": torch.tensor([0, 1]),
            "boxes": torch.tensor([[400, 300, 200, 150], [600, 200, 150, 100]])  # center_x, center_y, width, height
        }
        mock_processor.post_process_object_detection.return_value = [mock_results]
        
        # Mock torch.tensor for target_sizes
        mock_torch.tensor.return_value = torch.tensor([[600, 800]])  # height, width
        mock_torch.device.return_value = "cpu"
        
        result = service.detect_objects(self.test_image)
        
        assert len(result) == 2
        assert result[0].label == "picture frame"
        assert abs(result[0].confidence - 0.85) < 1e-6
        assert result[1].label == "laptop"
        assert abs(result[1].confidence - 0.75) < 1e-6
    
    @patch('src.services.object_detection.torch')
    def test_detect_objects_with_target_classes_filter(self, mock_torch):
        """Test object detection with target class filtering."""
        config = ObjectDetectionConfig(target_classes=["picture frame"])
        service = ObjectDetectionService(config)
        
        # Mock the model components
        mock_processor = Mock()
        mock_model = Mock()
        service._processor = mock_processor
        service._model = mock_model
        
        # Mock model config
        mock_model.config.id2label = {0: "picture frame", 1: "car"}  # car should be filtered out
        
        # Mock processor inputs and outputs  
        mock_tensor = Mock()
        mock_tensor.to.return_value = mock_tensor
        mock_processor.return_value = {"input_ids": mock_tensor}
        mock_model.return_value = Mock()
        
        # Mock post-processing results
        mock_results = {
            "scores": torch.tensor([0.85, 0.75]),
            "labels": torch.tensor([0, 1]),
            "boxes": torch.tensor([[400, 300, 200, 150], [600, 200, 150, 100]])
        }
        mock_processor.post_process_object_detection.return_value = [mock_results]
        mock_torch.tensor.return_value = torch.tensor([[600, 800]])
        mock_torch.device.return_value = "cpu"
        
        result = service.detect_objects(self.test_image)
        
        # Only picture frame should be included
        assert len(result) == 1
        assert result[0].label == "picture frame"
    
    @patch('src.services.object_detection.torch')
    def test_detect_objects_max_detections_limit(self, mock_torch):
        """Test max detections limit."""
        config = ObjectDetectionConfig(max_detections=1)
        service = ObjectDetectionService(config)
        
        # Mock the model components
        mock_processor = Mock()
        mock_model = Mock()
        service._processor = mock_processor
        service._model = mock_model
        
        # Mock model config
        mock_model.config.id2label = {0: "picture frame", 1: "laptop"}
        
        # Mock processor inputs and outputs  
        mock_tensor = Mock()
        mock_tensor.to.return_value = mock_tensor
        mock_processor.return_value = {"input_ids": mock_tensor}
        mock_model.return_value = Mock()
        
        # Mock post-processing results with multiple detections
        mock_results = {
            "scores": torch.tensor([0.85, 0.75]),
            "labels": torch.tensor([0, 1]),
            "boxes": torch.tensor([[400, 300, 200, 150], [600, 200, 150, 100]])
        }
        mock_processor.post_process_object_detection.return_value = [mock_results]
        mock_torch.tensor.return_value = torch.tensor([[600, 800]])
        mock_torch.device.return_value = "cpu"
        
        result = service.detect_objects(self.test_image)
        
        # Only one detection should be returned due to limit
        assert len(result) == 1
    
    def test_detect_objects_failure(self):
        """Test object detection failure."""
        service = ObjectDetectionService(self.config)
        
        # Mock model loading to fail
        with patch.object(service, '_load_model', side_effect=Exception("Model loading failed")):
            with pytest.raises(Exception):
                service.detect_objects(self.test_image)
    
    def test_find_suitable_regions_success(self):
        """Test finding suitable regions successfully."""
        service = ObjectDetectionService(self.config)
        
        # Mock detect_objects to return mock detections
        mock_detections = [
            BoundingBox(100, 100, 200, 200, 0.9, "picture frame"),  # Large enough
            BoundingBox(50, 50, 10, 10, 0.8, "small object")        # Too small
        ]
        
        with patch.object(service, 'detect_objects', return_value=mock_detections):
            result = service.find_suitable_regions(self.test_image)
            
            # Only the large detection should be returned
            assert len(result) == 1
            assert result[0].label == "picture frame"
            assert result[0].confidence == 0.9
    
    def test_find_suitable_regions_no_detections(self):
        """Test finding suitable regions when no objects are detected."""
        service = ObjectDetectionService(self.config)
        
        with patch.object(service, 'detect_objects', return_value=[]):
            with pytest.raises(NoSuitableRegionsError, match="No suitable regions detected"):
                service.find_suitable_regions(self.test_image)
    
    def test_find_suitable_regions_all_too_small(self):
        """Test finding suitable regions when all detections are too small."""
        service = ObjectDetectionService(self.config)
        
        # All detections are too small (less than 1% of image area)
        mock_detections = [
            BoundingBox(50, 50, 5, 5, 0.9, "small object 1"),
            BoundingBox(100, 100, 3, 3, 0.8, "small object 2")
        ]
        
        with patch.object(service, 'detect_objects', return_value=mock_detections):
            with pytest.raises(NoSuitableRegionsError, match="none are large enough"):
                service.find_suitable_regions(self.test_image)
    
    def test_find_suitable_regions_sorted_by_confidence(self):
        """Test that suitable regions are sorted by confidence."""
        service = ObjectDetectionService(self.config)
        
        mock_detections = [
            BoundingBox(100, 100, 200, 200, 0.7, "frame 1"),
            BoundingBox(300, 300, 200, 200, 0.9, "frame 2"),
            BoundingBox(500, 500, 200, 200, 0.8, "frame 3")
        ]
        
        with patch.object(service, 'detect_objects', return_value=mock_detections):
            result = service.find_suitable_regions(self.test_image)
            
            # Should be sorted by confidence (highest first)
            assert len(result) == 3
            assert result[0].confidence == 0.9
            assert result[1].confidence == 0.8
            assert result[2].confidence == 0.7
    
    def test_find_suitable_regions_detection_error(self):
        """Test finding suitable regions when detection fails."""
        service = ObjectDetectionService(self.config)
        
        with patch.object(service, 'detect_objects', side_effect=Exception("Detection failed")):
            with pytest.raises(ObjectDetectionError, match="Failed to find suitable regions"):
                service.find_suitable_regions(self.test_image)

class TestMockObjectDetectionService:
    """Tests for the MockObjectDetectionService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_image = Image.new('RGB', (800, 600), color='white')
        self.mock_service = MockObjectDetectionService()
    
    def test_mock_detect_objects(self):
        """Test mock object detection."""
        result = self.mock_service.detect_objects(self.test_image)
        
        assert len(result) == 2
        assert result[0].label == "picture frame"
        assert result[1].label == "laptop"
        assert all(bbox.confidence > 0 for bbox in result)
    
    def test_mock_find_suitable_regions(self):
        """Test mock find suitable regions."""
        result = self.mock_service.find_suitable_regions(self.test_image)
        
        assert len(result) == 2
        assert all(isinstance(bbox, BoundingBox) for bbox in result)
    
    def test_create_mock_detection_service(self):
        """Test creating mock detection service."""
        service = create_mock_detection_service()
        
        assert isinstance(service, MockObjectDetectionService)
        assert hasattr(service, 'config')

class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_object_detection_error(self):
        """Test ObjectDetectionError exception."""
        with pytest.raises(ObjectDetectionError, match="Test error"):
            raise ObjectDetectionError("Test error")
    
    def test_no_suitable_regions_error(self):
        """Test NoSuitableRegionsError exception."""
        with pytest.raises(NoSuitableRegionsError, match="No regions found"):
            raise NoSuitableRegionsError("No regions found")
    
    def test_no_suitable_regions_error_inheritance(self):
        """Test that NoSuitableRegionsError inherits from ObjectDetectionError."""
        assert issubclass(NoSuitableRegionsError, ObjectDetectionError)

class TestIntegration:
    """Integration tests to ensure isolation from existing services."""
    
    def test_service_isolation(self):
        """Test that object detection service doesn't interfere with imports."""
        # This test ensures we can import the service without side effects
        from src.services.object_detection import ObjectDetectionService
        
        service = ObjectDetectionService()
        assert service is not None
        
        # Verify we can still import other services
        try:
            import src.services.bfl_api  # This should not fail
        except ImportError:
            pass  # bfl_api might not be importable, that's ok
    
    def test_memory_usage(self):
        """Test that service creation doesn't cause memory issues."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create multiple service instances
        services = [ObjectDetectionService() for _ in range(10)]
        
        # Memory shouldn't increase dramatically (no model loading yet)
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # Allow for some memory increase but not excessive
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase
        
        # Cleanup
        del services
    
    def test_torch_compatibility(self):
        """Test that torch usage doesn't conflict with existing dependencies."""
        import torch
        
        # Verify basic torch operations work
        tensor = torch.tensor([1, 2, 3])
        assert tensor.sum().item() == 6
        
        # Verify device detection works
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        assert device.type in ["cuda", "cpu"]