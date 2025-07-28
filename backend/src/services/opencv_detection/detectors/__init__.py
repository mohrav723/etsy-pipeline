"""
OpenCV detection algorithms for finding suitable regions in mockup templates
"""

from .edge_detector import EdgeBasedDetector
from .contour_detector import ContourBasedDetector
from .color_detector import ColorBasedDetector
from .template_detector import TemplateMatchingDetector
from .fallback_detector import FallbackDetector

__all__ = [
    'EdgeBasedDetector',
    'ContourBasedDetector', 
    'ColorBasedDetector',
    'TemplateMatchingDetector',
    'FallbackDetector'
]