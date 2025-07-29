"""
Compatibility wrapper for seamless migration between DETR and OpenCV detection services.

This module provides a wrapper that maintains the exact interface of the original
ObjectDetectionService while allowing configuration-based switching to OpenCV.
"""

import logging
from typing import List, Optional, Dict, Any
from PIL import Image

# Import original DETR-based service classes
from ..object_detection import (
    ObjectDetectionConfig as DETRConfig,
    BoundingBox as DETRBoundingBox,
    ObjectDetectionError as DETRObjectDetectionError,
    NoSuitableRegionsError as DETRNoSuitableRegionsError
)

# Import OpenCV-based service classes
from .opencv_detection_service import (
    OpenCVObjectDetectionService,
    ObjectDetectionError as OpenCVObjectDetectionError,
    NoSuitableRegionsError as OpenCVNoSuitableRegionsError
)
from .config import OpenCVObjectDetectionConfig
from .base import BoundingBox as OpenCVBoundingBox

logger = logging.getLogger(__name__)


class ObjectDetectionCompatibilityWrapper:
    """
    Wrapper class that provides the exact same interface as ObjectDetectionService
    but can use either DETR or OpenCV backend based on configuration.
    """
    
    def __init__(self, config: Optional[DETRConfig] = None, use_opencv: bool = False):
        """
        Initialize the compatibility wrapper.
        
        Args:
            config: ObjectDetectionConfig instance (DETR format)
            use_opencv: If True, use OpenCV backend; otherwise use DETR
        """
        self.use_opencv = use_opencv
        self.detr_config = config or DETRConfig()
        
        if use_opencv:
            # Convert DETR config to OpenCV config
            self.opencv_config = self._convert_config(self.detr_config)
            self._service = OpenCVObjectDetectionService(self.opencv_config)
            logger.info("Using OpenCV-based object detection service")
        else:
            # Import and use original DETR service
            from ..object_detection import ObjectDetectionService as DETRService
            self._service = DETRService(self.detr_config)
            logger.info("Using DETR-based object detection service")
            
    def _convert_config(self, detr_config: DETRConfig) -> OpenCVObjectDetectionConfig:
        """Convert DETR config to OpenCV config format."""
        opencv_config = OpenCVObjectDetectionConfig(
            confidence_threshold=detr_config.confidence_threshold,
            max_detections=detr_config.max_detections,
            # Map DETR target classes to enable specific detectors
            enabled_detectors=self._get_enabled_detectors(detr_config.target_classes)
        )
        
        # Apply optimized settings for mockup detection
        if "picture frame" in detr_config.target_classes:
            opencv_config = OpenCVObjectDetectionConfig.for_mockup_templates()
            opencv_config.confidence_threshold = detr_config.confidence_threshold
            opencv_config.max_detections = detr_config.max_detections
            
        return opencv_config
        
    def _get_enabled_detectors(self, target_classes: List[str]) -> List[str]:
        """Determine which OpenCV detectors to enable based on target classes."""
        detectors = ['edge', 'contour']  # Always use these base detectors
        
        # Add specific detectors based on target classes
        if any(cls in ["picture frame", "tv", "laptop"] for cls in target_classes):
            detectors.append('template')
            
        if any(cls in ["bottle", "cup", "bowl"] for cls in target_classes):
            detectors.append('color')
            
        detectors.append('fallback')  # Always include fallback
        return detectors
        
    def _convert_bounding_box(self, box: OpenCVBoundingBox) -> DETRBoundingBox:
        """Convert OpenCV BoundingBox to DETR BoundingBox format."""
        return DETRBoundingBox(
            x=box.x,
            y=box.y,
            width=box.width,
            height=box.height,
            confidence=box.confidence,
            label=box.label
        )
        
    def detect_objects(self, image: Image.Image) -> List[DETRBoundingBox]:
        """
        Detect objects in the given image.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            List of BoundingBox objects (DETR format) representing detected regions
            
        Raises:
            Exception: If object detection fails
        """
        try:
            if self.use_opencv:
                # Get OpenCV results and convert to DETR format
                opencv_boxes = self._service.detect_objects(image)
                return [self._convert_bounding_box(box) for box in opencv_boxes]
            else:
                # Use DETR service directly
                return self._service.detect_objects(image)
                
        except (OpenCVObjectDetectionError, DETRObjectDetectionError) as e:
            # Re-raise as DETR error for compatibility
            raise DETRObjectDetectionError(str(e))
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            raise
            
    def find_suitable_regions(self, image: Image.Image) -> List[DETRBoundingBox]:
        """
        Find regions in the image that are suitable for artwork placement.
        
        Args:
            image: PIL Image of the mockup template
            
        Returns:
            List of BoundingBox objects (DETR format) representing suitable regions
            
        Raises:
            NoSuitableRegionsError: If no suitable regions are found
            ObjectDetectionError: If detection fails
        """
        try:
            if self.use_opencv:
                # Get OpenCV results and convert to DETR format
                opencv_boxes = self._service.find_suitable_regions(image)
                return [self._convert_bounding_box(box) for box in opencv_boxes]
            else:
                # Use DETR service directly
                return self._service.find_suitable_regions(image)
                
        except OpenCVNoSuitableRegionsError as e:
            # Re-raise as DETR error for compatibility
            raise DETRNoSuitableRegionsError(str(e))
        except OpenCVObjectDetectionError as e:
            # Re-raise as DETR error for compatibility
            raise DETRObjectDetectionError(str(e))
        except (DETRNoSuitableRegionsError, DETRObjectDetectionError):
            # DETR errors pass through
            raise
        except Exception as e:
            raise DETRObjectDetectionError(f"Failed to find suitable regions: {e}")
            
    @property
    def config(self) -> DETRConfig:
        """Get the configuration (always returns DETR format for compatibility)."""
        return self.detr_config
        

def create_object_detection_service(
    config: Optional[DETRConfig] = None,
    use_opencv: Optional[bool] = None,
    job_id: Optional[str] = None
) -> ObjectDetectionCompatibilityWrapper:
    """
    Factory function to create an object detection service.
    
    Args:
        config: ObjectDetectionConfig instance
        use_opencv: If True, use OpenCV; if False, use DETR; if None, check feature flag
        job_id: Optional job ID for feature flag evaluation
        
    Returns:
        ObjectDetectionCompatibilityWrapper instance
    """
    if use_opencv is None:
        # Check feature flag
        from ..feature_flags import should_use_opencv_detection
        use_opencv = should_use_opencv_detection(job_id)
        
    return ObjectDetectionCompatibilityWrapper(config, use_opencv)