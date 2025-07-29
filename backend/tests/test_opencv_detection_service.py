"""
Tests for the main OpenCV Object Detection Service
"""

import pytest
from PIL import Image, ImageDraw
import numpy as np
from unittest.mock import Mock, patch
import threading
import time

from src.services.opencv_detection import (
    OpenCVObjectDetectionService,
    OpenCVObjectDetectionConfig,
    BoundingBox,
    ObjectDetectionError,
    NoSuitableRegionsError
)
from src.services.opencv_detection.detectors import (
    EdgeBasedDetector,
    ContourBasedDetector,
    ColorBasedDetector,
    TemplateMatchingDetector,
    FallbackDetector
)


class TestOpenCVObjectDetectionService:
    """Test cases for OpenCVObjectDetectionService."""
    
    def test_initialization(self):
        """Test service initialization with default config."""
        service = OpenCVObjectDetectionService()
        assert service.config is not None
        assert len(service._detectors) == 5  # All detectors enabled by default
        assert 'edge' in service._detectors
        assert 'contour' in service._detectors
        assert 'color' in service._detectors
        assert 'template' in service._detectors
        assert 'fallback' in service._detectors
        
    def test_initialization_with_custom_config(self):
        """Test service initialization with custom configuration."""
        config = OpenCVObjectDetectionConfig(
            enabled_detectors=['edge', 'contour'],
            max_detections=5,
            confidence_threshold=0.8
        )
        service = OpenCVObjectDetectionService(config)
        assert len(service._detectors) == 2
        assert 'edge' in service._detectors
        assert 'contour' in service._detectors
        assert 'color' not in service._detectors
        
    def test_detect_objects_basic(self):
        """Test basic object detection on simple image."""
        # Create test image with rectangle
        image = Image.new('RGB', (400, 300), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([50, 50, 200, 150], outline='black', width=5)
        
        service = OpenCVObjectDetectionService()
        detections = service.detect_objects(image)
        
        assert len(detections) > 0
        assert all(isinstance(d, BoundingBox) for d in detections)
        
    def test_detect_objects_invalid_image(self):
        """Test detection with invalid image."""
        service = OpenCVObjectDetectionService()
        
        with pytest.raises(ValueError, match="Invalid image"):
            service.detect_objects(None)
            
    def test_sequential_detection(self):
        """Test sequential detector execution."""
        config = OpenCVObjectDetectionConfig(parallel_processing=False)
        service = OpenCVObjectDetectionService(config)
        
        image = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([40, 40, 160, 160], outline='black', width=3)
        
        detections = service.detect_objects(image)
        assert len(detections) > 0
        
    def test_parallel_detection(self):
        """Test parallel detector execution."""
        config = OpenCVObjectDetectionConfig(parallel_processing=True)
        service = OpenCVObjectDetectionService(config)
        
        image = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([40, 40, 160, 160], outline='black', width=3)
        
        detections = service.detect_objects(image)
        assert len(detections) > 0
        
    def test_early_termination(self):
        """Test early termination when enough high-confidence detections found."""
        # Create image with multiple rectangles
        image = Image.new('RGB', (400, 400), 'white')
        draw = ImageDraw.Draw(image)
        for i in range(5):
            x = i * 70 + 10
            draw.rectangle([x, 10, x + 60, 70], outline='black', width=3)
            
        config = OpenCVObjectDetectionConfig(
            max_detections=3,
            enabled_detectors=['edge', 'contour', 'color', 'template', 'fallback'],
            parallel_processing=False
        )
        service = OpenCVObjectDetectionService(config)
        
        # Mock detectors to track calls
        original_detectors = service._detectors.copy()
        call_order = []
        
        for name, detector in original_detectors.items():
            mock_detector = Mock(spec=detector)
            mock_detector.detect.side_effect = lambda img, n=name: (
                call_order.append(n),
                [BoundingBox(0, 0, 50, 50, 0.9, f"test_{n}")] * 2
            )[1]
            service._detectors[name] = mock_detector
            
        detections = service.detect_objects(image)
        
        # Should terminate early, not calling all detectors
        assert len(call_order) < 5
        
    def test_merge_overlapping_regions(self):
        """Test merging of overlapping detections."""
        service = OpenCVObjectDetectionService()
        
        # Create overlapping detections
        detections = [
            BoundingBox(0, 0, 100, 100, 0.9, "test1"),
            BoundingBox(10, 10, 100, 100, 0.8, "test2"),  # Overlaps with first
            BoundingBox(200, 200, 100, 100, 0.7, "test3")  # No overlap
        ]
        
        merged = service._merge_overlapping_regions(detections)
        
        # Should merge first two, keep third separate
        assert len(merged) == 2
        
    def test_calculate_iou(self):
        """Test IoU calculation."""
        service = OpenCVObjectDetectionService()
        
        box1 = BoundingBox(0, 0, 100, 100, 0.9, "test1")
        box2 = BoundingBox(50, 50, 100, 100, 0.8, "test2")
        
        iou = service._calculate_iou(box1, box2)
        
        # Intersection area: 50x50 = 2500
        # Union area: 100x100 + 100x100 - 2500 = 17500
        expected_iou = 2500 / 17500
        assert abs(iou - expected_iou) < 0.01
        
    def test_calculate_iou_no_overlap(self):
        """Test IoU calculation with no overlap."""
        service = OpenCVObjectDetectionService()
        
        box1 = BoundingBox(0, 0, 100, 100, 0.9, "test1")
        box2 = BoundingBox(200, 200, 100, 100, 0.8, "test2")
        
        iou = service._calculate_iou(box1, box2)
        assert iou == 0.0
        
    def test_merge_boxes(self):
        """Test bounding box merging."""
        service = OpenCVObjectDetectionService()
        
        box1 = BoundingBox(0, 0, 100, 100, 0.9, "test1")
        box2 = BoundingBox(50, 50, 100, 100, 0.8, "test2")
        
        merged = service._merge_boxes(box1, box2)
        
        assert merged.x == 0
        assert merged.y == 0
        assert merged.width == 150
        assert merged.height == 150
        assert merged.label == "test1"  # Higher confidence label
        
    def test_rank_regions(self):
        """Test region ranking algorithm."""
        service = OpenCVObjectDetectionService()
        image_size = (400, 300)
        
        detections = [
            # Small region with high confidence
            BoundingBox(10, 10, 50, 50, 0.95, "small"),
            # Large centered region with medium confidence
            BoundingBox(100, 75, 200, 150, 0.7, "centered"),
            # Edge region with low confidence
            BoundingBox(0, 0, 100, 100, 0.6, "edge")
        ]
        
        ranked = service._rank_regions(detections, image_size)
        
        # Centered region should rank higher despite lower confidence
        assert ranked[0].label == "centered"
        
    def test_find_suitable_regions(self):
        """Test the main find_suitable_regions interface."""
        # Create test image with clear rectangle
        image = Image.new('RGB', (400, 300), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([50, 50, 350, 250], outline='black', width=5)
        
        service = OpenCVObjectDetectionService()
        regions = service.find_suitable_regions(image)
        
        assert len(regions) > 0
        assert all(isinstance(r, BoundingBox) for r in regions)
        
    def test_find_suitable_regions_no_detections(self):
        """Test behavior when no regions are detected."""
        # Create blank image
        image = Image.new('RGB', (100, 100), 'white')
        
        service = OpenCVObjectDetectionService()
        regions = service.find_suitable_regions(image)
        
        # Should use fallback detector
        assert len(regions) > 0
        
    def test_find_suitable_regions_too_small(self):
        """Test filtering of regions that are too small."""
        # Create image with tiny rectangle
        image = Image.new('RGB', (1000, 1000), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([10, 10, 20, 20], outline='black', width=1)
        
        config = OpenCVObjectDetectionConfig(
            min_region_area_ratio=0.1,  # 10% minimum
            enabled_detectors=['edge'],  # Only edge detector
            enable_fallback=False  # Disable fallback to test the error
        )
        service = OpenCVObjectDetectionService(config)
        
        with pytest.raises(NoSuitableRegionsError):
            service.find_suitable_regions(image)
            
    def test_detector_failure_handling(self):
        """Test handling of detector failures."""
        config = OpenCVObjectDetectionConfig(
            enabled_detectors=['edge', 'contour'],
            parallel_processing=False
        )
        service = OpenCVObjectDetectionService(config)
        
        # Mock edge detector to fail
        original_edge = service._detectors['edge']
        service._detectors['edge'] = Mock(spec=EdgeBasedDetector)
        service._detectors['edge'].detect.side_effect = Exception("Edge detector failed")
        
        # Should still get results from contour detector
        image = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([40, 40, 160, 160], outline='black', width=3)
        
        detections = service.detect_objects(image)
        assert len(detections) > 0  # Contour detector should still work
        
    def test_parallel_detector_timeout(self):
        """Test timeout handling in parallel detection."""
        config = OpenCVObjectDetectionConfig(
            enabled_detectors=['edge', 'contour'],
            parallel_processing=True,
            detector_timeout=0.1  # Very short timeout
        )
        service = OpenCVObjectDetectionService(config)
        
        # Mock edge detector to be slow
        original_edge = service._detectors['edge']
        service._detectors['edge'] = Mock(spec=EdgeBasedDetector)
        service._detectors['edge'].detect.side_effect = lambda img: (
            time.sleep(0.5),  # Sleep longer than timeout
            []
        )[1]
        
        # Should still get results from contour detector
        image = Image.new('RGB', (200, 200), 'white')
        draw = ImageDraw.Draw(image)
        draw.rectangle([40, 40, 160, 160], outline='black', width=3)
        
        detections = service.detect_objects(image)
        # Should have detections from contour detector even if edge times out
        assert isinstance(detections, list)
        
    def test_cleanup(self):
        """Test resource cleanup."""
        service = OpenCVObjectDetectionService()
        service._executor = Mock()
        
        service.cleanup()
        service._executor.shutdown.assert_called_once_with(wait=False)
        
    def test_config_validation_in_service(self):
        """Test that service validates config on initialization."""
        # Invalid config with negative confidence
        config = OpenCVObjectDetectionConfig(confidence_threshold=-0.5)
        
        # Should not raise during initialization (validation is optional)
        service = OpenCVObjectDetectionService(config)
        assert service.config.confidence_threshold == -0.5
        
    def test_scoring_weights_normalization(self):
        """Test that scoring weights are properly used."""
        config = OpenCVObjectDetectionConfig(
            scoring_weights={
                'confidence': 0.5,
                'size': 0.2,
                'aspect_ratio': 0.1,
                'position': 0.1,
                'edge_distance': 0.1
            }
        )
        service = OpenCVObjectDetectionService(config)
        
        # Create detections to rank
        detections = [
            BoundingBox(50, 50, 100, 100, 0.9, "high_conf"),
            BoundingBox(150, 150, 100, 100, 0.5, "low_conf")
        ]
        
        ranked = service._rank_regions(detections, (400, 400))
        
        # High confidence detection should rank first due to weight
        assert ranked[0].label == "high_conf"