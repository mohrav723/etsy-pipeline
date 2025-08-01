"""
Tests for perspective transformation service with no-distortion mode
"""

import pytest
import numpy as np
from PIL import Image
from unittest.mock import Mock, patch

from src.services.perspective_transform import (
    PerspectiveTransformService, 
    PerspectiveTransformConfig,
    TransformationResult
)
from src.services.object_detection import BoundingBox


class TestNoPerspectiveMode:
    """Test suite for no-perspective transformation mode."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a test artwork image (100x100, red)
        self.artwork = Image.new('RGB', (100, 100), color='red')
        
        # Create a test region
        self.region = BoundingBox(
            x=50,
            y=50,
            width=200,
            height=150,
            confidence=0.9,
            label="frame"
        )
        
        # Mock mockup size
        self.mockup_size = (800, 600)
    
    def test_no_perspective_mode_corners(self):
        """Test that no-perspective mode returns straight corners."""
        config = PerspectiveTransformConfig(
            enable_perspective=False
        )
        service = PerspectiveTransformService(config)
        
        corners = service._calculate_perspective_corners(self.region)
        
        # Verify corners form a perfect rectangle
        assert corners[0] == (50, 50)  # top-left
        assert corners[1] == (250, 50)  # top-right
        assert corners[2] == (250, 200)  # bottom-right
        assert corners[3] == (50, 200)  # bottom-left
    
    def test_perspective_mode_corners(self):
        """Test that perspective mode adds distortion."""
        config = PerspectiveTransformConfig(
            enable_perspective=True,
            perspective_factor=0.05
        )
        service = PerspectiveTransformService(config)
        
        corners = service._calculate_perspective_corners(self.region)
        
        # Verify corners are distorted (not a perfect rectangle)
        assert corners[0] == (50, 50)  # top-left unchanged
        assert corners[1][0] < 250  # top-right x is shifted left
        assert corners[1][1] > 50   # top-right y is shifted down
        assert corners[2] == (250, 200)  # bottom-right unchanged
        assert corners[3][0] > 50   # bottom-left x is shifted right
    
    def test_contain_mode_preserves_aspect_ratio(self):
        """Test that contain mode preserves artwork aspect ratio."""
        config = PerspectiveTransformConfig(
            enable_perspective=False,
            fit_mode="contain",
            padding_ratio=0.0
        )
        service = PerspectiveTransformService(config)
        
        # Create a square artwork (100x100)
        square_artwork = Image.new('RGB', (100, 100), color='blue')
        
        # Transform to a wider region (200x100)
        wide_region = BoundingBox(0, 0, 200, 100, 0.9, "frame")
        
        result = service.transform_artwork_to_region(
            square_artwork, wide_region, self.mockup_size
        )
        
        # Verify the output maintains aspect ratio
        # The artwork should be 100x100 centered in 200x100
        assert result.transformed_image.size == (200, 100)
        assert result.target_size == (200, 100)
    
    def test_fill_mode_crops_artwork(self):
        """Test that fill mode crops artwork to fill region."""
        config = PerspectiveTransformConfig(
            enable_perspective=False,
            fit_mode="fill",
            padding_ratio=0.0
        )
        service = PerspectiveTransformService(config)
        
        # Transform to a different aspect ratio region
        result = service.transform_artwork_to_region(
            self.artwork, self.region, self.mockup_size
        )
        
        # Verify the output fills the region
        assert result.transformed_image.size == (200, 150)
    
    def test_no_padding_exact_placement(self):
        """Test that no padding results in exact placement."""
        config = PerspectiveTransformConfig(
            enable_perspective=False,
            padding_ratio=0.0
        )
        service = PerspectiveTransformService(config)
        
        # Create mockup template
        mockup = Image.new('RGB', (800, 600), color='white')
        
        # Transform artwork
        result = service.transform_artwork_to_region(
            self.artwork, self.region, self.mockup_size
        )
        
        # Composite onto mockup
        composite = service.create_composite_image(
            mockup, result.transformed_image, self.region
        )
        
        # Verify composite size matches mockup
        assert composite.size == mockup.size
    
    def test_perspective_factor_clamping(self):
        """Test that perspective factor is clamped to valid range."""
        # Test with factor > 0.1
        config1 = PerspectiveTransformConfig(perspective_factor=0.5)
        assert config1.perspective_factor == 0.1  # Clamped to max
        
        # Test with factor < 0
        config2 = PerspectiveTransformConfig(perspective_factor=-0.1)
        assert config2.perspective_factor == 0  # Clamped to min
        
        # Test with valid factor
        config3 = PerspectiveTransformConfig(perspective_factor=0.05)
        assert config3.perspective_factor == 0.05


class TestAspectRatioHandling:
    """Test aspect ratio preservation in different modes."""
    
    def test_contain_mode_letterboxing(self):
        """Test that contain mode adds letterboxing for mismatched aspects."""
        config = PerspectiveTransformConfig(
            enable_perspective=False,
            fit_mode="contain",
            padding_ratio=0.0
        )
        service = PerspectiveTransformService(config)
        
        # Create a wide artwork (200x100)
        wide_artwork = Image.new('RGB', (200, 100), color='green')
        
        # Transform to a square region (150x150)
        square_region = BoundingBox(0, 0, 150, 150, 0.9, "frame")
        
        result = service.transform_artwork_to_region(
            wide_artwork, square_region, (800, 600)
        )
        
        # Verify letterboxing (artwork scaled to 150x75, centered)
        assert result.transformed_image.size == (150, 150)
        
        # Check that the image has letterboxing (white bars)
        # by examining the corners which should be white
        np_image = np.array(result.transformed_image)
        assert np.array_equal(np_image[0, 0], [255, 255, 255])  # Top-left is white
        assert np.array_equal(np_image[149, 0], [255, 255, 255])  # Bottom-left is white