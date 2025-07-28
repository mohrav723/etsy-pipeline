"""
Unit tests for OpenCV object detection base classes
"""

import pytest
import numpy as np
import sys
import os

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.services.opencv_detection.base import BoundingBox, BaseDetector
from src.services.opencv_detection.config import OpenCVObjectDetectionConfig


class TestBoundingBox:
    """Test cases for BoundingBox class."""
    
    def test_bounding_box_creation(self):
        """Test creating a bounding box."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50, 
                          confidence=0.85, label="test_region")
        
        assert bbox.x == 10
        assert bbox.y == 20
        assert bbox.width == 100
        assert bbox.height == 50
        assert bbox.confidence == 0.85
        assert bbox.label == "test_region"
    
    def test_bounding_box_to_dict(self):
        """Test converting bounding box to dictionary."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50, 
                          confidence=0.85, label="test_region")
        
        bbox_dict = bbox.to_dict()
        
        assert isinstance(bbox_dict, dict)
        assert bbox_dict['x'] == 10
        assert bbox_dict['y'] == 20
        assert bbox_dict['width'] == 100
        assert bbox_dict['height'] == 50
        assert bbox_dict['confidence'] == 0.85
        assert bbox_dict['label'] == "test_region"
    
    def test_get_corners(self):
        """Test getting corners of bounding box."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50, 
                          confidence=0.85, label="test")
        
        corners = bbox.get_corners()
        
        assert len(corners) == 4
        assert corners[0] == (10, 20)      # Top-left
        assert corners[1] == (110, 20)     # Top-right
        assert corners[2] == (110, 70)     # Bottom-right
        assert corners[3] == (10, 70)      # Bottom-left
    
    def test_get_center(self):
        """Test getting center of bounding box."""
        bbox = BoundingBox(x=10, y=20, width=100, height=50, 
                          confidence=0.85, label="test")
        
        center = bbox.get_center()
        
        assert center == (60, 45)  # (10 + 100/2, 20 + 50/2)
    
    def test_get_area(self):
        """Test calculating area of bounding box."""
        bbox = BoundingBox(x=0, y=0, width=100, height=50, 
                          confidence=0.85, label="test")
        
        area = bbox.get_area()
        
        assert area == 5000  # 100 * 50
    
    def test_get_aspect_ratio(self):
        """Test calculating aspect ratio."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=50, 
                           confidence=0.85, label="test")
        bbox2 = BoundingBox(x=0, y=0, width=50, height=100, 
                           confidence=0.85, label="test")
        bbox3 = BoundingBox(x=0, y=0, width=100, height=0, 
                           confidence=0.85, label="test")
        
        assert bbox1.get_aspect_ratio() == 2.0
        assert bbox2.get_aspect_ratio() == 0.5
        assert bbox3.get_aspect_ratio() == 0  # Division by zero handled
    
    def test_overlaps_with(self):
        """Test checking if bounding boxes overlap."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100, 
                           confidence=0.85, label="test1")
        bbox2 = BoundingBox(x=50, y=50, width=100, height=100, 
                           confidence=0.85, label="test2")
        bbox3 = BoundingBox(x=200, y=200, width=100, height=100, 
                           confidence=0.85, label="test3")
        
        assert bbox1.overlaps_with(bbox2) is True
        assert bbox1.overlaps_with(bbox3) is False
        assert bbox2.overlaps_with(bbox3) is False
    
    def test_intersection_over_union(self):
        """Test calculating IoU between bounding boxes."""
        bbox1 = BoundingBox(x=0, y=0, width=100, height=100, 
                           confidence=0.85, label="test1")
        bbox2 = BoundingBox(x=50, y=50, width=100, height=100, 
                           confidence=0.85, label="test2")
        bbox3 = BoundingBox(x=200, y=200, width=100, height=100, 
                           confidence=0.85, label="test3")
        
        # Partial overlap
        iou12 = bbox1.intersection_over_union(bbox2)
        assert 0 < iou12 < 1
        # Calculate expected IoU: intersection = 50x50 = 2500, union = 20000 - 2500 = 17500
        expected_iou = 2500 / 17500
        assert abs(iou12 - expected_iou) < 0.001
        
        # No overlap
        iou13 = bbox1.intersection_over_union(bbox3)
        assert iou13 == 0
        
        # Same box (100% overlap)
        iou11 = bbox1.intersection_over_union(bbox1)
        assert iou11 == 1.0


class MockDetector(BaseDetector):
    """Mock detector for testing base class functionality."""
    
    def detect(self, image: np.ndarray) -> list:
        """Simple mock detection that returns fixed regions."""
        height, width = image.shape[:2]
        return [
            BoundingBox(x=10, y=10, width=50, height=50, 
                       confidence=0.9, label="mock1"),
            BoundingBox(x=100, y=100, width=20, height=20, 
                       confidence=0.8, label="mock2"),
            BoundingBox(x=width-60, y=height-60, width=50, height=50, 
                       confidence=0.7, label="mock3"),
        ]


class TestBaseDetector:
    """Test cases for BaseDetector abstract class."""
    
    def test_base_detector_initialization(self):
        """Test initializing base detector."""
        config = OpenCVObjectDetectionConfig()
        detector = MockDetector(config)
        
        assert detector.config == config
        assert detector.name == "MockDetector"
    
    def test_filter_regions_size_constraints(self):
        """Test filtering regions by size constraints."""
        config = OpenCVObjectDetectionConfig(
            min_area_ratio=0.05,  # 5% of image
            max_area_ratio=0.5    # 50% of image
        )
        detector = MockDetector(config)
        
        # Create test image 200x200
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        image_area = 200 * 200  # 40000
        
        regions = [
            # Too small (1% of image)
            BoundingBox(x=0, y=0, width=20, height=20, 
                       confidence=0.9, label="small"),
            # Good size (10% of image)
            BoundingBox(x=0, y=0, width=63, height=63, 
                       confidence=0.9, label="medium"),
            # Too large (64% of image)
            BoundingBox(x=0, y=0, width=160, height=160, 
                       confidence=0.9, label="large"),
        ]
        
        filtered = detector.filter_regions(regions, image.shape)
        
        assert len(filtered) == 1
        assert filtered[0].label == "medium"
    
    def test_filter_regions_aspect_ratio(self):
        """Test filtering regions by aspect ratio."""
        config = OpenCVObjectDetectionConfig(
            aspect_ratio_range=(0.5, 2.0)
        )
        detector = MockDetector(config)
        
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        regions = [
            # Too wide (aspect ratio 4.0)
            BoundingBox(x=0, y=0, width=100, height=25, 
                       confidence=0.9, label="wide"),
            # Good aspect ratio (1.5)
            BoundingBox(x=0, y=0, width=60, height=40, 
                       confidence=0.9, label="good"),
            # Too tall (aspect ratio 0.25)
            BoundingBox(x=0, y=0, width=25, height=100, 
                       confidence=0.9, label="tall"),
        ]
        
        filtered = detector.filter_regions(regions, image.shape)
        
        assert len(filtered) == 1
        assert filtered[0].label == "good"
    
    def test_filter_regions_confidence(self):
        """Test filtering regions by confidence threshold."""
        config = OpenCVObjectDetectionConfig(
            confidence_threshold=0.7
        )
        detector = MockDetector(config)
        
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        regions = [
            BoundingBox(x=0, y=0, width=50, height=50, 
                       confidence=0.9, label="high_conf"),
            BoundingBox(x=0, y=0, width=50, height=50, 
                       confidence=0.5, label="low_conf"),
            BoundingBox(x=0, y=0, width=50, height=50, 
                       confidence=0.7, label="threshold_conf"),
        ]
        
        filtered = detector.filter_regions(regions, image.shape)
        
        assert len(filtered) == 2
        assert all(r.confidence >= 0.7 for r in filtered)
    
    def test_filter_regions_out_of_bounds(self):
        """Test filtering regions that are out of image bounds."""
        config = OpenCVObjectDetectionConfig()
        detector = MockDetector(config)
        
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        regions = [
            # Negative coordinates
            BoundingBox(x=-10, y=10, width=50, height=50, 
                       confidence=0.9, label="negative"),
            # Extends beyond image
            BoundingBox(x=180, y=180, width=50, height=50, 
                       confidence=0.9, label="overflow"),
            # Good region
            BoundingBox(x=50, y=50, width=50, height=50, 
                       confidence=0.9, label="good"),
        ]
        
        filtered = detector.filter_regions(regions, image.shape)
        
        assert len(filtered) == 1
        assert filtered[0].label == "good"
    
    def test_merge_overlapping_regions(self):
        """Test merging overlapping regions."""
        config = OpenCVObjectDetectionConfig()
        detector = MockDetector(config)
        
        regions = [
            BoundingBox(x=0, y=0, width=100, height=100, 
                       confidence=0.9, label="region1"),
            BoundingBox(x=50, y=50, width=100, height=100, 
                       confidence=0.8, label="region2"),
            BoundingBox(x=200, y=200, width=100, height=100, 
                       confidence=0.7, label="region3"),
        ]
        
        merged = detector.merge_overlapping_regions(regions, iou_threshold=0.1)
        
        # First two should merge, third should remain separate
        assert len(merged) == 2
        
        # Check that merged region encompasses both original regions
        merged_region = next(r for r in merged if '+' in r.label)
        assert merged_region.x == 0
        assert merged_region.y == 0
        assert merged_region.width == 150
        assert merged_region.height == 150
        assert merged_region.confidence == 0.9  # Takes highest confidence


if __name__ == '__main__':
    pytest.main([__file__, '-v'])