"""
Color-based object detection for finding uniform color regions
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

from ..base import BaseDetector, BoundingBox
from ..config import OpenCVObjectDetectionConfig

logger = logging.getLogger(__name__)


class ColorBasedDetector(BaseDetector):
    """
    Detects uniform color regions that could be suitable for artwork placement.
    
    This detector identifies areas with consistent color that might represent
    surfaces, screens, or other placement areas in mockup templates.
    """
    
    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect uniform color regions suitable for artwork placement.
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            List of detected BoundingBox regions
        """
        try:
            logger.debug(f"{self.name}: Starting color-based detection")
            
            # Convert to different color spaces for analysis
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            
            # Find uniform color regions
            color_masks = self._find_uniform_color_regions(image, lab, hsv)
            
            # Extract regions from masks
            all_regions = []
            for mask in color_masks:
                regions = self._extract_regions_from_mask(mask)
                all_regions.extend(regions)
            
            # Convert to bounding boxes
            bounding_boxes = self._regions_to_bounding_boxes(all_regions, image.shape)
            
            # Filter regions
            filtered_boxes = self.filter_regions(bounding_boxes, image.shape)
            
            logger.info(f"{self.name}: Detected {len(filtered_boxes)} color regions")
            return filtered_boxes
            
        except Exception as e:
            logger.error(f"{self.name}: Detection failed - {e}")
            return []
    
    def _find_uniform_color_regions(self, bgr: np.ndarray, lab: np.ndarray, 
                                   hsv: np.ndarray) -> List[np.ndarray]:
        """
        Find regions with uniform color using multiple color spaces.
        
        Args:
            bgr: Image in BGR color space
            lab: Image in LAB color space
            hsv: Image in HSV color space
            
        Returns:
            List of binary masks for uniform regions
        """
        masks = []
        
        # 1. Find regions with low color variance in LAB space
        lab_mask = self._find_low_variance_regions(lab)
        if lab_mask is not None:
            masks.append(lab_mask)
        
        # 2. Find dominant color regions
        dominant_masks = self._find_dominant_color_regions(bgr)
        masks.extend(dominant_masks)
        
        # 3. Find regions with consistent hue
        hue_mask = self._find_consistent_hue_regions(hsv)
        if hue_mask is not None:
            masks.append(hue_mask)
        
        # 4. Find neutral color regions (grays, whites, blacks)
        neutral_mask = self._find_neutral_regions(lab)
        if neutral_mask is not None:
            masks.append(neutral_mask)
        
        return masks
    
    def _find_low_variance_regions(self, lab: np.ndarray) -> Optional[np.ndarray]:
        """
        Find regions with low color variance in LAB space.
        
        Args:
            lab: Image in LAB color space
            
        Returns:
            Binary mask of low variance regions
        """
        # Calculate local color variance
        kernel_size = 15
        
        # Calculate mean and variance for each channel
        l_channel = lab[:, :, 0].astype(np.float32)
        
        # Local mean
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        local_mean = cv2.filter2D(l_channel, -1, kernel)
        
        # Local variance
        local_mean_sq = cv2.filter2D(l_channel ** 2, -1, kernel)
        local_variance = local_mean_sq - local_mean ** 2
        
        # Threshold variance to find uniform regions
        variance_threshold = self.config.color_threshold
        uniform_mask = (local_variance < variance_threshold).astype(np.uint8) * 255
        
        # Clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        uniform_mask = cv2.morphologyEx(uniform_mask, cv2.MORPH_OPEN, kernel)
        uniform_mask = cv2.morphologyEx(uniform_mask, cv2.MORPH_CLOSE, kernel)
        
        # Check if we found significant regions
        if np.sum(uniform_mask) < self.config.min_color_region_size:
            return None
        
        return uniform_mask
    
    def _find_dominant_color_regions(self, bgr: np.ndarray) -> List[np.ndarray]:
        """
        Find regions belonging to dominant colors in the image.
        
        Args:
            bgr: Image in BGR color space
            
        Returns:
            List of binary masks for dominant color regions
        """
        masks = []
        
        # Downsample for faster processing
        scale = 0.25
        small = cv2.resize(bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        
        # Reshape for clustering
        pixels = small.reshape(-1, 3)
        
        # Use k-means to find dominant colors
        try:
            from sklearn.cluster import KMeans
            n_colors = 5
            kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
            kmeans.fit(pixels)
        except ImportError:
            # Fallback to simple color quantization if sklearn not available
            logger.warning("sklearn not available, using simple color quantization")
            # Simple quantization by reducing color space
            pixels_quant = (pixels // 32) * 32
            unique_colors = np.unique(pixels_quant.reshape(-1, pixels_quant.shape[-1]), axis=0)
            # Take top 5 most common colors
            kmeans = type('obj', (object,), {'cluster_centers_': unique_colors[:5]})
        
        # For each dominant color, create a mask
        for i, center in enumerate(kmeans.cluster_centers_):
            # Create mask for this color
            color_lower = np.array(center - self.config.color_threshold, dtype=np.uint8)
            color_upper = np.array(center + self.config.color_threshold, dtype=np.uint8)
            
            mask = cv2.inRange(bgr, color_lower, color_upper)
            
            # Clean up the mask
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Check if this color covers significant area
            if np.sum(mask) > self.config.min_color_region_size:
                masks.append(mask)
        
        return masks
    
    def _find_consistent_hue_regions(self, hsv: np.ndarray) -> Optional[np.ndarray]:
        """
        Find regions with consistent hue values.
        
        Args:
            hsv: Image in HSV color space
            
        Returns:
            Binary mask of consistent hue regions
        """
        h, s, v = cv2.split(hsv)
        
        # Only consider pixels with sufficient saturation and value
        # (to avoid including black/white/gray pixels)
        color_pixels = (s > 30) & (v > 30)
        
        if np.sum(color_pixels) < self.config.min_color_region_size:
            return None
        
        # Calculate hue variance in local windows
        kernel_size = 11
        kernel = np.ones((kernel_size, kernel_size), np.float32) / (kernel_size * kernel_size)
        
        # Convert hue to continuous representation for variance calculation
        hue_sin = np.sin(h * np.pi / 90).astype(np.float32)
        hue_cos = np.cos(h * np.pi / 90).astype(np.float32)
        
        # Local variance of hue
        local_sin_mean = cv2.filter2D(hue_sin, -1, kernel)
        local_cos_mean = cv2.filter2D(hue_cos, -1, kernel)
        
        local_sin_var = cv2.filter2D(hue_sin ** 2, -1, kernel) - local_sin_mean ** 2
        local_cos_var = cv2.filter2D(hue_cos ** 2, -1, kernel) - local_cos_mean ** 2
        
        hue_variance = local_sin_var + local_cos_var
        
        # Find regions with low hue variance
        consistent_hue = (hue_variance < 0.1) & color_pixels
        mask = consistent_hue.astype(np.uint8) * 255
        
        # Clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        return mask
    
    def _find_neutral_regions(self, lab: np.ndarray) -> Optional[np.ndarray]:
        """
        Find neutral color regions (grays, whites, blacks).
        
        Args:
            lab: Image in LAB color space
            
        Returns:
            Binary mask of neutral regions
        """
        l, a, b = cv2.split(lab)
        
        # Neutral colors have low a and b values (close to 0 in LAB)
        # LAB values are shifted by 128 in OpenCV
        neutral_threshold = 15
        neutral_mask = (np.abs(a.astype(np.int16) - 128) < neutral_threshold) & \
                      (np.abs(b.astype(np.int16) - 128) < neutral_threshold)
        
        mask = neutral_mask.astype(np.uint8) * 255
        
        # Clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Check if we found significant regions
        if np.sum(mask) < self.config.min_color_region_size:
            return None
        
        return mask
    
    def _extract_regions_from_mask(self, mask: np.ndarray) -> List[Tuple[np.ndarray, float]]:
        """
        Extract individual regions from a binary mask.
        
        Args:
            mask: Binary mask
            
        Returns:
            List of (contour, confidence) tuples
        """
        regions = []
        
        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        
        # Skip background (label 0)
        for label in range(1, num_labels):
            # Get region statistics
            x, y, w, h, area = stats[label]
            
            if area < self.config.min_color_region_size:
                continue
            
            # Extract region mask
            region_mask = (labels == label).astype(np.uint8) * 255
            
            # Find contour of this region
            contours, _ = cv2.findContours(region_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                contour = contours[0]
                
                # Calculate confidence based on how filled the region is
                bbox_area = w * h
                fill_ratio = area / bbox_area if bbox_area > 0 else 0
                confidence = fill_ratio * 0.9  # Max 0.9 for color-based detection
                
                regions.append((contour, confidence))
        
        return regions
    
    def _regions_to_bounding_boxes(self, regions: List[Tuple[np.ndarray, float]], 
                                  image_shape: Tuple[int, ...]) -> List[BoundingBox]:
        """
        Convert regions to BoundingBox objects.
        
        Args:
            regions: List of (contour, confidence) tuples
            image_shape: Shape of the original image
            
        Returns:
            List of BoundingBox objects
        """
        bounding_boxes = []
        
        for contour, confidence in regions:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Create bounding box
            bbox = BoundingBox(
                x=float(x),
                y=float(y),
                width=float(w),
                height=float(h),
                confidence=confidence,
                label="color_region"
            )
            
            bounding_boxes.append(bbox)
        
        return bounding_boxes