"""
Unit tests for OpenCV image conversion utilities
"""

import pytest
import numpy as np
from PIL import Image
import cv2
import sys
import os

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.services.opencv_detection.utils import (
    pil_to_cv2, cv2_to_pil, bytes_to_cv2, cv2_to_bytes,
    validate_image, resize_image_if_needed, normalize_image,
    apply_clahe
)


class TestImageConversions:
    """Test cases for image format conversions."""
    
    def test_pil_to_cv2_rgb(self):
        """Test converting RGB PIL image to OpenCV."""
        # Create RGB PIL image
        pil_image = Image.new('RGB', (100, 100), color=(255, 0, 0))  # Red
        
        # Convert to OpenCV
        cv2_image = pil_to_cv2(pil_image)
        
        assert isinstance(cv2_image, np.ndarray)
        assert cv2_image.shape == (100, 100, 3)
        # Check BGR format (red in RGB becomes blue channel in BGR)
        assert cv2_image[0, 0, 0] == 0    # Blue
        assert cv2_image[0, 0, 1] == 0    # Green
        assert cv2_image[0, 0, 2] == 255  # Red
    
    def test_pil_to_cv2_rgba(self):
        """Test converting RGBA PIL image to OpenCV."""
        # Create RGBA PIL image with transparency
        pil_image = Image.new('RGBA', (50, 50), color=(255, 0, 0, 128))
        
        # Convert to OpenCV
        cv2_image = pil_to_cv2(pil_image)
        
        assert cv2_image.shape == (50, 50, 3)
        # Should have converted to RGB with white background
    
    def test_pil_to_cv2_grayscale(self):
        """Test converting grayscale PIL image to OpenCV."""
        # Create grayscale PIL image
        pil_image = Image.new('L', (75, 75), color=128)
        
        # Convert to OpenCV
        cv2_image = pil_to_cv2(pil_image)
        
        assert cv2_image.shape == (75, 75, 3)
        # Should be converted to RGB/BGR
        assert np.all(cv2_image[:, :, 0] == 128)
        assert np.all(cv2_image[:, :, 1] == 128)
        assert np.all(cv2_image[:, :, 2] == 128)
    
    def test_cv2_to_pil_color(self):
        """Test converting color OpenCV image to PIL."""
        # Create BGR OpenCV image
        cv2_image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2_image[:, :] = [255, 0, 0]  # Blue in BGR
        
        # Convert to PIL
        pil_image = cv2_to_pil(cv2_image)
        
        assert isinstance(pil_image, Image.Image)
        assert pil_image.size == (100, 100)
        assert pil_image.mode == 'RGB'
        # Check RGB format (blue in BGR becomes red channel in RGB)
        pixels = pil_image.load()
        assert pixels[0, 0] == (0, 0, 255)  # Blue
    
    def test_cv2_to_pil_grayscale(self):
        """Test converting grayscale OpenCV image to PIL."""
        # Create grayscale OpenCV image
        cv2_image = np.full((50, 50), 128, dtype=np.uint8)
        
        # Convert to PIL
        pil_image = cv2_to_pil(cv2_image)
        
        assert isinstance(pil_image, Image.Image)
        assert pil_image.size == (50, 50)
        assert pil_image.mode == 'L'
        pixels = pil_image.load()
        assert pixels[0, 0] == 128
    
    def test_round_trip_conversion(self):
        """Test converting PIL to OpenCV and back."""
        # Create test image with specific pattern
        original = Image.new('RGB', (100, 100))
        pixels = original.load()
        for i in range(100):
            for j in range(100):
                pixels[i, j] = (i % 256, j % 256, (i + j) % 256)
        
        # Convert PIL -> OpenCV -> PIL
        cv2_image = pil_to_cv2(original)
        recovered = cv2_to_pil(cv2_image)
        
        # Compare pixels
        original_pixels = original.load()
        recovered_pixels = recovered.load()
        for i in range(100):
            for j in range(100):
                assert original_pixels[i, j] == recovered_pixels[i, j]
    
    def test_bytes_to_cv2(self):
        """Test converting image bytes to OpenCV."""
        # Create a simple image and encode it
        test_image = np.zeros((50, 50, 3), dtype=np.uint8)
        test_image[:25, :25] = [255, 0, 0]  # Blue quadrant
        
        # Encode to PNG bytes
        success, encoded = cv2.imencode('.png', test_image)
        assert success
        image_bytes = encoded.tobytes()
        
        # Convert back
        decoded_image = bytes_to_cv2(image_bytes)
        
        assert decoded_image.shape == test_image.shape
        # Check that blue quadrant is preserved (all pixels should be blue)
        assert np.all(decoded_image[:25, :25, 0] == 255)  # Blue channel
        assert np.all(decoded_image[:25, :25, 1] == 0)    # Green channel
        assert np.all(decoded_image[:25, :25, 2] == 0)    # Red channel
    
    def test_cv2_to_bytes(self):
        """Test converting OpenCV image to bytes."""
        # Create test image
        test_image = np.zeros((30, 30, 3), dtype=np.uint8)
        test_image[:, :] = [0, 255, 0]  # Green
        
        # Convert to PNG bytes
        image_bytes = cv2_to_bytes(test_image, '.png')
        
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0
        
        # Verify by decoding
        decoded = bytes_to_cv2(image_bytes)
        assert np.array_equal(decoded, test_image)
    
    def test_invalid_conversions(self):
        """Test error handling for invalid conversions."""
        # Invalid image shape for cv2_to_pil
        invalid_cv2 = np.zeros((10, 10, 10, 10))  # 4D array
        with pytest.raises(ValueError):
            cv2_to_pil(invalid_cv2)
        
        # Invalid bytes
        with pytest.raises(ValueError):
            bytes_to_cv2(b"not an image")


class TestImageValidation:
    """Test cases for image validation."""
    
    def test_validate_pil_image(self):
        """Test validating PIL images."""
        # Valid image
        valid_image = Image.new('RGB', (100, 100))
        assert validate_image(valid_image) is True
        
        # Too small
        small_image = Image.new('RGB', (10, 10))
        assert validate_image(small_image) is False
        
        # Too large
        large_image = Image.new('RGB', (5000, 5000))
        assert validate_image(large_image) is False
    
    def test_validate_cv2_image(self):
        """Test validating OpenCV images."""
        # Valid image
        valid_image = np.zeros((100, 100, 3), dtype=np.uint8)
        assert validate_image(valid_image) is True
        
        # Too small
        small_image = np.zeros((10, 10, 3), dtype=np.uint8)
        assert validate_image(small_image) is False
        
        # Custom limits
        assert validate_image(small_image, min_dimension=5) is True
    
    def test_validate_invalid_type(self):
        """Test validating invalid image types."""
        assert validate_image("not an image") is False
        assert validate_image(123) is False
        assert validate_image(None) is False


class TestImageProcessing:
    """Test cases for image processing utilities."""
    
    def test_resize_image_if_needed_no_resize(self):
        """Test resize when image is already within limits."""
        image = np.zeros((1000, 1000, 3), dtype=np.uint8)
        
        resized, scale = resize_image_if_needed(image, max_dimension=2000)
        
        assert np.array_equal(resized, image)
        assert scale == 1.0
    
    def test_resize_image_if_needed_resize(self):
        """Test resize when image exceeds limits."""
        image = np.zeros((2000, 3000, 3), dtype=np.uint8)
        
        resized, scale = resize_image_if_needed(image, max_dimension=1000)
        
        # Check that aspect ratio is maintained (height:width = 2:3)
        assert resized.shape[1] == 1000  # Width should be max dimension
        assert resized.shape[0] < 1000   # Height should be proportionally smaller
        assert abs(resized.shape[0] / resized.shape[1] - 2/3) < 0.01  # Aspect ratio preserved
        assert abs(scale - 1/3) < 0.01
    
    def test_normalize_image_grayscale(self):
        """Test normalizing grayscale image."""
        # Create image with poor contrast
        image = np.full((100, 100), 128, dtype=np.uint8)
        image[:50, :50] = 100
        image[50:, 50:] = 150
        
        normalized = normalize_image(image)
        
        assert normalized.shape == image.shape
        # Check that contrast is improved (wider range of values)
        assert normalized.min() < image.min() or normalized.max() > image.max()
    
    def test_normalize_image_color(self):
        """Test normalizing color image."""
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        image[:, :] = [100, 100, 100]
        
        normalized = normalize_image(image)
        
        assert normalized.shape == image.shape
    
    def test_apply_clahe_grayscale(self):
        """Test applying CLAHE to grayscale image."""
        image = np.random.randint(0, 256, (100, 100), dtype=np.uint8)
        
        enhanced = apply_clahe(image)
        
        assert enhanced.shape == image.shape
        assert enhanced.dtype == image.dtype
    
    def test_apply_clahe_color(self):
        """Test applying CLAHE to color image."""
        image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        
        enhanced = apply_clahe(image)
        
        assert enhanced.shape == image.shape
        assert enhanced.dtype == image.dtype


if __name__ == '__main__':
    pytest.main([__file__, '-v'])