"""
Object Detection Service for Intelligent Mockup Generation

This module provides object detection functionality to identify suitable regions
in mockup templates where artwork should be placed using pre-trained models.
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
        confidence_threshold: float = 0.7,
        model_name: str = "facebook/detr-resnet-50",
        target_classes: Optional[List[str]] = None,
        max_detections: int = 10
    ):
        self.confidence_threshold = confidence_threshold
        self.model_name = model_name
        self.target_classes = target_classes or [
            "picture frame", "tv", "laptop", "cell phone", "book",
            "bottle", "cup", "bowl", "chair", "couch", "bed"
        ]
        self.max_detections = max_detections

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

class ObjectDetectionService:
    """Service for detecting objects in mockup template images."""
    
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
            
            # Process results
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
                
                # Filter for target classes (if specified)
                if self.config.target_classes and not any(
                    target in label.lower() for target in 
                    [tc.lower() for tc in self.config.target_classes]
                ):
                    continue
                
                # Convert box coordinates (center_x, center_y, width, height) to (x, y, width, height)
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
            
            logger.info(f"Detected {len(detected_boxes)} suitable objects")
            return detected_boxes
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            raise
    
    def find_suitable_regions(self, image: Image.Image) -> List[BoundingBox]:
        """
        Find regions in the image that are suitable for artwork placement.
        
        This is the main interface for the intelligent mockup generation workflow.
        
        Args:
            image: PIL Image of the mockup template
            
        Returns:
            List of BoundingBox objects representing suitable regions
            
        Raises:
            NoSuitableRegionsError: If no suitable regions are found
            ObjectDetectionError: If detection fails
        """
        try:
            detected_objects = self.detect_objects(image)
            
            if not detected_objects:
                raise NoSuitableRegionsError("No suitable regions detected in the mockup template")
            
            # Sort by confidence score (highest first)
            detected_objects.sort(key=lambda x: x.confidence, reverse=True)
            
            # Filter for regions that are large enough to be useful
            min_area = (image.width * image.height) * 0.01  # At least 1% of image area
            suitable_regions = [
                obj for obj in detected_objects 
                if (obj.width * obj.height) >= min_area
            ]
            
            if not suitable_regions:
                raise NoSuitableRegionsError(
                    f"Detected {len(detected_objects)} objects but none are large enough for artwork placement"
                )
            
            logger.info(f"Found {len(suitable_regions)} suitable regions for artwork placement")
            return suitable_regions
            
        except NoSuitableRegionsError:
            raise
        except Exception as e:
            raise ObjectDetectionError(f"Failed to find suitable regions: {e}")

class ObjectDetectionError(Exception):
    """Base exception for object detection errors."""
    pass

class NoSuitableRegionsError(ObjectDetectionError):
    """Raised when no suitable regions are found for artwork placement."""
    pass

def create_mock_detection_service() -> 'MockObjectDetectionService':
    """
    Create a mock object detection service for testing purposes.
    
    Returns:
        MockObjectDetectionService instance
    """
    return MockObjectDetectionService()

class MockObjectDetectionService:
    """Mock implementation of ObjectDetectionService for testing."""
    
    def __init__(self):
        self.config = ObjectDetectionConfig()
    
    def detect_objects(self, image: Image.Image) -> List[BoundingBox]:
        """Mock object detection that returns predictable results."""
        # Return mock detections based on image size
        width, height = image.size
        
        mock_detections = [
            BoundingBox(
                x=width * 0.2,
                y=height * 0.2,
                width=width * 0.3,
                height=height * 0.4,
                confidence=0.85,
                label="picture frame"
            ),
            BoundingBox(
                x=width * 0.6,
                y=height * 0.1,
                width=width * 0.25,
                height=height * 0.3,
                confidence=0.75,
                label="laptop"
            )
        ]
        
        return mock_detections
    
    def find_suitable_regions(self, image: Image.Image) -> List[BoundingBox]:
        """Mock implementation of find_suitable_regions."""
        return self.detect_objects(image)