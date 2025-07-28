"""
Configuration for OpenCV-based object detection
"""

from typing import Tuple, Optional, List
from dataclasses import dataclass, field


@dataclass
class OpenCVObjectDetectionConfig:
    """Configuration class for OpenCV-based object detection parameters."""
    
    # Edge detection parameters
    canny_low_threshold: int = 50
    canny_high_threshold: int = 150
    gaussian_blur_kernel: Tuple[int, int] = (5, 5)
    
    # Contour detection parameters
    min_contour_area: int = 1000  # Minimum contour area in pixels
    contour_approximation_epsilon: float = 0.02  # Epsilon for polygon approximation
    
    # Region filtering parameters
    min_area_ratio: float = 0.01  # Minimum region area as ratio of image area (1%)
    max_area_ratio: float = 0.8   # Maximum region area as ratio of image area (80%)
    aspect_ratio_range: Tuple[float, float] = (0.3, 3.0)  # Min and max aspect ratios
    
    # Color detection parameters
    color_threshold: int = 30  # Threshold for color uniformity
    min_color_region_size: int = 5000  # Minimum size for color-based regions
    
    # Template matching parameters
    template_match_threshold: float = 0.7  # Minimum correlation for template match
    template_scales: List[float] = field(default_factory=lambda: [0.5, 0.75, 1.0, 1.25, 1.5])
    
    # General detection parameters
    confidence_threshold: float = 0.5  # Minimum confidence for detections
    max_detections: int = 10  # Maximum number of regions to return
    enable_fallback: bool = True  # Enable fallback detection
    
    # Performance parameters
    enable_parallel_detection: bool = True  # Run detectors in parallel
    detection_timeout: float = 5.0  # Timeout for each detector in seconds
    max_image_dimension: int = 4096  # Maximum image dimension to process
    parallel_processing: bool = True  # Alias for enable_parallel_detection
    detector_timeout: float = 5.0  # Timeout for individual detectors
    
    # Scoring weights for region ranking
    size_weight: float = 0.3  # Weight for region size in scoring
    position_weight: float = 0.2  # Weight for central position
    confidence_weight: float = 0.5  # Weight for detection confidence
    
    # Additional parameters for service
    enabled_detectors: List[str] = field(default_factory=lambda: ['edge', 'contour', 'color', 'template', 'fallback'])
    merge_iou_threshold: float = 0.3  # IoU threshold for merging overlapping regions
    min_region_area_ratio: float = 0.01  # Minimum region area as ratio of image area
    scoring_weights: dict = field(default_factory=lambda: {
        'confidence': 0.3,
        'size': 0.25,
        'aspect_ratio': 0.15,
        'position': 0.2,
        'edge_distance': 0.1
    })
    
    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.canny_low_threshold >= self.canny_high_threshold:
            raise ValueError("Canny low threshold must be less than high threshold")
        
        if self.min_area_ratio >= self.max_area_ratio:
            raise ValueError("Min area ratio must be less than max area ratio")
        
        if self.aspect_ratio_range[0] >= self.aspect_ratio_range[1]:
            raise ValueError("Min aspect ratio must be less than max aspect ratio")
        
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("Confidence threshold must be between 0 and 1")
        
        if self.max_detections < 1:
            raise ValueError("Max detections must be at least 1")
        
        if not all(0 < scale <= 2.0 for scale in self.template_scales):
            raise ValueError("Template scales must be between 0 and 2.0")
        
        # Validate scoring weights
        if self.scoring_weights:
            weights_sum = sum(self.scoring_weights.values())
            if abs(weights_sum - 1.0) > 0.001:
                raise ValueError(f"Scoring weights must sum to 1.0, got {weights_sum}")
        
        # Validate enabled detectors
        valid_detectors = {'edge', 'contour', 'color', 'template', 'fallback'}
        for detector in self.enabled_detectors:
            if detector not in valid_detectors:
                raise ValueError(f"Invalid detector: {detector}. Must be one of {valid_detectors}")
    
    @classmethod
    def for_high_quality(cls) -> 'OpenCVObjectDetectionConfig':
        """Create configuration optimized for high quality detection."""
        return cls(
            canny_low_threshold=30,
            canny_high_threshold=100,
            confidence_threshold=0.7,
            min_area_ratio=0.02,
            max_area_ratio=0.7,
            enable_parallel_detection=True
        )
    
    @classmethod
    def for_fast_detection(cls) -> 'OpenCVObjectDetectionConfig':
        """Create configuration optimized for speed."""
        return cls(
            canny_low_threshold=70,
            canny_high_threshold=170,
            confidence_threshold=0.4,
            template_scales=[0.75, 1.0, 1.25],
            enable_parallel_detection=False,
            detection_timeout=2.0
        )
    
    @classmethod
    def for_mockup_templates(cls) -> 'OpenCVObjectDetectionConfig':
        """Create configuration optimized for mockup template detection."""
        return cls(
            # Mockups often have clear edges
            canny_low_threshold=40,
            canny_high_threshold=120,
            
            # Mockups usually have rectangular regions
            min_area_ratio=0.05,  # At least 5% of image
            max_area_ratio=0.6,   # At most 60% of image
            aspect_ratio_range=(0.5, 2.0),  # More restrictive aspect ratio
            
            # Higher confidence for mockups
            confidence_threshold=0.6,
            
            # Mockups benefit from multiple scales
            template_scales=[0.6, 0.8, 1.0, 1.2, 1.4],
            
            # Prioritize position and size for mockups
            size_weight=0.4,
            position_weight=0.3,
            confidence_weight=0.3
        )