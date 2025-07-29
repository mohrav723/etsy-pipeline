"""
Base classes and interfaces for OpenCV object detection
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Represents a detected object's bounding box with metadata."""
    
    x: float
    y: float
    width: float
    height: float
    confidence: float
    label: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bounding box to dictionary format."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'confidence': self.confidence,
            'label': self.label
        }
    
    def get_corners(self) -> Tuple[Tuple[float, float], ...]:
        """Get the four corners of the bounding box."""
        return (
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        )
    
    def get_center(self) -> Tuple[float, float]:
        """Get the center point of the bounding box."""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def get_area(self) -> float:
        """Calculate the area of the bounding box."""
        return self.width * self.height
    
    def get_aspect_ratio(self) -> float:
        """Calculate the aspect ratio (width/height) of the bounding box."""
        return self.width / self.height if self.height > 0 else 0
    
    def overlaps_with(self, other: 'BoundingBox') -> bool:
        """Check if this bounding box overlaps with another."""
        return not (self.x + self.width < other.x or 
                   other.x + other.width < self.x or
                   self.y + self.height < other.y or
                   other.y + other.height < self.y)
    
    def intersection_over_union(self, other: 'BoundingBox') -> float:
        """Calculate IoU (Intersection over Union) with another bounding box."""
        if not self.overlaps_with(other):
            return 0.0
        
        # Calculate intersection area
        x_left = max(self.x, other.x)
        y_top = max(self.y, other.y)
        x_right = min(self.x + self.width, other.x + other.width)
        y_bottom = min(self.y + self.height, other.y + other.height)
        
        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        
        # Calculate union area
        union_area = self.get_area() + other.get_area() - intersection_area
        
        return intersection_area / union_area if union_area > 0 else 0


class BaseDetector(ABC):
    """Abstract base class for all detection algorithms."""
    
    def __init__(self, config: 'OpenCVObjectDetectionConfig'):
        """
        Initialize the detector with configuration.
        
        Args:
            config: Configuration object with detection parameters
        """
        self.config = config
        self.name = self.__class__.__name__
        
    @abstractmethod
    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect suitable regions in the image.
        
        Args:
            image: OpenCV image (numpy array) in BGR format
            
        Returns:
            List of BoundingBox objects representing detected regions
        """
        pass
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Common preprocessing steps for images.
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed image
        """
        # This can be overridden by specific detectors
        return image
    
    def filter_regions(self, regions: List[BoundingBox], 
                      image_shape: Tuple[int, int, int]) -> List[BoundingBox]:
        """
        Filter detected regions based on size and position constraints.
        
        Args:
            regions: List of detected regions
            image_shape: Shape of the original image (height, width, channels)
            
        Returns:
            Filtered list of regions
        """
        height, width = image_shape[:2]
        image_area = height * width
        
        filtered = []
        for region in regions:
            # Check if region is within image bounds
            if (region.x < 0 or region.y < 0 or 
                region.x + region.width > width or 
                region.y + region.height > height):
                logger.debug(f"Skipping out-of-bounds region: {region.label}")
                continue
            
            # Check minimum area
            region_area = region.get_area()
            if region_area < image_area * self.config.min_area_ratio:
                logger.debug(f"Skipping too small region: {region.label} "
                           f"(area: {region_area/image_area:.2%} of image)")
                continue
            
            # Check maximum area
            if region_area > image_area * self.config.max_area_ratio:
                logger.debug(f"Skipping too large region: {region.label} "
                           f"(area: {region_area/image_area:.2%} of image)")
                continue
            
            # Check aspect ratio
            aspect_ratio = region.get_aspect_ratio()
            if (aspect_ratio < self.config.aspect_ratio_range[0] or 
                aspect_ratio > self.config.aspect_ratio_range[1]):
                logger.debug(f"Skipping region with bad aspect ratio: {region.label} "
                           f"(ratio: {aspect_ratio:.2f})")
                continue
            
            # Check confidence threshold
            if region.confidence < self.config.confidence_threshold:
                logger.debug(f"Skipping low confidence region: {region.label} "
                           f"(confidence: {region.confidence:.2f})")
                continue
            
            filtered.append(region)
        
        return filtered
    
    def merge_overlapping_regions(self, regions: List[BoundingBox], 
                                 iou_threshold: float = 0.5) -> List[BoundingBox]:
        """
        Merge overlapping regions based on IoU threshold.
        
        Args:
            regions: List of regions to merge
            iou_threshold: Minimum IoU to consider regions as overlapping
            
        Returns:
            List of merged regions
        """
        if not regions:
            return []
        
        # Sort by confidence (highest first)
        sorted_regions = sorted(regions, key=lambda r: r.confidence, reverse=True)
        merged = []
        
        for region in sorted_regions:
            # Check if this region overlaps significantly with any merged region
            should_merge = False
            for i, merged_region in enumerate(merged):
                if region.intersection_over_union(merged_region) > iou_threshold:
                    # Merge by taking the union of the two regions
                    x_min = min(region.x, merged_region.x)
                    y_min = min(region.y, merged_region.y)
                    x_max = max(region.x + region.width, 
                               merged_region.x + merged_region.width)
                    y_max = max(region.y + region.height, 
                               merged_region.y + merged_region.height)
                    
                    # Create merged region with higher confidence
                    merged[i] = BoundingBox(
                        x=x_min,
                        y=y_min,
                        width=x_max - x_min,
                        height=y_max - y_min,
                        confidence=max(region.confidence, merged_region.confidence),
                        label=f"{merged_region.label}+{region.label}"
                    )
                    should_merge = True
                    break
            
            if not should_merge:
                merged.append(region)
        
        return merged


class ObjectDetectionError(Exception):
    """Base exception for object detection errors."""
    pass


class NoSuitableRegionsError(ObjectDetectionError):
    """Raised when no suitable regions are found for artwork placement."""
    pass