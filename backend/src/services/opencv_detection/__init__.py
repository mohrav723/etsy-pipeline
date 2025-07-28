"""
OpenCV-based Object Detection Service

This package provides computer vision-based object detection for intelligent mockup generation,
replacing the previous DETR (AI-based) implementation with more reliable OpenCV algorithms.
"""

from .config import OpenCVObjectDetectionConfig
from .base import BaseDetector, BoundingBox

# OpenCVObjectDetectionService will be imported once implemented
__all__ = [
    'OpenCVObjectDetectionConfig',
    'BaseDetector',
    'BoundingBox'
]