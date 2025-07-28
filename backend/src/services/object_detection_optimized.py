"""
Optimized Object Detection Service for Intelligent Mockup Generation

This module provides optimized object detection functionality with:
- Lower confidence thresholds for better detection
- Expanded target classes for mockup placement
- Better handling of common mockup templates
- Fallback detection for generic rectangular regions
"""

import logging
from typing import List, Dict, Tuple, Optional, Any
import torch
from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

class ObjectDetectionConfig:
    """Configuration class for object detection parameters."""
    
    def __init__(
        self,
        confidence_threshold: float = 0.5,  # Lowered from 0.7 for better detection
        model_name: str = "facebook/detr-resnet-50",
        target_classes: Optional[List[str]] = None,
        max_detections: int = 10,
        enable_fallback: bool = True  # Enable fallback detection
    ):
        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        # Expanded list of target classes for mockup placement
        self.target_classes = target_classes or [
            "picture frame", "painting", "poster", "tv", "monitor", "screen",
            "laptop", "computer", "tablet", "cell phone", "phone", "smartphone",
            "book", "notebook", "magazine", "paper", "card",
            "bottle", "cup", "mug", "bowl", "plate", "dish",
            "shirt", "t-shirt", "clothing", "bag", "backpack",
            "wall", "surface", "board", "sign", "banner",
            "chair", "couch", "bed", "pillow", "cushion"
        ]
        self.max_detections = max_detections
        self.enable_fallback = enable_fallback

class BoundingBox:
    """Represents a detected object's bounding box with metadata."""
    
    def __init__(self, x: float, y: float, width: float, height: float, 
                 confidence: float, label: str):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.confidence = confidence
        self.label = label
    
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

class NoSuitableRegionsError(Exception):
    """Raised when no suitable regions are found for artwork placement."""
    pass

class ObjectDetectionService:
    """Optimized service for detecting objects in mockup template images."""
    
    def __init__(self, config: Optional[ObjectDetectionConfig] = None):
        self.config = config or ObjectDetectionConfig()
        self._processor = None
        self._model = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
    def _load_model(self):
        """Lazy load the DETR model and processor."""
        if self._processor is None or self._model is None:
            logger.info(f"Loading object detection model: {self.config.model_name}")
            try:
                self._processor = DetrImageProcessor.from_pretrained(self.config.model_name)
                self._model = DetrForObjectDetection.from_pretrained(self.config.model_name)
                self._model.to(self._device)
                self._model.eval()
                logger.info(f"Model loaded successfully on device: {self._device}")
            except Exception as e:
                logger.error(f"Failed to load object detection model: {e}")
                raise
    
    def _detect_fallback_regions(self, image: Image.Image) -> List[BoundingBox]:
        """
        Fallback method to detect generic rectangular regions when no objects are found.
        Looks for high-contrast rectangular areas that could be placement targets.
        """
        logger.info("Using fallback detection for generic regions")
        
        # Convert to grayscale for edge detection
        gray = image.convert('L')
        img_array = np.array(gray)
        
        # Simple edge detection using gradient
        from scipy import ndimage
        edges = ndimage.sobel(img_array)
        
        # Find potential rectangular regions (simplified approach)
        height, width = img_array.shape
        regions = []
        
        # Look for central region (common in mockups)
        center_x, center_y = width // 2, height // 2
        
        # Try different region sizes
        for scale in [0.3, 0.4, 0.5]:
            region_width = int(width * scale)
            region_height = int(height * scale)
            
            x = center_x - region_width // 2
            y = center_y - region_height // 2
            
            # Check if this region has good contrast
            region_edges = edges[y:y+region_height, x:x+region_width]
            edge_density = np.mean(region_edges)
            
            if edge_density > 10:  # Threshold for edge density
                bbox = BoundingBox(
                    x=float(x),
                    y=float(y),
                    width=float(region_width),
                    height=float(region_height),
                    confidence=0.6,  # Lower confidence for fallback
                    label=f"generic_region_{scale}"
                )
                regions.append(bbox)
        
        return regions[:3]  # Return top 3 fallback regions
    
    def detect_objects(self, image: Image.Image) -> List[BoundingBox]:
        """
        Detect objects in the given image that are suitable for artwork placement.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            List of BoundingBox objects representing detected regions
            
        Raises:
            Exception: If object detection fails
        """
        try:
            self._load_model()
            
            # Preprocess the image
            inputs = self._processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            # Run inference
            with torch.no_grad():
                outputs = self._model(**inputs)
            
            # Process results with lower threshold
            target_sizes = torch.tensor([image.size[::-1]])  # (height, width)
            results = self._processor.post_process_object_detection(
                outputs, 
                target_sizes=target_sizes, 
                threshold=self.config.confidence_threshold
            )[0]
            
            # Convert to BoundingBox objects
            detected_boxes = []
            for score, label_id, box in zip(
                results["scores"], 
                results["labels"], 
                results["boxes"]
            ):
                if len(detected_boxes) >= self.config.max_detections:
                    break
                    
                # Convert label ID to label name
                label = self._model.config.id2label[label_id.item()]
                
                # More flexible class matching
                label_lower = label.lower()
                is_target = False
                
                # Check if any target class is a substring of the detected label
                for target in [tc.lower() for tc in self.config.target_classes]:
                    if target in label_lower or label_lower in target:
                        is_target = True
                        break
                
                # Also accept generic objects that could hold artwork
                generic_targets = ["object", "thing", "item", "surface", "area"]
                if not is_target and any(gt in label_lower for gt in generic_targets):
                    is_target = True
                
                if not is_target and self.config.target_classes:
                    continue
                
                # Convert box coordinates
                center_x, center_y, width, height = box.tolist()
                x = center_x - width / 2
                y = center_y - height / 2
                
                bbox = BoundingBox(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    confidence=score.item(),
                    label=label
                )
                detected_boxes.append(bbox)
            
            # If no objects detected and fallback is enabled, try fallback detection
            if not detected_boxes and self.config.enable_fallback:
                logger.warning("No objects detected with model, trying fallback detection")
                detected_boxes = self._detect_fallback_regions(image)
            
            logger.info(f"Detected {len(detected_boxes)} suitable objects/regions")
            return detected_boxes
            
        except Exception as e:
            logger.error(f"Error during object detection: {e}")
            # If model fails completely, try fallback
            if self.config.enable_fallback:
                try:
                    return self._detect_fallback_regions(image)
                except Exception as fallback_error:
                    logger.error(f"Fallback detection also failed: {fallback_error}")
            raise
    
    def find_suitable_regions(self, mockup_image: Image.Image) -> List[BoundingBox]:
        """
        Find suitable regions in the mockup template for placing artwork.
        
        Args:
            mockup_image: The mockup template image
            
        Returns:
            List of suitable BoundingBox regions sorted by confidence
            
        Raises:
            NoSuitableRegionsError: If no suitable regions are found
        """
        detected_boxes = self.detect_objects(mockup_image)
        
        if not detected_boxes:
            raise NoSuitableRegionsError("No suitable regions detected in the mockup template")
        
        # Sort by confidence score
        detected_boxes.sort(key=lambda box: box.confidence, reverse=True)
        
        # Log detected regions
        for box in detected_boxes[:5]:  # Log top 5
            logger.info(
                f"Found region: {box.label} at ({box.x:.1f}, {box.y:.1f}) "
                f"size {box.width:.1f}x{box.height:.1f} confidence {box.confidence:.3f}"
            )
        
        return detected_boxes

def create_mock_detection_service() -> ObjectDetectionService:
    """Create a mock detection service for testing that doesn't require ML models."""
    
    class MockDetectionService(ObjectDetectionService):
        def _load_model(self):
            # Don't load any models
            pass
            
        def detect_objects(self, image: Image.Image) -> List[BoundingBox]:
            # Return a mock bounding box in the center of the image
            width, height = image.size
            box_width = width * 0.4
            box_height = height * 0.4
            x = (width - box_width) / 2
            y = (height - box_height) / 2
            
            return [BoundingBox(
                x=x, y=y, width=box_width, height=box_height,
                confidence=0.95, label="mock_frame"
            )]
    
    return MockDetectionService()