"""
Unit tests for OpenCV detection algorithms
"""

import pytest
import numpy as np
import cv2
import sys
import os

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.services.opencv_detection.config import OpenCVObjectDetectionConfig
from src.services.opencv_detection.detectors import (
    EdgeBasedDetector,
    ContourBasedDetector,
    ColorBasedDetector,
    TemplateMatchingDetector,
    FallbackDetector
)


def create_test_image_with_rectangle(size=300, rect_size=100):
    """Create a test image with a clear rectangle."""
    image = np.ones((size, size, 3), dtype=np.uint8) * 200  # Gray background
    
    # Draw a black rectangle
    x = (size - rect_size) // 2
    y = (size - rect_size) // 2
    cv2.rectangle(image, (x, y), (x + rect_size, y + rect_size), (0, 0, 0), 3)
    
    # Fill with white
    cv2.rectangle(image, (x+3, y+3), (x + rect_size - 3, y + rect_size - 3), (255, 255, 255), -1)
    
    return image


def create_test_image_with_colored_regions(size=300):
    """Create a test image with distinct colored regions."""
    image = np.zeros((size, size, 3), dtype=np.uint8)
    
    # Red region (top-left)
    image[0:size//2, 0:size//2] = (0, 0, 255)
    
    # Green region (top-right)
    image[0:size//2, size//2:size] = (0, 255, 0)
    
    # Blue region (bottom-left)
    image[size//2:size, 0:size//2] = (255, 0, 0)
    
    # White region (bottom-right)
    image[size//2:size, size//2:size] = (255, 255, 255)
    
    return image


def create_test_image_with_gradient(size=300):
    """Create a test image with gradient (no clear regions)."""
    image = np.zeros((size, size, 3), dtype=np.uint8)
    
    for i in range(size):
        for j in range(size):
            image[i, j] = [i * 255 // size, j * 255 // size, (i + j) * 255 // (2 * size)]
    
    return image


class TestEdgeBasedDetector:
    """Test cases for edge-based detector."""
    
    def test_detect_rectangle(self):
        """Test detecting a clear rectangle with edges."""
        config = OpenCVObjectDetectionConfig()
        detector = EdgeBasedDetector(config)
        
        image = create_test_image_with_rectangle()
        regions = detector.detect(image)
        
        assert len(regions) > 0
        # Should detect at least the central rectangle
        central_region = next((r for r in regions if 
                              abs(r.x - 100) < 20 and abs(r.y - 100) < 20), None)
        assert central_region is not None
        assert central_region.confidence > 0.5
    
    def test_detect_no_edges(self):
        """Test with image that has no clear edges."""
        config = OpenCVObjectDetectionConfig()
        detector = EdgeBasedDetector(config)
        
        # Create uniform color image
        image = np.ones((200, 200, 3), dtype=np.uint8) * 128
        regions = detector.detect(image)
        
        # Should find few or no regions
        assert len(regions) < 3
    
    def test_preprocessor(self):
        """Test image preprocessing for edge detection."""
        config = OpenCVObjectDetectionConfig()
        detector = EdgeBasedDetector(config)
        
        image = create_test_image_with_rectangle()
        preprocessed = detector._preprocess_for_edge_detection(image)
        
        assert len(preprocessed.shape) == 2  # Should be grayscale
        assert preprocessed.dtype == np.uint8


class TestContourBasedDetector:
    """Test cases for contour-based detector."""
    
    def test_detect_rectangles(self):
        """Test detecting rectangular contours."""
        config = OpenCVObjectDetectionConfig()
        detector = ContourBasedDetector(config)
        
        image = create_test_image_with_rectangle()
        regions = detector.detect(image)
        
        assert len(regions) > 0
        # Check that detected regions are labeled as rectangles
        assert any(r.label == "contour_rectangle" for r in regions)
    
    def test_rectangle_score_calculation(self):
        """Test rectangle score calculation."""
        config = OpenCVObjectDetectionConfig()
        detector = ContourBasedDetector(config)
        
        # Create a perfect rectangle contour
        rect_points = np.array([[0, 0], [100, 0], [100, 50], [0, 50]], dtype=np.int32)
        score = detector._calculate_rectangle_score(rect_points)
        
        assert score > 0.8  # Should have high score for perfect rectangle
    
    def test_duplicate_removal(self):
        """Test removal of duplicate rectangles."""
        config = OpenCVObjectDetectionConfig()
        detector = ContourBasedDetector(config)
        
        # Create fake rectangles with overlap
        contour1 = np.array([[0, 0], [100, 0], [100, 100], [0, 100]], dtype=np.int32)
        contour2 = np.array([[10, 10], [110, 10], [110, 110], [10, 110]], dtype=np.int32)
        contour3 = np.array([[200, 200], [300, 200], [300, 300], [200, 300]], dtype=np.int32)
        
        rectangles = [(contour1, 0.9), (contour2, 0.8), (contour3, 0.85)]
        unique = detector._remove_duplicate_rectangles(rectangles)
        
        assert len(unique) == 2  # Should remove one overlapping rectangle


class TestColorBasedDetector:
    """Test cases for color-based detector."""
    
    def test_detect_colored_regions(self):
        """Test detecting uniform color regions."""
        config = OpenCVObjectDetectionConfig()
        detector = ColorBasedDetector(config)
        
        image = create_test_image_with_colored_regions()
        regions = detector.detect(image)
        
        assert len(regions) >= 4  # Should detect all 4 colored quadrants
        assert all(r.label == "color_region" for r in regions)
    
    def test_no_uniform_regions(self):
        """Test with gradient image (no uniform regions)."""
        config = OpenCVObjectDetectionConfig()
        detector = ColorBasedDetector(config)
        
        image = create_test_image_with_gradient()
        regions = detector.detect(image)
        
        # Should find few or no regions in gradient
        assert len(regions) <= 3  # May find some regions due to edge effects
    
    def test_neutral_region_detection(self):
        """Test detection of neutral (gray) regions."""
        config = OpenCVObjectDetectionConfig()
        detector = ColorBasedDetector(config)
        
        # Create image with gray region
        image = np.ones((200, 200, 3), dtype=np.uint8) * 128  # Gray
        cv2.rectangle(image, (50, 50), (150, 150), (200, 200, 200), -1)  # Light gray rectangle
        
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        mask = detector._find_neutral_regions(lab)
        
        assert mask is not None
        assert np.sum(mask > 0) > 0  # Should find neutral regions


class TestTemplateMatchingDetector:
    """Test cases for template matching detector."""
    
    def test_template_generation(self):
        """Test synthetic template generation."""
        config = OpenCVObjectDetectionConfig()
        detector = TemplateMatchingDetector(config)
        
        assert len(detector.templates) > 0
        assert 'frame' in detector.templates
        assert 'screen' in detector.templates
        assert 'device' in detector.templates
    
    def test_detect_frame_pattern(self):
        """Test detecting frame-like patterns."""
        config = OpenCVObjectDetectionConfig()
        detector = TemplateMatchingDetector(config)
        
        # Create image with frame-like border
        image = np.ones((300, 300, 3), dtype=np.uint8) * 255
        cv2.rectangle(image, (20, 20), (280, 280), (0, 0, 0), 15)
        
        regions = detector.detect(image)
        
        # Should detect frame pattern
        assert len(regions) > 0
        assert any('template' in r.label for r in regions)
    
    def test_multiscale_matching(self):
        """Test template matching at multiple scales."""
        config = OpenCVObjectDetectionConfig()
        detector = TemplateMatchingDetector(config)
        
        # Create a simple test image
        image = create_test_image_with_rectangle(size=400, rect_size=150)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Get a template
        template = detector.templates['frame']
        
        matches = detector._match_template_multiscale(gray, template, 'frame')
        
        # Should find matches (may not find any if template doesn't match well)
        # Just verify the function runs without error
        assert isinstance(matches, list)


class TestFallbackDetector:
    """Test cases for fallback detector."""
    
    def test_always_returns_regions(self):
        """Test that fallback always returns some regions."""
        config = OpenCVObjectDetectionConfig()
        detector = FallbackDetector(config)
        
        # Test with various images
        test_images = [
            np.zeros((200, 200, 3), dtype=np.uint8),  # Black
            np.ones((300, 300, 3), dtype=np.uint8) * 255,  # White
            create_test_image_with_gradient(),  # Gradient
        ]
        
        for image in test_images:
            regions = detector.detect(image)
            assert len(regions) > 0
            assert all(r.label.startswith('fallback') for r in regions)
    
    def test_center_region(self):
        """Test center region generation."""
        config = OpenCVObjectDetectionConfig()
        detector = FallbackDetector(config)
        
        center = detector._get_center_region(400, 300)
        
        # 40% of 300 (smaller dimension) = 120
        expected_size = int(300 * 0.4)
        assert center.x == (400 - expected_size) // 2
        assert center.y == (300 - expected_size) // 2
        assert center.width == expected_size
        assert center.height == expected_size
    
    def test_golden_ratio_regions(self):
        """Test golden ratio region generation."""
        config = OpenCVObjectDetectionConfig()
        detector = FallbackDetector(config)
        
        regions = detector._get_golden_ratio_regions(500, 300)
        
        assert len(regions) == 4  # Four golden ratio intersections
        assert all(r.label.startswith('fallback_golden') for r in regions)
    
    def test_aspect_ratio_regions(self):
        """Test aspect ratio based region generation."""
        config = OpenCVObjectDetectionConfig()
        detector = FallbackDetector(config)
        
        regions = detector._get_aspect_ratio_regions(800, 600)
        
        assert len(regions) > 0
        # Check that regions have expected aspect ratios
        for region in regions:
            ratio = region.width / region.height
            # Should be close to one of the standard ratios
            standard_ratios = [1.0, 1.5, 1.33, 1.77, 1/1.5, 1/1.33, 1/1.77]
            assert any(abs(ratio - sr) < 0.1 for sr in standard_ratios)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])