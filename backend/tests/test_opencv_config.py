"""
Unit tests for OpenCV object detection configuration
"""

import pytest
import sys
import os

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.services.opencv_detection.config import OpenCVObjectDetectionConfig


class TestOpenCVObjectDetectionConfig:
    """Test cases for OpenCV detection configuration."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = OpenCVObjectDetectionConfig()
        
        # Edge detection parameters
        assert config.canny_low_threshold == 50
        assert config.canny_high_threshold == 150
        assert config.gaussian_blur_kernel == (5, 5)
        
        # Region filtering parameters
        assert config.min_area_ratio == 0.01
        assert config.max_area_ratio == 0.8
        assert config.aspect_ratio_range == (0.3, 3.0)
        
        # General parameters
        assert config.confidence_threshold == 0.5
        assert config.max_detections == 10
        assert config.enable_fallback is True
    
    def test_config_validation_valid(self):
        """Test validation with valid configuration."""
        config = OpenCVObjectDetectionConfig()
        # Should not raise any exception
        config.validate()
    
    def test_config_validation_invalid_canny_thresholds(self):
        """Test validation with invalid Canny thresholds."""
        config = OpenCVObjectDetectionConfig(
            canny_low_threshold=150,
            canny_high_threshold=50
        )
        with pytest.raises(ValueError, match="Canny low threshold must be less than high threshold"):
            config.validate()
    
    def test_config_validation_invalid_area_ratios(self):
        """Test validation with invalid area ratios."""
        config = OpenCVObjectDetectionConfig(
            min_area_ratio=0.9,
            max_area_ratio=0.1
        )
        with pytest.raises(ValueError, match="Min area ratio must be less than max area ratio"):
            config.validate()
    
    def test_config_validation_invalid_aspect_ratios(self):
        """Test validation with invalid aspect ratios."""
        config = OpenCVObjectDetectionConfig(
            aspect_ratio_range=(3.0, 0.3)
        )
        with pytest.raises(ValueError, match="Min aspect ratio must be less than max aspect ratio"):
            config.validate()
    
    def test_config_validation_invalid_confidence_threshold(self):
        """Test validation with invalid confidence threshold."""
        config = OpenCVObjectDetectionConfig(
            confidence_threshold=1.5
        )
        with pytest.raises(ValueError, match="Confidence threshold must be between 0 and 1"):
            config.validate()
    
    def test_config_validation_invalid_max_detections(self):
        """Test validation with invalid max detections."""
        config = OpenCVObjectDetectionConfig(
            max_detections=0
        )
        with pytest.raises(ValueError, match="Max detections must be at least 1"):
            config.validate()
    
    def test_config_validation_invalid_weights(self):
        """Test validation with invalid scoring weights."""
        config = OpenCVObjectDetectionConfig(
            size_weight=0.5,
            position_weight=0.3,
            confidence_weight=0.5  # Sum > 1.0
        )
        with pytest.raises(ValueError, match="Scoring weights must sum to 1.0"):
            config.validate()
    
    def test_high_quality_preset(self):
        """Test high quality configuration preset."""
        config = OpenCVObjectDetectionConfig.for_high_quality()
        
        assert config.canny_low_threshold == 30
        assert config.canny_high_threshold == 100
        assert config.confidence_threshold == 0.7
        assert config.min_area_ratio == 0.02
        assert config.max_area_ratio == 0.7
        assert config.enable_parallel_detection is True
        
        # Should be valid
        config.validate()
    
    def test_fast_detection_preset(self):
        """Test fast detection configuration preset."""
        config = OpenCVObjectDetectionConfig.for_fast_detection()
        
        assert config.canny_low_threshold == 70
        assert config.canny_high_threshold == 170
        assert config.confidence_threshold == 0.4
        assert len(config.template_scales) == 3
        assert config.enable_parallel_detection is False
        assert config.detection_timeout == 2.0
        
        # Should be valid
        config.validate()
    
    def test_mockup_template_preset(self):
        """Test mockup template configuration preset."""
        config = OpenCVObjectDetectionConfig.for_mockup_templates()
        
        assert config.canny_low_threshold == 40
        assert config.canny_high_threshold == 120
        assert config.min_area_ratio == 0.05
        assert config.max_area_ratio == 0.6
        assert config.aspect_ratio_range == (0.5, 2.0)
        assert config.confidence_threshold == 0.6
        assert len(config.template_scales) == 5
        
        # Check mockup-specific weights
        assert config.size_weight == 0.4
        assert config.position_weight == 0.3
        assert config.confidence_weight == 0.3
        
        # Should be valid
        config.validate()
    
    def test_custom_configuration(self):
        """Test creating custom configuration."""
        config = OpenCVObjectDetectionConfig(
            canny_low_threshold=25,
            canny_high_threshold=75,
            min_area_ratio=0.1,
            max_area_ratio=0.5,
            confidence_threshold=0.8,
            max_detections=5,
            enable_fallback=False
        )
        
        assert config.canny_low_threshold == 25
        assert config.canny_high_threshold == 75
        assert config.min_area_ratio == 0.1
        assert config.max_area_ratio == 0.5
        assert config.confidence_threshold == 0.8
        assert config.max_detections == 5
        assert config.enable_fallback is False
        
        # Should be valid
        config.validate()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])