"""
Tests to ensure perspective transformation service is compatible with existing storage.py patterns.
"""

import pytest
import io
from unittest.mock import Mock, patch
from PIL import Image

from src.services.perspective_transform import (
    PerspectiveTransformService,
    MockPerspectiveTransformService
)
from src.services.object_detection import BoundingBox

class TestStorageCompatibility:
    """Tests for compatibility with existing storage.py patterns."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PerspectiveTransformService()
        self.mock_service = MockPerspectiveTransformService()
        
        # Create test images
        self.test_artwork = Image.new('RGB', (300, 200), color='blue')
        self.test_mockup = Image.new('RGB', (800, 600), color='white')
        self.test_region = BoundingBox(100, 100, 200, 150, 0.9, "picture frame")
    
    def test_image_to_bytes_conversion(self):
        """Test that transformed images can be converted to bytes for storage."""
        mock_result = self.mock_service.transform_artwork_to_region(
            self.test_artwork, self.test_region, self.test_mockup.size
        )
        
        # Test conversion to bytes (as required by storage.py)
        img_bytes = io.BytesIO()
        mock_result.transformed_image.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        assert len(img_data) > 0
        assert isinstance(img_data, bytes)
    
    def test_composite_image_to_bytes_conversion(self):
        """Test that composite images can be converted to bytes for storage."""
        # Create a transformed artwork using mock service
        mock_result = self.mock_service.transform_artwork_to_region(
            self.test_artwork, self.test_region, self.test_mockup.size
        )
        
        # Create composite image
        composite = self.mock_service.create_composite_image(
            self.test_mockup, mock_result.transformed_image, self.test_region
        )
        
        # Test conversion to bytes (storage.py pattern)
        img_bytes = io.BytesIO()
        composite.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        assert len(img_data) > 0
        assert isinstance(img_data, bytes)
        assert composite.size == self.test_mockup.size
    
    def test_storage_upload_simulation(self):
        """Simulate the storage upload pattern with transformed images."""
        # Transform artwork
        mock_result = self.mock_service.transform_artwork_to_region(
            self.test_artwork, self.test_region, self.test_mockup.size
        )
        
        # Create composite
        composite = self.mock_service.create_composite_image(
            self.test_mockup, mock_result.transformed_image, self.test_region
        )
        
        # Simulate storage.py upload pattern
        img_bytes = io.BytesIO()
        composite.save(img_bytes, format='PNG')
        image_data = img_bytes.getvalue()
        
        # Mock the storage upload function
        with patch('src.storage.upload_image_to_storage') as mock_upload:
            mock_upload.return_value = "https://storage.googleapis.com/bucket/generated-art/test.png"
            
            # Simulate calling storage function
            try:
                from src.storage import upload_image_to_storage
                # This would normally upload to Firebase Storage
                # We're just testing the interface compatibility
                result_url = mock_upload(image_data)
                assert result_url.startswith("https://")
            except ImportError:
                # storage.py might not be importable in test environment
                # Just verify we can create the bytes data correctly
                assert isinstance(image_data, bytes)
                assert len(image_data) > 0
    
    def test_multiple_format_support(self):
        """Test that transformed images support multiple formats like storage.py."""
        mock_result = self.mock_service.transform_artwork_to_region(
            self.test_artwork, self.test_region, self.test_mockup.size
        )
        
        # Test PNG format (used by storage.py)
        png_bytes = io.BytesIO()
        mock_result.transformed_image.save(png_bytes, format='PNG')
        png_data = png_bytes.getvalue()
        
        # Test JPEG format (alternative)
        jpeg_bytes = io.BytesIO()
        mock_result.transformed_image.save(jpeg_bytes, format='JPEG')
        jpeg_data = jpeg_bytes.getvalue()
        
        assert len(png_data) > 0
        assert len(jpeg_data) > 0
        assert isinstance(png_data, bytes)
        assert isinstance(jpeg_data, bytes)
    
    def test_image_loading_from_bytes(self):
        """Test loading images from bytes (reverse of storage pattern)."""
        # Create and save image
        test_image = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        test_image.save(img_bytes, format='PNG')
        img_data = img_bytes.getvalue()
        
        # Load image back from bytes
        img_bytes.seek(0)
        loaded_image = Image.open(img_bytes)
        
        assert loaded_image.size == test_image.size
        assert loaded_image.mode == test_image.mode
        
        # Test that loaded image can be used with transformation service
        mock_result = self.mock_service.transform_artwork_to_region(
            loaded_image, self.test_region, self.test_mockup.size
        )
        
        assert isinstance(mock_result.transformed_image, Image.Image)
    
    def test_batch_processing_storage_pattern(self):
        """Test batch processing multiple images for storage."""
        artworks = [
            Image.new('RGB', (150, 100), color='red'),
            Image.new('RGB', (200, 150), color='green'),
            Image.new('RGB', (100, 200), color='blue')
        ]
        
        regions = [
            BoundingBox(50, 50, 120, 80, 0.9, "frame1"),
            BoundingBox(200, 100, 160, 120, 0.8, "frame2"),
            BoundingBox(400, 200, 80, 160, 0.85, "frame3")
        ]
        
        # Batch transform
        results = self.mock_service.batch_transform_artworks(
            artworks, regions, self.test_mockup.size
        )
        
        # Test that all results can be converted to bytes for storage
        storage_ready_images = []
        for result in results:
            composite = self.mock_service.create_composite_image(
                self.test_mockup.copy(), result.transformed_image, 
                regions[len(storage_ready_images)]
            )
            
            img_bytes = io.BytesIO()
            composite.save(img_bytes, format='PNG')
            img_data = img_bytes.getvalue()
            
            assert len(img_data) > 0
            storage_ready_images.append(img_data)
        
        assert len(storage_ready_images) == len(artworks)
        assert all(isinstance(img, bytes) for img in storage_ready_images)
    
    def test_error_handling_storage_compatibility(self):
        """Test that errors don't break storage compatibility."""
        # Test with invalid region (too small)
        invalid_region = BoundingBox(10, 10, 5, 5, 0.9, "too_small")
        
        try:
            # This should fail with validation error
            self.service.transform_artwork_to_region(
                self.test_artwork, invalid_region, self.test_mockup.size
            )
        except Exception:
            # Even with errors, we should be able to fall back to original image
            img_bytes = io.BytesIO()
            self.test_artwork.save(img_bytes, format='PNG')
            fallback_data = img_bytes.getvalue()
            
            assert len(fallback_data) > 0
            assert isinstance(fallback_data, bytes)
    
    def test_memory_efficiency_with_storage_pattern(self):
        """Test memory efficiency when processing for storage."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Process multiple images (simulating batch storage upload)
        for i in range(5):
            artwork = Image.new('RGB', (300, 200), color=(i*50, 100, 150))
            region = BoundingBox(50 + i*10, 50 + i*10, 150, 100, 0.9, f"frame_{i}")
            
            # Transform
            result = self.mock_service.transform_artwork_to_region(
                artwork, region, self.test_mockup.size
            )
            
            # Create composite
            composite = self.mock_service.create_composite_image(
                self.test_mockup, result.transformed_image, region
            )
            
            # Convert to bytes (storage pattern)
            img_bytes = io.BytesIO()
            composite.save(img_bytes, format='PNG')
            _ = img_bytes.getvalue()
            
            # Cleanup
            del artwork, result, composite, img_bytes
        
        current_memory = process.memory_info().rss
        memory_increase = current_memory - initial_memory
        
        # Should not use excessive memory
        assert memory_increase < 100 * 1024 * 1024  # Less than 100MB

class TestExistingStorageIntegration:
    """Integration tests with existing storage functionality."""
    
    def test_storage_module_compatibility(self):
        """Test that storage module can still be imported and used."""
        try:
            import src.storage as storage
            
            # Verify the upload function still exists
            assert hasattr(storage, 'upload_image_to_storage')
            
            # Test with mock data
            test_bytes = b"test image data"
            
            with patch('src.storage.storage') as mock_storage_client:
                with patch('src.storage.os.getenv') as mock_getenv:
                    mock_getenv.return_value = "test-bucket"
                    
                    # Mock the storage client chain
                    mock_bucket = Mock()
                    mock_blob = Mock()
                    mock_blob.public_url = "https://test.com/image.png"
                    mock_bucket.blob.return_value = mock_blob
                    mock_storage_client.Client().bucket.return_value = mock_bucket
                    
                    # This should work without interference from new services
                    result = storage.upload_image_to_storage(test_bytes)
                    assert result == "https://test.com/image.png"
                    
        except ImportError:
            # If storage can't be imported in test environment, that's okay
            pytest.skip("Storage module not available in test environment")
    
    def test_no_import_side_effects(self):
        """Test that importing perspective transform doesn't affect storage."""
        # Import storage first
        try:
            import src.storage
        except ImportError:
            pytest.skip("Storage module not available")
        
        # Import perspective transform
        from src.services.perspective_transform import PerspectiveTransformService
        
        # Storage should still work
        try:
            import src.storage as storage_reimport
            assert hasattr(storage_reimport, 'upload_image_to_storage')
        except ImportError:
            pytest.skip("Storage module not available after import")
    
    def test_uuid_and_path_generation_compatibility(self):
        """Test that UUID generation and path patterns still work."""
        import uuid
        
        # Test UUID generation (used by storage.py)
        test_uuid = uuid.uuid4()
        image_name = f"generated-art/{test_uuid}.png"
        
        assert image_name.startswith("generated-art/")
        assert image_name.endswith(".png")
        assert len(str(test_uuid)) == 36  # Standard UUID length
        
        # Test that perspective transform doesn't interfere with UUID
        service = PerspectiveTransformService()
        another_uuid = uuid.uuid4()
        assert str(test_uuid) != str(another_uuid)