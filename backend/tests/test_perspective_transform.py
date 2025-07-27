"""
Unit tests for the Perspective Transformation Service.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import cv2

from src.services.perspective_transform import (
    PerspectiveTransformService,
    PerspectiveTransformConfig,
    TransformationResult,
    PerspectiveTransformError,
    MockPerspectiveTransformService,
    create_mock_perspective_service
)
from src.services.object_detection import BoundingBox

class TestPerspectiveTransformConfig:
    """Tests for the PerspectiveTransformConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = PerspectiveTransformConfig()
        
        assert config.interpolation_method == cv2.INTER_LANCZOS4
        assert config.border_mode == cv2.BORDER_REFLECT
        assert config.quality_factor == 1.0
        assert config.padding_ratio == 0.05
        assert config.min_region_size == 50
        assert config.max_aspect_ratio_diff == 3.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = PerspectiveTransformConfig(
            interpolation_method=cv2.INTER_LINEAR,
            border_mode=cv2.BORDER_CONSTANT,
            quality_factor=1.5,
            padding_ratio=0.1,
            min_region_size=100,
            max_aspect_ratio_diff=2.0
        )
        
        assert config.interpolation_method == cv2.INTER_LINEAR
        assert config.border_mode == cv2.BORDER_CONSTANT
        assert config.quality_factor == 1.5
        assert config.padding_ratio == 0.1
        assert config.min_region_size == 100
        assert config.max_aspect_ratio_diff == 2.0

class TestTransformationResult:
    """Tests for the TransformationResult class."""
    
    def test_transformation_result_creation(self):
        """Test creating a transformation result."""
        test_image = Image.new('RGB', (100, 100), color='red')
        matrix = np.eye(3)
        source_corners = [(0, 0), (100, 0), (100, 100), (0, 100)]
        target_corners = [(10, 10), (110, 10), (110, 110), (10, 110)]
        
        result = TransformationResult(
            transformed_image=test_image,
            transformation_matrix=matrix,
            source_corners=source_corners,
            target_corners=target_corners,
            original_size=(100, 100),
            target_size=(100, 100)
        )
        
        assert result.transformed_image == test_image
        assert np.array_equal(result.transformation_matrix, matrix)
        assert result.source_corners == source_corners
        assert result.target_corners == target_corners
        assert result.original_size == (100, 100)
        assert result.target_size == (100, 100)

class TestPerspectiveTransformService:
    """Tests for the PerspectiveTransformService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_artwork = Image.new('RGB', (200, 150), color='blue')
        self.test_region = BoundingBox(50, 50, 100, 75, 0.9, "picture frame")
        self.mockup_size = (800, 600)
        self.config = PerspectiveTransformConfig()
        self.service = PerspectiveTransformService(self.config)
    
    def test_initialization(self):
        """Test service initialization."""
        service = PerspectiveTransformService(self.config)
        assert service.config == self.config
        
        # Test with default config
        default_service = PerspectiveTransformService()
        assert default_service.config is not None
    
    def test_validate_inputs_success(self):
        """Test input validation with valid inputs."""
        # Should not raise any exception
        self.service._validate_inputs(self.test_artwork, self.test_region, self.mockup_size)
    
    def test_validate_inputs_zero_dimensions(self):
        """Test input validation with zero-dimension artwork."""
        zero_artwork = Image.new('RGB', (0, 100), color='red')
        
        with pytest.raises(PerspectiveTransformError, match="zero dimensions"):
            self.service._validate_inputs(zero_artwork, self.test_region, self.mockup_size)
    
    def test_validate_inputs_small_region(self):
        """Test input validation with too small region."""
        small_region = BoundingBox(10, 10, 20, 20, 0.9, "small object")
        
        with pytest.raises(PerspectiveTransformError, match="too small"):
            self.service._validate_inputs(self.test_artwork, small_region, self.mockup_size)
    
    def test_validate_inputs_aspect_ratio_warning(self):
        """Test input validation logs warning for extreme aspect ratios."""
        # Create artwork with extreme aspect ratio
        extreme_artwork = Image.new('RGB', (1000, 10), color='red')
        
        with patch('src.services.perspective_transform.logger') as mock_logger:
            self.service._validate_inputs(extreme_artwork, self.test_region, self.mockup_size)
            mock_logger.warning.assert_called()
    
    def test_calculate_perspective_corners(self):
        """Test perspective corner calculation."""
        corners = self.service._calculate_perspective_corners(self.test_region)
        
        assert len(corners) == 4
        # Verify corners are roughly in the right positions
        assert corners[0][0] == self.test_region.x  # top-left x
        assert corners[0][1] == self.test_region.y  # top-left y
        
        # Other corners should have perspective distortion
        assert corners[1][0] != self.test_region.x + self.test_region.width  # top-right has distortion
        assert corners[2][0] == self.test_region.x + self.test_region.width  # bottom-right x
        assert corners[2][1] == self.test_region.y + self.test_region.height  # bottom-right y
    
    def test_calculate_source_corners(self):
        """Test source corner calculation."""
        corners = self.service._calculate_source_corners(self.test_artwork, self.test_region)
        
        assert len(corners) == 4
        aw, ah = self.test_artwork.size
        
        # Should be full artwork corners
        expected = [(0, 0), (aw, 0), (aw, ah), (0, ah)]
        assert corners == expected
    
    def test_calculate_transformation_matrix(self):
        """Test transformation matrix calculation."""
        source_corners = [(0, 0), (100, 0), (100, 100), (0, 100)]
        target_corners = [(10, 10), (110, 15), (115, 115), (5, 110)]
        
        matrix = self.service._calculate_transformation_matrix(source_corners, target_corners)
        
        assert matrix.shape == (3, 3)
        assert isinstance(matrix, np.ndarray)
        assert matrix.dtype in [np.float32, np.float64]  # Accept both float types
    
    @patch('src.services.perspective_transform.cv2')
    def test_apply_transformation(self, mock_cv2):
        """Test applying transformation to artwork."""
        # Mock OpenCV functions
        mock_cv2.cvtColor.side_effect = lambda img, code: img  # Pass through
        mock_cv2.resize.side_effect = lambda img, size, **kwargs: img  # Pass through
        mock_cv2.warpPerspective.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.COLOR_RGB2BGR = 0
        mock_cv2.COLOR_BGR2RGB = 0
        
        transform_matrix = np.eye(3)
        
        result = self.service._apply_transformation(
            self.test_artwork, transform_matrix, self.test_region, self.mockup_size
        )
        
        assert isinstance(result, Image.Image)
        mock_cv2.warpPerspective.assert_called_once()
    
    @patch('src.services.perspective_transform.cv2')
    def test_transform_artwork_to_region_success(self, mock_cv2):
        """Test successful artwork transformation."""
        # Mock OpenCV functions
        mock_cv2.cvtColor.side_effect = lambda img, code: img
        mock_cv2.warpPerspective.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
        mock_cv2.COLOR_RGB2BGR = 0
        mock_cv2.COLOR_BGR2RGB = 0
        
        result = self.service.transform_artwork_to_region(
            self.test_artwork, self.test_region, self.mockup_size
        )
        
        assert isinstance(result, TransformationResult)
        assert isinstance(result.transformed_image, Image.Image)
        assert result.original_size == self.test_artwork.size
        assert result.target_size == (int(self.test_region.width), int(self.test_region.height))
    
    @patch('src.services.perspective_transform.cv2')
    def test_transform_artwork_to_region_with_custom_corners(self, mock_cv2):
        """Test artwork transformation with custom perspective corners."""
        # Mock OpenCV functions
        mock_cv2.cvtColor.side_effect = lambda img, code: img
        mock_cv2.warpPerspective.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
        mock_cv2.COLOR_RGB2BGR = 0
        mock_cv2.COLOR_BGR2RGB = 0
        
        custom_corners = [(40, 40), (140, 45), (145, 130), (35, 125)]
        
        result = self.service.transform_artwork_to_region(
            self.test_artwork, self.test_region, self.mockup_size, custom_corners
        )
        
        assert isinstance(result, TransformationResult)
        assert result.target_corners == custom_corners
    
    def test_transform_artwork_to_region_validation_error(self):
        """Test transformation with invalid inputs."""
        invalid_region = BoundingBox(10, 10, 10, 10, 0.9, "too small")
        
        with pytest.raises(PerspectiveTransformError):
            self.service.transform_artwork_to_region(
                self.test_artwork, invalid_region, self.mockup_size
            )
    
    def test_create_composite_image_success(self):
        """Test successful image composition."""
        mockup_template = Image.new('RGB', self.mockup_size, color='white')
        transformed_artwork = Image.new('RGB', (100, 75), color='red')
        
        result = self.service.create_composite_image(
            mockup_template, transformed_artwork, self.test_region
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == mockup_template.size
    
    def test_create_composite_image_with_alpha(self):
        """Test image composition with alpha channel."""
        mockup_template = Image.new('RGB', self.mockup_size, color='white')
        transformed_artwork = Image.new('RGBA', (100, 75), color=(255, 0, 0, 128))
        
        result = self.service.create_composite_image(
            mockup_template, transformed_artwork, self.test_region
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == mockup_template.size
    
    def test_create_composite_image_oversized_artwork(self):
        """Test composition with artwork larger than mockup."""
        mockup_template = Image.new('RGB', (100, 100), color='white')
        large_artwork = Image.new('RGB', (200, 200), color='red')
        large_region = BoundingBox(10, 10, 150, 150, 0.9, "large region")
        
        result = self.service.create_composite_image(
            mockup_template, large_artwork, large_region
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == mockup_template.size
    
    def test_create_composite_image_edge_position(self):
        """Test composition with artwork at edge positions."""
        mockup_template = Image.new('RGB', (200, 200), color='white')
        artwork = Image.new('RGB', (50, 50), color='red')
        edge_region = BoundingBox(-10, -10, 60, 60, 0.9, "edge region")
        
        # Should handle negative positions gracefully
        result = self.service.create_composite_image(
            mockup_template, artwork, edge_region
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == mockup_template.size
    
    @patch('src.services.perspective_transform.cv2')
    def test_batch_transform_artworks_success(self, mock_cv2):
        """Test batch transformation of multiple artworks."""
        # Mock OpenCV functions
        mock_cv2.cvtColor.side_effect = lambda img, code: img
        mock_cv2.warpPerspective.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
        mock_cv2.COLOR_RGB2BGR = 0
        mock_cv2.COLOR_BGR2RGB = 0
        
        artworks = [
            Image.new('RGB', (100, 100), color='red'),
            Image.new('RGB', (150, 100), color='blue')
        ]
        regions = [
            BoundingBox(50, 50, 80, 80, 0.9, "frame1"),
            BoundingBox(200, 100, 120, 80, 0.8, "frame2")
        ]
        
        results = self.service.batch_transform_artworks(artworks, regions, self.mockup_size)
        
        assert len(results) == 2
        assert all(isinstance(result, TransformationResult) for result in results)
    
    def test_batch_transform_artworks_mismatched_counts(self):
        """Test batch transformation with mismatched artwork and region counts."""
        artworks = [Image.new('RGB', (100, 100), color='red')]
        regions = [
            BoundingBox(50, 50, 80, 80, 0.9, "frame1"),
            BoundingBox(200, 100, 120, 80, 0.8, "frame2")
        ]
        
        with pytest.raises(PerspectiveTransformError, match="must match"):
            self.service.batch_transform_artworks(artworks, regions, self.mockup_size)
    
    @patch('src.services.perspective_transform.cv2')
    def test_batch_transform_artworks_partial_failure(self, mock_cv2):
        """Test batch transformation with some failures."""
        # Mock OpenCV functions for successful transformation
        mock_cv2.cvtColor.side_effect = lambda img, code: img
        mock_cv2.warpPerspective.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_cv2.getPerspectiveTransform.return_value = np.eye(3)
        mock_cv2.COLOR_RGB2BGR = 0
        mock_cv2.COLOR_BGR2RGB = 0
        
        artworks = [
            Image.new('RGB', (100, 100), color='red'),
            Image.new('RGB', (150, 100), color='blue')
        ]
        regions = [
            BoundingBox(50, 50, 80, 80, 0.9, "frame1"),
            BoundingBox(200, 100, 10, 10, 0.8, "too_small")  # This will fail validation
        ]
        
        with patch('src.services.perspective_transform.logger') as mock_logger:
            results = self.service.batch_transform_artworks(artworks, regions, self.mockup_size)
            
            # Should have one successful result and one failure
            assert len(results) == 1
            mock_logger.warning.assert_called()

class TestMockPerspectiveTransformService:
    """Tests for the MockPerspectiveTransformService class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_artwork = Image.new('RGB', (200, 150), color='blue')
        self.test_region = BoundingBox(50, 50, 100, 75, 0.9, "picture frame")
        self.mockup_size = (800, 600)
        self.mock_service = MockPerspectiveTransformService()
    
    def test_mock_transform_artwork_to_region(self):
        """Test mock artwork transformation."""
        result = self.mock_service.transform_artwork_to_region(
            self.test_artwork, self.test_region, self.mockup_size
        )
        
        assert isinstance(result, TransformationResult)
        assert isinstance(result.transformed_image, Image.Image)
        assert result.target_size == (int(self.test_region.width), int(self.test_region.height))
        assert result.transformed_image.size == result.target_size
    
    def test_mock_create_composite_image(self):
        """Test mock image composition."""
        mockup_template = Image.new('RGB', self.mockup_size, color='white')
        transformed_artwork = Image.new('RGB', (100, 75), color='red')
        
        result = self.mock_service.create_composite_image(
            mockup_template, transformed_artwork, self.test_region
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == mockup_template.size
    
    def test_mock_create_composite_image_oversized(self):
        """Test mock composition with oversized artwork."""
        mockup_template = Image.new('RGB', (100, 100), color='white')
        large_artwork = Image.new('RGB', (200, 200), color='red')
        large_region = BoundingBox(10, 10, 80, 80, 0.9, "large region")
        
        result = self.mock_service.create_composite_image(
            mockup_template, large_artwork, large_region
        )
        
        assert isinstance(result, Image.Image)
        assert result.size == mockup_template.size
    
    def test_mock_batch_transform_artworks(self):
        """Test mock batch transformation."""
        artworks = [
            Image.new('RGB', (100, 100), color='red'),
            Image.new('RGB', (150, 100), color='blue')
        ]
        regions = [
            BoundingBox(50, 50, 80, 80, 0.9, "frame1"),
            BoundingBox(200, 100, 120, 80, 0.8, "frame2")
        ]
        
        results = self.mock_service.batch_transform_artworks(artworks, regions, self.mockup_size)
        
        assert len(results) == 2
        assert all(isinstance(result, TransformationResult) for result in results)
    
    def test_create_mock_perspective_service(self):
        """Test creating mock perspective service."""
        service = create_mock_perspective_service()
        
        assert isinstance(service, MockPerspectiveTransformService)
        assert hasattr(service, 'config')

class TestExceptions:
    """Tests for custom exceptions."""
    
    def test_perspective_transform_error(self):
        """Test PerspectiveTransformError exception."""
        with pytest.raises(PerspectiveTransformError, match="Test error"):
            raise PerspectiveTransformError("Test error")

class TestIntegration:
    """Integration tests to ensure compatibility with existing systems."""
    
    def test_service_isolation(self):
        """Test that perspective transform service doesn't interfere with imports."""
        from src.services.perspective_transform import PerspectiveTransformService
        
        service = PerspectiveTransformService()
        assert service is not None
        
        # Verify we can still import other services
        try:
            import src.services.object_detection
            import src.services.bfl_api
        except ImportError:
            pass  # Services might not be importable in test environment
    
    def test_opencv_compatibility(self):
        """Test OpenCV compatibility and basic operations."""
        import cv2
        import numpy as np
        
        # Test basic OpenCV operations
        test_array = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test color conversion
        try:
            converted = cv2.cvtColor(test_array, cv2.COLOR_BGR2RGB)
            assert converted.shape == test_array.shape
        except Exception as e:
            pytest.skip(f"OpenCV color conversion not available: {e}")
        
        # Test perspective transformation functions exist
        assert hasattr(cv2, 'getPerspectiveTransform')
        assert hasattr(cv2, 'warpPerspective')
    
    def test_pil_opencv_interop(self):
        """Test PIL and OpenCV interoperability."""
        from PIL import Image
        import numpy as np
        
        # Test PIL to numpy conversion
        pil_image = Image.new('RGB', (100, 100), color='red')
        np_array = np.array(pil_image)
        
        assert np_array.shape == (100, 100, 3)
        assert np_array.dtype == np.uint8
        
        # Test numpy to PIL conversion
        converted_back = Image.fromarray(np_array)
        assert converted_back.size == pil_image.size
        assert converted_back.mode == pil_image.mode
    
    def test_memory_usage_perspective_transform(self):
        """Test memory usage doesn't increase dramatically."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create multiple service instances
        services = [PerspectiveTransformService() for _ in range(10)]
        
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # Should not use excessive memory
        assert memory_increase < 50 * 1024 * 1024  # Less than 50MB increase
        
        # Cleanup
        del services

class TestRegressionCompatibility:
    """Regression tests to ensure existing image processing still works."""
    
    def test_existing_pil_operations(self):
        """Test that existing PIL operations still work."""
        from PIL import Image
        
        # Test basic PIL operations that existing code might use
        test_image = Image.new('RGB', (100, 100), color='white')
        
        # Resize operation
        resized = test_image.resize((50, 50), Image.Resampling.LANCZOS)
        assert resized.size == (50, 50)
        
        # Paste operation
        red_image = Image.new('RGB', (25, 25), color='red')
        test_image.paste(red_image, (10, 10))
        
        # Copy operation
        copied = test_image.copy()
        assert copied.size == test_image.size
    
    def test_storage_compatibility_simulation(self):
        """Simulate compatibility with storage.py image handling patterns."""
        from PIL import Image
        import io
        
        # Simulate typical storage.py operations
        test_image = Image.new('RGB', (200, 200), color='blue')
        
        # Test saving to bytes (common in storage operations)
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        # Test loading from bytes
        loaded_image = Image.open(img_bytes)
        assert loaded_image.size == test_image.size
        
        # Test format conversions
        if test_image.mode != 'RGB':
            rgb_image = test_image.convert('RGB')
            assert rgb_image.mode == 'RGB'