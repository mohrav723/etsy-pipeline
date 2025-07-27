"""
Perspective Transformation Service for Intelligent Mockup Generation

This module provides OpenCV-based perspective transformation functionality to warp 
artwork to fit detected regions naturally in mockup templates.
"""

import logging
from typing import List, Tuple, Optional, Union
import cv2
import numpy as np
from PIL import Image
import math

from .object_detection import BoundingBox

logger = logging.getLogger(__name__)

class PerspectiveTransformConfig:
    """Configuration class for perspective transformation parameters."""
    
    def __init__(
        self,
        interpolation_method: int = cv2.INTER_LANCZOS4,
        border_mode: int = cv2.BORDER_REFLECT,
        quality_factor: float = 1.0,
        padding_ratio: float = 0.05,
        min_region_size: int = 50,
        max_aspect_ratio_diff: float = 3.0
    ):
        self.interpolation_method = interpolation_method
        self.border_mode = border_mode
        self.quality_factor = quality_factor  # Scale factor for quality preservation
        self.padding_ratio = padding_ratio    # Padding around detected region
        self.min_region_size = min_region_size  # Minimum size in pixels
        self.max_aspect_ratio_diff = max_aspect_ratio_diff  # Max aspect ratio difference

class TransformationResult:
    """Result of perspective transformation with metadata."""
    
    def __init__(
        self, 
        transformed_image: Image.Image,
        transformation_matrix: np.ndarray,
        source_corners: List[Tuple[float, float]],
        target_corners: List[Tuple[float, float]],
        original_size: Tuple[int, int],
        target_size: Tuple[int, int]
    ):
        self.transformed_image = transformed_image
        self.transformation_matrix = transformation_matrix
        self.source_corners = source_corners
        self.target_corners = target_corners
        self.original_size = original_size
        self.target_size = target_size

class PerspectiveTransformService:
    """Service for applying perspective transformations to artwork."""
    
    def __init__(self, config: Optional[PerspectiveTransformConfig] = None):
        self.config = config or PerspectiveTransformConfig()
    
    def transform_artwork_to_region(
        self, 
        artwork: Image.Image, 
        target_region: BoundingBox,
        mockup_size: Tuple[int, int],
        perspective_corners: Optional[List[Tuple[float, float]]] = None
    ) -> TransformationResult:
        """
        Transform artwork to fit into a detected region with proper perspective.
        
        Args:
            artwork: PIL Image of the artwork to transform
            target_region: BoundingBox representing the target region
            mockup_size: (width, height) of the mockup template
            perspective_corners: Optional custom corners for perspective effect
            
        Returns:
            TransformationResult containing transformed image and metadata
            
        Raises:
            PerspectiveTransformError: If transformation fails
        """
        try:
            # Validate inputs
            self._validate_inputs(artwork, target_region, mockup_size)
            
            # Calculate target corners
            if perspective_corners:
                target_corners = perspective_corners
            else:
                target_corners = self._calculate_perspective_corners(target_region)
            
            # Calculate source corners (artwork rectangle)
            source_corners = self._calculate_source_corners(artwork, target_region)
            
            # Calculate transformation matrix
            transform_matrix = self._calculate_transformation_matrix(
                source_corners, target_corners
            )
            
            # Apply transformation
            transformed_image = self._apply_transformation(
                artwork, transform_matrix, target_region, mockup_size
            )
            
            return TransformationResult(
                transformed_image=transformed_image,
                transformation_matrix=transform_matrix,
                source_corners=source_corners,
                target_corners=target_corners,
                original_size=artwork.size,
                target_size=(int(target_region.width), int(target_region.height))
            )
            
        except Exception as e:
            logger.error(f"Perspective transformation failed: {e}")
            raise PerspectiveTransformError(f"Failed to transform artwork: {e}")
    
    def _validate_inputs(
        self, 
        artwork: Image.Image, 
        target_region: BoundingBox, 
        mockup_size: Tuple[int, int]
    ):
        """Validate transformation inputs."""
        if artwork.size[0] == 0 or artwork.size[1] == 0:
            raise PerspectiveTransformError("Artwork has zero dimensions")
        
        if target_region.width < self.config.min_region_size or target_region.height < self.config.min_region_size:
            raise PerspectiveTransformError(
                f"Target region too small: {target_region.width}x{target_region.height} "
                f"(minimum: {self.config.min_region_size}x{self.config.min_region_size})"
            )
        
        # Check aspect ratio compatibility
        artwork_ratio = artwork.size[0] / artwork.size[1]
        region_ratio = target_region.width / target_region.height
        ratio_diff = max(artwork_ratio / region_ratio, region_ratio / artwork_ratio)
        
        if ratio_diff > self.config.max_aspect_ratio_diff:
            logger.warning(
                f"Large aspect ratio difference: artwork={artwork_ratio:.2f}, "
                f"region={region_ratio:.2f}, diff={ratio_diff:.2f}"
            )
    
    def _calculate_perspective_corners(
        self, 
        target_region: BoundingBox
    ) -> List[Tuple[float, float]]:
        """
        Calculate corner points for perspective transformation.
        
        Creates a subtle perspective effect by slightly adjusting corners.
        """
        x, y, w, h = target_region.x, target_region.y, target_region.width, target_region.height
        
        # Add subtle perspective distortion (simulating viewing angle)
        perspective_factor = 0.05  # 5% perspective distortion
        
        # Calculate corners with slight perspective
        top_left = (x, y)
        top_right = (x + w - w * perspective_factor * 0.5, y + h * perspective_factor * 0.3)
        bottom_right = (x + w, y + h)
        bottom_left = (x + w * perspective_factor * 0.3, y + h - h * perspective_factor * 0.2)
        
        return [top_left, top_right, bottom_right, bottom_left]
    
    def _calculate_source_corners(
        self, 
        artwork: Image.Image, 
        target_region: BoundingBox
    ) -> List[Tuple[float, float]]:
        """Calculate source corners from artwork, handling aspect ratio differences."""
        aw, ah = artwork.size
        tw, th = target_region.width, target_region.height
        
        # Calculate scaling to fit artwork into target region
        scale_w = tw / aw
        scale_h = th / ah
        scale = min(scale_w, scale_h)  # Maintain aspect ratio
        
        # Calculate centered position
        scaled_w = aw * scale
        scaled_h = ah * scale
        
        # Center the artwork in the available space
        offset_x = (tw - scaled_w) / 2
        offset_y = (th - scaled_h) / 2
        
        # Source corners (full artwork)
        return [
            (0, 0),           # top-left
            (aw, 0),          # top-right  
            (aw, ah),         # bottom-right
            (0, ah)           # bottom-left
        ]
    
    def _calculate_transformation_matrix(
        self,
        source_corners: List[Tuple[float, float]],
        target_corners: List[Tuple[float, float]]
    ) -> np.ndarray:
        """Calculate the perspective transformation matrix."""
        # Convert to numpy arrays
        src_pts = np.array(source_corners, dtype=np.float32)
        dst_pts = np.array(target_corners, dtype=np.float32)
        
        # Calculate perspective transformation matrix
        matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)
        
        return matrix
    
    def _apply_transformation(
        self,
        artwork: Image.Image,
        transform_matrix: np.ndarray,
        target_region: BoundingBox,
        mockup_size: Tuple[int, int]
    ) -> Image.Image:
        """Apply the perspective transformation to the artwork."""
        # Convert PIL to OpenCV format
        artwork_cv = cv2.cvtColor(np.array(artwork), cv2.COLOR_RGB2BGR)
        
        # Apply quality scaling if configured
        if self.config.quality_factor != 1.0:
            new_size = (
                int(artwork.size[0] * self.config.quality_factor),
                int(artwork.size[1] * self.config.quality_factor)
            )
            artwork_cv = cv2.resize(artwork_cv, new_size, interpolation=self.config.interpolation_method)
            
            # Scale transformation matrix accordingly
            scale_matrix = np.array([
                [self.config.quality_factor, 0, 0],
                [0, self.config.quality_factor, 0],
                [0, 0, 1]
            ])
            transform_matrix = scale_matrix @ transform_matrix
        
        # Calculate output size (region size with padding)
        padding = int(max(target_region.width, target_region.height) * self.config.padding_ratio)
        output_width = int(target_region.width + 2 * padding)
        output_height = int(target_region.height + 2 * padding)
        
        # Apply perspective transformation
        transformed_cv = cv2.warpPerspective(
            artwork_cv,
            transform_matrix,
            (output_width, output_height),
            flags=self.config.interpolation_method,
            borderMode=self.config.border_mode
        )
        
        # Convert back to PIL
        transformed_rgb = cv2.cvtColor(transformed_cv, cv2.COLOR_BGR2RGB)
        transformed_image = Image.fromarray(transformed_rgb)
        
        return transformed_image
    
    def create_composite_image(
        self,
        mockup_template: Image.Image,
        transformed_artwork: Image.Image,
        target_region: BoundingBox,
        blend_mode: str = "normal"
    ) -> Image.Image:
        """
        Composite the transformed artwork onto the mockup template.
        
        Args:
            mockup_template: Background mockup template
            transformed_artwork: Perspective-transformed artwork
            target_region: Region where artwork should be placed
            blend_mode: Blending mode ("normal", "multiply", "overlay")
            
        Returns:
            Composite image with artwork placed on mockup
        """
        try:
            # Create a copy of the mockup template
            composite = mockup_template.copy()
            
            # Calculate paste position (accounting for padding)
            padding = int(max(target_region.width, target_region.height) * self.config.padding_ratio)
            paste_x = int(target_region.x - padding)
            paste_y = int(target_region.y - padding)
            
            # Handle edge cases where paste position goes outside image bounds
            paste_x = max(0, paste_x)
            paste_y = max(0, paste_y)
            
            # Resize artwork if it extends beyond composite bounds
            max_width = composite.size[0] - paste_x
            max_height = composite.size[1] - paste_y
            
            if transformed_artwork.size[0] > max_width or transformed_artwork.size[1] > max_height:
                scale_factor = min(max_width / transformed_artwork.size[0], max_height / transformed_artwork.size[1])
                new_size = (
                    int(transformed_artwork.size[0] * scale_factor),
                    int(transformed_artwork.size[1] * scale_factor)
                )
                transformed_artwork = transformed_artwork.resize(new_size, Image.Resampling.LANCZOS)
            
            # Apply blending
            if blend_mode == "normal":
                # Simple paste with alpha blending if available
                if transformed_artwork.mode == "RGBA":
                    composite.paste(transformed_artwork, (paste_x, paste_y), transformed_artwork)
                else:
                    composite.paste(transformed_artwork, (paste_x, paste_y))
            else:
                # For other blend modes, use PIL's blend functionality
                # This is a simplified implementation - could be expanded
                composite.paste(transformed_artwork, (paste_x, paste_y))
            
            return composite
            
        except Exception as e:
            logger.error(f"Image composition failed: {e}")
            raise PerspectiveTransformError(f"Failed to composite images: {e}")
    
    def batch_transform_artworks(
        self,
        artworks: List[Image.Image],
        target_regions: List[BoundingBox],
        mockup_size: Tuple[int, int]
    ) -> List[TransformationResult]:
        """
        Transform multiple artworks to multiple regions efficiently.
        
        Args:
            artworks: List of artwork images to transform
            target_regions: List of target regions (must match artwork count)
            mockup_size: Size of the mockup template
            
        Returns:
            List of TransformationResult objects
        """
        if len(artworks) != len(target_regions):
            raise PerspectiveTransformError(
                f"Artwork count ({len(artworks)}) must match region count ({len(target_regions)})"
            )
        
        results = []
        for artwork, region in zip(artworks, target_regions):
            try:
                result = self.transform_artwork_to_region(artwork, region, mockup_size)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to transform artwork to region {region.label}: {e}")
                # Continue with other transformations
                continue
        
        return results

class PerspectiveTransformError(Exception):
    """Base exception for perspective transformation errors."""
    pass

def create_mock_perspective_service() -> 'MockPerspectiveTransformService':
    """
    Create a mock perspective transformation service for testing.
    
    Returns:
        MockPerspectiveTransformService instance
    """
    return MockPerspectiveTransformService()

class MockPerspectiveTransformService:
    """Mock implementation of PerspectiveTransformService for testing."""
    
    def __init__(self):
        self.config = PerspectiveTransformConfig()
    
    def transform_artwork_to_region(
        self, 
        artwork: Image.Image, 
        target_region: BoundingBox,
        mockup_size: Tuple[int, int],
        perspective_corners: Optional[List[Tuple[float, float]]] = None
    ) -> TransformationResult:
        """Mock transformation that returns a simple resized artwork."""
        # Simple resize to target region size
        target_size = (int(target_region.width), int(target_region.height))
        transformed_image = artwork.resize(target_size, Image.Resampling.LANCZOS)
        
        # Mock transformation matrix (identity)
        transform_matrix = np.eye(3)
        
        # Mock corners
        source_corners = [(0, 0), (artwork.size[0], 0), artwork.size, (0, artwork.size[1])]
        target_corners = target_region.get_corners()
        
        return TransformationResult(
            transformed_image=transformed_image,
            transformation_matrix=transform_matrix,
            source_corners=source_corners,
            target_corners=list(target_corners),
            original_size=artwork.size,
            target_size=target_size
        )
    
    def create_composite_image(
        self,
        mockup_template: Image.Image,
        transformed_artwork: Image.Image,
        target_region: BoundingBox,
        blend_mode: str = "normal"
    ) -> Image.Image:
        """Mock composition that simply pastes artwork onto template."""
        composite = mockup_template.copy()
        paste_x = int(target_region.x)
        paste_y = int(target_region.y)
        
        # Ensure artwork fits
        max_width = composite.size[0] - paste_x
        max_height = composite.size[1] - paste_y
        
        if transformed_artwork.size[0] > max_width or transformed_artwork.size[1] > max_height:
            scale_factor = min(max_width / transformed_artwork.size[0], max_height / transformed_artwork.size[1])
            new_size = (
                int(transformed_artwork.size[0] * scale_factor),
                int(transformed_artwork.size[1] * scale_factor)
            )
            transformed_artwork = transformed_artwork.resize(new_size, Image.Resampling.LANCZOS)
        
        composite.paste(transformed_artwork, (paste_x, paste_y))
        return composite
    
    def batch_transform_artworks(
        self,
        artworks: List[Image.Image],
        target_regions: List[BoundingBox],
        mockup_size: Tuple[int, int]
    ) -> List[TransformationResult]:
        """Mock batch transformation."""
        results = []
        for artwork, region in zip(artworks, target_regions):
            result = self.transform_artwork_to_region(artwork, region, mockup_size)
            results.append(result)
        return results