"""
Contour-based object detection focusing on rectangular shapes
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging

from ..base import BaseDetector, BoundingBox
from ..config import OpenCVObjectDetectionConfig

logger = logging.getLogger(__name__)


class ContourBasedDetector(BaseDetector):
    """
    Detects rectangular regions using contour analysis.
    
    This detector uses adaptive thresholding and contour analysis to find
    rectangular shapes that could be suitable for artwork placement.
    """
    
    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect rectangular regions using contour analysis.
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            List of detected BoundingBox regions
        """
        try:
            logger.debug(f"{self.name}: Starting contour-based detection")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Apply multiple thresholding techniques
            binary_images = self._create_binary_images(gray)
            
            # Find rectangles in each binary image
            all_rectangles = []
            for binary in binary_images:
                rectangles = self._find_rectangles(binary)
                all_rectangles.extend(rectangles)
            
            # Remove duplicates and convert to bounding boxes
            unique_rectangles = self._remove_duplicate_rectangles(all_rectangles)
            bounding_boxes = self._rectangles_to_bounding_boxes(unique_rectangles, image.shape)
            
            # Filter regions
            filtered_boxes = self.filter_regions(bounding_boxes, image.shape)
            
            logger.info(f"{self.name}: Detected {len(filtered_boxes)} rectangular regions")
            return filtered_boxes
            
        except Exception as e:
            logger.error(f"{self.name}: Detection failed - {e}")
            return []
    
    def _create_binary_images(self, gray: np.ndarray) -> List[np.ndarray]:
        """
        Create multiple binary images using different thresholding techniques.
        
        Args:
            gray: Grayscale image
            
        Returns:
            List of binary images
        """
        binary_images = []
        
        # 1. Adaptive threshold (Gaussian)
        adaptive_gaussian = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )
        binary_images.append(adaptive_gaussian)
        
        # 2. Adaptive threshold (Mean)
        adaptive_mean = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=3
        )
        binary_images.append(adaptive_mean)
        
        # 3. Otsu's thresholding
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary_images.append(otsu)
        
        # 4. Inverse adaptive threshold (for dark regions)
        adaptive_inv = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            blockSize=11,
            C=2
        )
        binary_images.append(adaptive_inv)
        
        return binary_images
    
    def _find_rectangles(self, binary: np.ndarray) -> List[Tuple[np.ndarray, float]]:
        """
        Find rectangular contours in a binary image.
        
        Args:
            binary: Binary image
            
        Returns:
            List of (contour, confidence) tuples
        """
        rectangles = []
        
        # Find contours
        contours, hierarchy = cv2.findContours(
            binary,
            cv2.RETR_TREE,  # Retrieve all contours with hierarchy
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        for i, contour in enumerate(contours):
            # Skip if area is too small
            area = cv2.contourArea(contour)
            if area < self.config.min_contour_area:
                continue
            
            # Approximate contour to polygon
            perimeter = cv2.arcLength(contour, True)
            epsilon = self.config.contour_approximation_epsilon * perimeter
            approx = cv2.approxPolyDP(contour, epsilon, True)
            
            # Check if it's a quadrilateral
            if len(approx) == 4:
                # Check if it's rectangular enough
                rect_score = self._calculate_rectangle_score(approx)
                if rect_score > 0.7:  # Threshold for rectangularity
                    rectangles.append((contour, rect_score))
            
            # Also check if the bounding rect is close to the contour
            elif 3 <= len(approx) <= 6:
                x, y, w, h = cv2.boundingRect(contour)
                rect_area = w * h
                if rect_area > 0 and area / rect_area > 0.8:
                    # It's close to rectangular
                    rectangles.append((contour, 0.8))
        
        return rectangles
    
    def _calculate_rectangle_score(self, approx: np.ndarray) -> float:
        """
        Calculate how close a quadrilateral is to being a rectangle.
        
        Args:
            approx: 4-point approximated contour
            
        Returns:
            Score between 0 and 1 (1 being perfect rectangle)
        """
        if len(approx) != 4:
            return 0.0
        
        # Get the four corners
        pts = approx.reshape(4, 2)
        
        # Calculate angles at each corner
        angles = []
        for i in range(4):
            p1 = pts[i]
            p2 = pts[(i + 1) % 4]
            p3 = pts[(i - 1) % 4]
            
            v1 = p1 - p3
            v2 = p2 - p1
            
            # Calculate angle using dot product
            cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
            angle = np.arccos(np.clip(cosine, -1, 1))
            angles.append(np.degrees(angle))
        
        # Perfect rectangle has 90-degree angles
        angle_scores = [1.0 - abs(90 - angle) / 90 for angle in angles]
        avg_angle_score = np.mean(angle_scores)
        
        # Check if opposite sides are parallel and equal
        side_lengths = []
        for i in range(4):
            p1 = pts[i]
            p2 = pts[(i + 1) % 4]
            length = np.linalg.norm(p2 - p1)
            side_lengths.append(length)
        
        # Check if opposite sides are similar in length
        length_ratio1 = min(side_lengths[0], side_lengths[2]) / (max(side_lengths[0], side_lengths[2]) + 1e-10)
        length_ratio2 = min(side_lengths[1], side_lengths[3]) / (max(side_lengths[1], side_lengths[3]) + 1e-10)
        length_score = (length_ratio1 + length_ratio2) / 2
        
        # Combine scores
        total_score = avg_angle_score * 0.7 + length_score * 0.3
        
        return total_score
    
    def _remove_duplicate_rectangles(self, rectangles: List[Tuple[np.ndarray, float]]) -> List[Tuple[np.ndarray, float]]:
        """
        Remove duplicate rectangles based on their bounding boxes.
        
        Args:
            rectangles: List of (contour, confidence) tuples
            
        Returns:
            List of unique rectangles
        """
        if not rectangles:
            return []
        
        # Convert to bounding boxes for comparison
        rect_data = []
        for contour, conf in rectangles:
            x, y, w, h = cv2.boundingRect(contour)
            rect_data.append((x, y, w, h, contour, conf))
        
        # Sort by confidence (highest first)
        rect_data.sort(key=lambda r: r[5], reverse=True)
        
        # Remove duplicates
        unique = []
        for i, (x1, y1, w1, h1, cont1, conf1) in enumerate(rect_data):
            is_duplicate = False
            
            for x2, y2, w2, h2, cont2, conf2 in unique:
                # Check IoU
                x_left = max(x1, x2)
                y_top = max(y1, y2)
                x_right = min(x1 + w1, x2 + w2)
                y_bottom = min(y1 + h1, y2 + h2)
                
                if x_right > x_left and y_bottom > y_top:
                    intersection = (x_right - x_left) * (y_bottom - y_top)
                    area1 = w1 * h1
                    area2 = w2 * h2
                    union = area1 + area2 - intersection
                    iou = intersection / union if union > 0 else 0
                    
                    if iou > 0.5:  # Duplicate threshold
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique.append((x1, y1, w1, h1, cont1, conf1))
        
        # Return contours and confidences
        return [(cont, conf) for _, _, _, _, cont, conf in unique]
    
    def _rectangles_to_bounding_boxes(self, rectangles: List[Tuple[np.ndarray, float]], 
                                     image_shape: Tuple[int, ...]) -> List[BoundingBox]:
        """
        Convert rectangles to BoundingBox objects.
        
        Args:
            rectangles: List of (contour, confidence) tuples
            image_shape: Shape of the original image
            
        Returns:
            List of BoundingBox objects
        """
        bounding_boxes = []
        
        for contour, base_confidence in rectangles:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Adjust confidence based on aspect ratio
            aspect_ratio = w / h if h > 0 else 0
            aspect_penalty = 1.0
            if aspect_ratio < self.config.aspect_ratio_range[0] or aspect_ratio > self.config.aspect_ratio_range[1]:
                aspect_penalty = 0.8
            
            confidence = base_confidence * aspect_penalty
            
            # Create bounding box
            bbox = BoundingBox(
                x=float(x),
                y=float(y),
                width=float(w),
                height=float(h),
                confidence=confidence,
                label="contour_rectangle"
            )
            
            bounding_boxes.append(bbox)
        
        return bounding_boxes