"""
Edge-based object detection using Canny edge detection and contour analysis
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

from ..base import BaseDetector, BoundingBox
from ..config import OpenCVObjectDetectionConfig
from ..utils import apply_clahe

logger = logging.getLogger(__name__)


class EdgeBasedDetector(BaseDetector):
    """
    Detects regions using edge detection algorithms.
    
    This detector uses Canny edge detection to find edges in the image,
    then analyzes contours to identify rectangular regions suitable for
    artwork placement.
    """
    
    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect suitable regions using edge detection.
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            List of detected BoundingBox regions
        """
        try:
            logger.debug(f"{self.name}: Starting edge-based detection")
            
            # Preprocess image
            preprocessed = self._preprocess_for_edge_detection(image)
            
            # Apply Canny edge detection
            edges = self._apply_canny_edge_detection(preprocessed)
            
            # Find contours from edges
            contours = self._find_contours_from_edges(edges)
            
            # Convert contours to bounding boxes
            bounding_boxes = self._contours_to_bounding_boxes(contours, image.shape)
            
            # Filter regions
            filtered_boxes = self.filter_regions(bounding_boxes, image.shape)
            
            logger.info(f"{self.name}: Detected {len(filtered_boxes)} regions")
            return filtered_boxes
            
        except Exception as e:
            logger.error(f"{self.name}: Detection failed - {e}")
            return []
    
    def _preprocess_for_edge_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better edge detection.
        
        Args:
            image: Input image
            
        Returns:
            Preprocessed grayscale image
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, self.config.gaussian_blur_kernel, 0)
        
        # Apply CLAHE for better contrast
        enhanced = apply_clahe(blurred, clip_limit=2.0, tile_grid_size=(8, 8))
        
        return enhanced
    
    def _apply_canny_edge_detection(self, image: np.ndarray) -> np.ndarray:
        """
        Apply Canny edge detection with configured thresholds.
        
        Args:
            image: Preprocessed grayscale image
            
        Returns:
            Binary edge map
        """
        edges = cv2.Canny(
            image,
            threshold1=self.config.canny_low_threshold,
            threshold2=self.config.canny_high_threshold,
            apertureSize=3,
            L2gradient=True
        )
        
        # Apply morphological operations to connect nearby edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return edges
    
    def _find_contours_from_edges(self, edges: np.ndarray) -> List[np.ndarray]:
        """
        Find contours from edge map.
        
        Args:
            edges: Binary edge map
            
        Returns:
            List of contours
        """
        # Find contours
        contours, hierarchy = cv2.findContours(
            edges,
            cv2.RETR_EXTERNAL,  # Only external contours
            cv2.CHAIN_APPROX_SIMPLE  # Compress horizontal, vertical, diagonal segments
        )
        
        # Filter contours by area
        min_area = self.config.min_contour_area
        filtered_contours = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area >= min_area:
                filtered_contours.append(contour)
        
        logger.debug(f"Found {len(filtered_contours)} contours with sufficient area")
        return filtered_contours
    
    def _contours_to_bounding_boxes(self, contours: List[np.ndarray], 
                                   image_shape: Tuple[int, ...]) -> List[BoundingBox]:
        """
        Convert contours to bounding boxes with confidence scores.
        
        Args:
            contours: List of contours
            image_shape: Shape of the original image
            
        Returns:
            List of BoundingBox objects
        """
        bounding_boxes = []
        height, width = image_shape[:2]
        
        for contour in contours:
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate confidence based on how rectangular the contour is
            confidence = self._calculate_rectangularity_score(contour, (x, y, w, h))
            
            # Skip if confidence is too low
            if confidence < self.config.confidence_threshold:
                continue
            
            # Check if this could be a frame or border
            is_frame = self._check_if_frame_like(x, y, w, h, width, height)
            
            # Create bounding box
            bbox = BoundingBox(
                x=float(x),
                y=float(y),
                width=float(w),
                height=float(h),
                confidence=confidence,
                label="edge_frame" if is_frame else "edge_region"
            )
            
            bounding_boxes.append(bbox)
        
        return bounding_boxes
    
    def _calculate_rectangularity_score(self, contour: np.ndarray, 
                                       rect: Tuple[int, int, int, int]) -> float:
        """
        Calculate how rectangular a contour is.
        
        Args:
            contour: The contour to analyze
            rect: Bounding rectangle (x, y, w, h)
            
        Returns:
            Confidence score between 0 and 1
        """
        x, y, w, h = rect
        
        # Calculate contour area vs rectangle area
        contour_area = cv2.contourArea(contour)
        rect_area = w * h
        
        if rect_area == 0:
            return 0.0
        
        area_ratio = contour_area / rect_area
        
        # Approximate contour to polygon
        perimeter = cv2.arcLength(contour, True)
        epsilon = self.config.contour_approximation_epsilon * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # Score based on number of vertices (4 is ideal for rectangle)
        vertex_score = 1.0 if len(approx) == 4 else 0.7 if len(approx) in [3, 5, 6] else 0.5
        
        # Check if approximated polygon is convex
        convexity_score = 1.0 if cv2.isContourConvex(approx) else 0.8
        
        # Combine scores
        confidence = area_ratio * 0.4 + vertex_score * 0.4 + convexity_score * 0.2
        
        return min(confidence, 1.0)
    
    def _check_if_frame_like(self, x: int, y: int, w: int, h: int,
                            img_width: int, img_height: int) -> bool:
        """
        Check if a bounding box looks like a frame or border.
        
        Args:
            x, y, w, h: Bounding box coordinates
            img_width, img_height: Image dimensions
            
        Returns:
            True if the box appears to be a frame
        """
        # Check if box is near image edges
        edge_margin = 50  # pixels
        near_edge = (x < edge_margin or y < edge_margin or 
                    x + w > img_width - edge_margin or 
                    y + h > img_height - edge_margin)
        
        # Check aspect ratio (frames are often more square)
        aspect_ratio = w / h if h > 0 else 0
        good_aspect = 0.5 <= aspect_ratio <= 2.0
        
        # Check if it's a reasonable size for a frame
        area_ratio = (w * h) / (img_width * img_height)
        good_size = 0.05 <= area_ratio <= 0.7
        
        return near_edge and good_aspect and good_size