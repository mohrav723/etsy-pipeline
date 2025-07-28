"""
Main OpenCV Object Detection Service

This service orchestrates multiple computer vision detection algorithms
to find suitable regions for artwork placement in mockup templates.
"""

import logging
import time
from typing import List, Dict, Optional, Any, Tuple
from PIL import Image
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .config import OpenCVObjectDetectionConfig
from .base import BaseDetector, BoundingBox
from .utils import pil_to_cv2, validate_image
from .detectors import (
    EdgeBasedDetector,
    ContourBasedDetector,
    ColorBasedDetector,
    TemplateMatchingDetector,
    FallbackDetector
)
from .performance_monitor import get_performance_monitor

logger = logging.getLogger(__name__)

class OpenCVObjectDetectionService:
    """
    Main service class that orchestrates multiple OpenCV detection algorithms
    to find suitable regions for artwork placement.
    """
    
    def __init__(self, config: Optional[OpenCVObjectDetectionConfig] = None):
        """Initialize the service with configuration."""
        self.config = config or OpenCVObjectDetectionConfig()
        self._detectors: Dict[str, BaseDetector] = {}
        self._lock = threading.Lock()
        self._executor = None
        self._initialize_detectors()
        
    def _initialize_detectors(self) -> None:
        """Initialize all detection algorithms based on configuration."""
        detector_classes = {
            'edge': EdgeBasedDetector,
            'contour': ContourBasedDetector,
            'color': ColorBasedDetector,
            'template': TemplateMatchingDetector,
            'fallback': FallbackDetector
        }
        
        for name, detector_class in detector_classes.items():
            if name in self.config.enabled_detectors:
                try:
                    self._detectors[name] = detector_class(self.config)
                    logger.info(f"Initialized {name} detector")
                except Exception as e:
                    logger.error(f"Failed to initialize {name} detector: {e}")
                    
    def detect_objects(self, image: Image.Image, job_id: Optional[str] = None) -> List[BoundingBox]:
        """
        Detect objects in the given image using all enabled detectors.
        
        Args:
            image: PIL Image to analyze
            job_id: Optional job identifier for metrics
            
        Returns:
            List of BoundingBox objects representing detected regions
            
        Raises:
            ValueError: If image is invalid
            Exception: If all detectors fail
        """
        # Validate input image first
        if not validate_image(image):
            raise ValueError("Invalid image provided")
            
        monitor = get_performance_monitor()
        
        with monitor.measure_detection(job_id=job_id, image_size=image.size):
            # Convert image for OpenCV processing
            with monitor.measure_phase('preprocessing'):
                cv_image = pil_to_cv2(image)
            
            # Run detectors in parallel if enabled
            all_detections = []
            
            if self.config.parallel_processing and len(self._detectors) > 1:
                all_detections = self._run_detectors_parallel(cv_image)
            else:
                all_detections = self._run_detectors_sequential(cv_image)
                
            # Merge and rank detections
            with monitor.measure_phase('merging'):
                merged_detections = self._merge_overlapping_regions(all_detections)
                
            with monitor.measure_phase('ranking'):
                ranked_detections = self._rank_regions(merged_detections, image.size)
            
            # Apply max detections limit
            final_detections = ranked_detections[:self.config.max_detections]
            
            # Record metrics
            monitor.record_regions_detected(len(final_detections))
            
            return final_detections
        
    def _run_detectors_sequential(self, cv_image: np.ndarray) -> List[BoundingBox]:
        """Run all detectors sequentially."""
        all_detections = []
        monitor = get_performance_monitor()
        
        for name, detector in self._detectors.items():
            try:
                with monitor.measure_phase(f'{name}_detector'):
                    detections = detector.detect(cv_image)
                
                logger.debug(f"{name} detector found {len(detections)} regions")
                all_detections.extend(detections)
                
                # Early termination if we have enough high-confidence detections
                high_conf_count = sum(1 for d in all_detections if d.confidence > 0.8)
                if high_conf_count >= self.config.max_detections * 2:
                    logger.debug("Early termination: sufficient high-confidence detections")
                    break
                    
            except Exception as e:
                logger.error(f"{name} detector failed: {e}")
                
        return all_detections
        
    def _run_detectors_parallel(self, cv_image: np.ndarray) -> List[BoundingBox]:
        """Run all detectors in parallel using ThreadPoolExecutor."""
        all_detections = []
        
        with ThreadPoolExecutor(max_workers=len(self._detectors)) as executor:
            future_to_detector = {
                executor.submit(detector.detect, cv_image): name
                for name, detector in self._detectors.items()
            }
            
            for future in as_completed(future_to_detector):
                detector_name = future_to_detector[future]
                try:
                    detections = future.result(timeout=self.config.detector_timeout)
                    logger.debug(f"{detector_name} detector found {len(detections)} regions")
                    all_detections.extend(detections)
                except Exception as e:
                    logger.error(f"{detector_name} detector failed: {e}")
                    
        return all_detections
        
    def _merge_overlapping_regions(self, detections: List[BoundingBox]) -> List[BoundingBox]:
        """Merge overlapping detections based on IoU threshold."""
        if not detections:
            return []
            
        # Sort by confidence (highest first)
        sorted_detections = sorted(detections, key=lambda x: x.confidence, reverse=True)
        merged = []
        
        for detection in sorted_detections:
            should_merge = False
            
            for i, existing in enumerate(merged):
                iou = self._calculate_iou(detection, existing)
                if iou > self.config.merge_iou_threshold:
                    # Merge with existing detection
                    merged[i] = self._merge_boxes(existing, detection)
                    should_merge = True
                    break
                    
            if not should_merge:
                merged.append(detection)
                
        return merged
        
    def _calculate_iou(self, box1: BoundingBox, box2: BoundingBox) -> float:
        """Calculate Intersection over Union for two bounding boxes."""
        # Calculate intersection area
        x1 = max(box1.x, box2.x)
        y1 = max(box1.y, box2.y)
        x2 = min(box1.x + box1.width, box2.x + box2.width)
        y2 = min(box1.y + box1.height, box2.y + box2.height)
        
        if x2 < x1 or y2 < y1:
            return 0.0
            
        intersection = (x2 - x1) * (y2 - y1)
        
        # Calculate union area
        area1 = box1.width * box1.height
        area2 = box2.width * box2.height
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
        
    def _merge_boxes(self, box1: BoundingBox, box2: BoundingBox) -> BoundingBox:
        """Merge two bounding boxes, keeping the higher confidence."""
        # Calculate merged coordinates
        x1 = min(box1.x, box2.x)
        y1 = min(box1.y, box2.y)
        x2 = max(box1.x + box1.width, box2.x + box2.width)
        y2 = max(box1.y + box1.height, box2.y + box2.height)
        
        # Use weighted average confidence
        total_area = box1.width * box1.height + box2.width * box2.height
        weight1 = (box1.width * box1.height) / total_area
        weight2 = (box2.width * box2.height) / total_area
        merged_confidence = box1.confidence * weight1 + box2.confidence * weight2
        
        # Keep the label from the higher confidence detection
        label = box1.label if box1.confidence > box2.confidence else box2.label
        
        return BoundingBox(
            x=x1,
            y=y1,
            width=x2 - x1,
            height=y2 - y1,
            confidence=merged_confidence,
            label=label
        )
        
    def _rank_regions(self, detections: List[BoundingBox], image_size: Tuple[int, int]) -> List[BoundingBox]:
        """Rank detected regions by suitability for artwork placement."""
        if not detections:
            return []
            
        image_width, image_height = image_size
        image_area = image_width * image_height
        
        scored_detections = []
        
        for detection in detections:
            score = 0.0
            
            # Confidence score (0-1)
            score += detection.confidence * self.config.scoring_weights['confidence']
            
            # Size score (prefer regions that are 10-50% of image area)
            region_area = detection.width * detection.height
            area_ratio = region_area / image_area
            if 0.1 <= area_ratio <= 0.5:
                size_score = 1.0
            elif area_ratio < 0.1:
                size_score = area_ratio / 0.1
            else:
                size_score = max(0, 1.0 - (area_ratio - 0.5) / 0.5)
            score += size_score * self.config.scoring_weights['size']
            
            # Aspect ratio score (prefer ratios close to golden ratio or common photo ratios)
            aspect_ratio = detection.width / detection.height if detection.height > 0 else 0
            ideal_ratios = [1.618, 1.5, 1.333, 1.0, 0.75, 0.667]  # Golden ratio, 3:2, 4:3, 1:1, 3:4, 2:3
            ratio_diffs = [abs(aspect_ratio - ideal) for ideal in ideal_ratios]
            min_diff = min(ratio_diffs) if ratio_diffs else 1.0
            aspect_score = max(0, 1.0 - min_diff / 2.0)
            score += aspect_score * self.config.scoring_weights['aspect_ratio']
            
            # Position score (prefer centered regions)
            center_x = detection.x + detection.width / 2
            center_y = detection.y + detection.height / 2
            x_offset = abs(center_x - image_width / 2) / (image_width / 2)
            y_offset = abs(center_y - image_height / 2) / (image_height / 2)
            position_score = 1.0 - (x_offset + y_offset) / 2
            score += position_score * self.config.scoring_weights['position']
            
            # Edge distance score (prefer regions not touching edges)
            edge_margin = min(
                detection.x,
                detection.y,
                image_width - (detection.x + detection.width),
                image_height - (detection.y + detection.height)
            )
            edge_score = min(1.0, edge_margin / (min(image_width, image_height) * 0.1))
            score += edge_score * self.config.scoring_weights['edge_distance']
            
            # Store score for sorting
            scored_detections.append((score, detection))
            
        # Sort by score (highest first)
        scored_detections.sort(key=lambda x: x[0], reverse=True)
        
        # Return sorted detections
        return [detection for _, detection in scored_detections]
        
    def find_suitable_regions(self, image: Image.Image, job_id: Optional[str] = None) -> List[BoundingBox]:
        """
        Find regions in the image that are suitable for artwork placement.
        
        This is the main interface matching the original ObjectDetectionService.
        
        Args:
            image: PIL Image of the mockup template
            job_id: Optional job identifier for metrics
            
        Returns:
            List of BoundingBox objects representing suitable regions
            
        Raises:
            NoSuitableRegionsError: If no suitable regions are found
            ObjectDetectionError: If detection fails
        """
        try:
            detected_regions = self.detect_objects(image, job_id=job_id)
            
            if not detected_regions:
                # Use fallback detector if enabled and no regions found
                if self.config.enable_fallback:
                    if 'fallback' not in self._detectors:
                        self._detectors['fallback'] = FallbackDetector(self.config)
                        
                    cv_image = pil_to_cv2(image)
                    fallback_regions = self._detectors['fallback'].detect(cv_image)
                    
                    if not fallback_regions:
                        raise NoSuitableRegionsError("No suitable regions detected in the mockup template")
                        
                    detected_regions = fallback_regions
                else:
                    raise NoSuitableRegionsError("No suitable regions detected in the mockup template")
                
            # Apply minimum area filter
            min_area = (image.width * image.height) * self.config.min_region_area_ratio
            suitable_regions = [
                region for region in detected_regions
                if (region.width * region.height) >= min_area
            ]
            
            if not suitable_regions:
                raise NoSuitableRegionsError(
                    f"Detected {len(detected_regions)} regions but none are large enough for artwork placement"
                )
                
            logger.info(f"Found {len(suitable_regions)} suitable regions for artwork placement")
            return suitable_regions
            
        except NoSuitableRegionsError:
            raise
        except Exception as e:
            raise ObjectDetectionError(f"Failed to find suitable regions: {e}")
            
    def cleanup(self) -> None:
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
            

# Exception classes for compatibility with existing system
class ObjectDetectionError(Exception):
    """Base exception for object detection errors."""
    pass

class NoSuitableRegionsError(ObjectDetectionError):
    """Raised when no suitable regions are found for artwork placement."""
    pass