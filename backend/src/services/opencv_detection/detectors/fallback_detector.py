"""
Fallback detector for when other detection methods fail
"""

import cv2
import numpy as np
from typing import List, Tuple
import logging

from ..base import BaseDetector, BoundingBox
from ..config import OpenCVObjectDetectionConfig

logger = logging.getLogger(__name__)


class FallbackDetector(BaseDetector):
    """
    Fallback detector that provides sensible default regions.
    
    This detector is used when other detection methods fail to find
    suitable regions. It provides common placement areas based on
    image composition rules.
    """
    
    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect fallback regions based on image composition rules.
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            List of detected BoundingBox regions
        """
        try:
            logger.debug(f"{self.name}: Starting fallback detection")
            
            height, width = image.shape[:2]
            regions = []
            
            # 1. Center region (rule of thirds center)
            center_region = self._get_center_region(width, height)
            regions.append(center_region)
            
            # 2. Golden ratio regions
            golden_regions = self._get_golden_ratio_regions(width, height)
            regions.extend(golden_regions)
            
            # 3. Rule of thirds intersections
            thirds_regions = self._get_rule_of_thirds_regions(width, height)
            regions.extend(thirds_regions)
            
            # 4. Safe area regions (avoiding edges)
            safe_regions = self._get_safe_area_regions(width, height)
            regions.extend(safe_regions)
            
            # 5. Aspect ratio based regions
            aspect_regions = self._get_aspect_ratio_regions(width, height)
            regions.extend(aspect_regions)
            
            # Remove duplicates and filter
            unique_regions = self._remove_duplicate_regions(regions)
            filtered_regions = self.filter_regions(unique_regions, image.shape)
            
            # Sort by confidence (highest first)
            filtered_regions.sort(key=lambda x: x.confidence, reverse=True)
            
            # Limit number of fallback regions
            max_fallback = min(5, self.config.max_detections)
            filtered_regions = filtered_regions[:max_fallback]
            
            logger.info(f"{self.name}: Generated {len(filtered_regions)} fallback regions")
            return filtered_regions
            
        except Exception as e:
            logger.error(f"{self.name}: Fallback detection failed - {e}")
            # Last resort - return center region
            return [self._get_center_region(image.shape[1], image.shape[0])]
    
    def _get_center_region(self, width: int, height: int) -> BoundingBox:
        """Get a centered region."""
        # Use 40% of the smaller dimension
        size = int(min(width, height) * 0.4)
        x = (width - size) // 2
        y = (height - size) // 2
        
        return BoundingBox(
            x=float(x),
            y=float(y),
            width=float(size),
            height=float(size),
            confidence=0.7,
            label="fallback_center"
        )
    
    def _get_golden_ratio_regions(self, width: int, height: int) -> List[BoundingBox]:
        """Get regions based on golden ratio positioning."""
        regions = []
        golden_ratio = 1.618
        
        # Horizontal golden ratio
        golden_x1 = int(width / golden_ratio)
        golden_x2 = width - golden_x1
        
        # Vertical golden ratio
        golden_y1 = int(height / golden_ratio)
        golden_y2 = height - golden_y1
        
        # Create regions at golden ratio intersections
        region_size = int(min(width, height) * 0.3)
        
        positions = [
            (golden_x1 - region_size//2, golden_y1 - region_size//2),
            (golden_x2 - region_size//2, golden_y1 - region_size//2),
            (golden_x1 - region_size//2, golden_y2 - region_size//2),
            (golden_x2 - region_size//2, golden_y2 - region_size//2),
        ]
        
        for i, (x, y) in enumerate(positions):
            # Ensure within bounds
            x = max(0, min(x, width - region_size))
            y = max(0, min(y, height - region_size))
            
            regions.append(BoundingBox(
                x=float(x),
                y=float(y),
                width=float(region_size),
                height=float(region_size),
                confidence=0.65,
                label=f"fallback_golden_{i}"
            ))
        
        return regions
    
    def _get_rule_of_thirds_regions(self, width: int, height: int) -> List[BoundingBox]:
        """Get regions based on rule of thirds."""
        regions = []
        
        # Calculate thirds
        third_x = width // 3
        third_y = height // 3
        
        # Region size based on image size
        region_width = int(width * 0.25)
        region_height = int(height * 0.25)
        
        # Create regions at intersection points
        positions = [
            (third_x, third_y),
            (2 * third_x, third_y),
            (third_x, 2 * third_y),
            (2 * third_x, 2 * third_y),
        ]
        
        for i, (cx, cy) in enumerate(positions):
            x = cx - region_width // 2
            y = cy - region_height // 2
            
            # Ensure within bounds
            x = max(0, min(x, width - region_width))
            y = max(0, min(y, height - region_height))
            
            regions.append(BoundingBox(
                x=float(x),
                y=float(y),
                width=float(region_width),
                height=float(region_height),
                confidence=0.6,
                label=f"fallback_thirds_{i}"
            ))
        
        return regions
    
    def _get_safe_area_regions(self, width: int, height: int) -> List[BoundingBox]:
        """Get regions in safe areas (avoiding edges)."""
        regions = []
        
        # Define safe margins (10% from edges)
        margin_x = int(width * 0.1)
        margin_y = int(height * 0.1)
        
        safe_width = width - 2 * margin_x
        safe_height = height - 2 * margin_y
        
        # Large central safe area
        large_size = int(min(safe_width, safe_height) * 0.6)
        if large_size > 50:  # Minimum size check
            x = margin_x + (safe_width - large_size) // 2
            y = margin_y + (safe_height - large_size) // 2
            
            regions.append(BoundingBox(
                x=float(x),
                y=float(y),
                width=float(large_size),
                height=float(large_size),
                confidence=0.55,
                label="fallback_safe_large"
            ))
        
        # Medium safe areas in quadrants
        medium_size = int(min(safe_width, safe_height) * 0.35)
        if medium_size > 50:
            quadrants = [
                (margin_x, margin_y),
                (width - margin_x - medium_size, margin_y),
                (margin_x, height - margin_y - medium_size),
                (width - margin_x - medium_size, height - margin_y - medium_size),
            ]
            
            for i, (x, y) in enumerate(quadrants):
                regions.append(BoundingBox(
                    x=float(x),
                    y=float(y),
                    width=float(medium_size),
                    height=float(medium_size),
                    confidence=0.5,
                    label=f"fallback_safe_quad_{i}"
                ))
        
        return regions
    
    def _get_aspect_ratio_regions(self, width: int, height: int) -> List[BoundingBox]:
        """Get regions with common aspect ratios."""
        regions = []
        
        # Common aspect ratios for mockups
        aspect_ratios = [
            (1.0, "square"),      # Square
            (1.5, "photo"),       # 3:2 photo ratio
            (1.33, "classic"),    # 4:3 classic ratio
            (1.77, "widescreen"), # 16:9 widescreen
        ]
        
        for ratio, label in aspect_ratios:
            # Try both orientations
            for is_landscape in [True, False]:
                if is_landscape:
                    region_width = int(min(width * 0.5, height * 0.5 * ratio))
                    region_height = int(region_width / ratio)
                else:
                    region_height = int(min(height * 0.5, width * 0.5 * ratio))
                    region_width = int(region_height / ratio)
                
                # Check if region fits
                if region_width <= width and region_height <= height and \
                   region_width > 50 and region_height > 50:
                    
                    # Center the region
                    x = (width - region_width) // 2
                    y = (height - region_height) // 2
                    
                    regions.append(BoundingBox(
                        x=float(x),
                        y=float(y),
                        width=float(region_width),
                        height=float(region_height),
                        confidence=0.45,
                        label=f"fallback_{label}"
                    ))
        
        return regions
    
    def _remove_duplicate_regions(self, regions: List[BoundingBox]) -> List[BoundingBox]:
        """Remove duplicate or highly overlapping regions."""
        if not regions:
            return []
        
        # Sort by confidence
        regions = sorted(regions, key=lambda x: x.confidence, reverse=True)
        
        # Keep track of unique regions
        unique = []
        
        for region in regions:
            is_duplicate = False
            
            for unique_region in unique:
                iou = region.intersection_over_union(unique_region)
                if iou > 0.7:  # High overlap threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(region)
        
        return unique