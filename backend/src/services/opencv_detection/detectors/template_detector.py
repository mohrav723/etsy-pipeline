"""
Template matching detector for finding common mockup patterns
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
import logging
import os

from ..base import BaseDetector, BoundingBox
from ..config import OpenCVObjectDetectionConfig

logger = logging.getLogger(__name__)


class TemplateMatchingDetector(BaseDetector):
    """
    Detects regions using template matching for common mockup patterns.
    
    This detector looks for common patterns like frames, screens, and surfaces
    that frequently appear in mockup templates.
    """
    
    def __init__(self, config: OpenCVObjectDetectionConfig):
        super().__init__(config)
        self.templates = self._load_or_generate_templates()
    
    def detect(self, image: np.ndarray) -> List[BoundingBox]:
        """
        Detect regions using template matching.
        
        Args:
            image: OpenCV image (BGR format)
            
        Returns:
            List of detected BoundingBox regions
        """
        try:
            logger.debug(f"{self.name}: Starting template matching detection")
            
            # Convert to grayscale for matching
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Apply template matching at multiple scales
            all_matches = []
            for template_name, template in self.templates.items():
                matches = self._match_template_multiscale(gray, template, template_name)
                all_matches.extend(matches)
            
            # Remove overlapping matches
            unique_matches = self._remove_overlapping_matches(all_matches)
            
            # Convert to bounding boxes
            bounding_boxes = self._matches_to_bounding_boxes(unique_matches)
            
            # Filter regions
            filtered_boxes = self.filter_regions(bounding_boxes, image.shape)
            
            logger.info(f"{self.name}: Detected {len(filtered_boxes)} template matches")
            return filtered_boxes
            
        except Exception as e:
            logger.error(f"{self.name}: Detection failed - {e}")
            return []
    
    def _load_or_generate_templates(self) -> Dict[str, np.ndarray]:
        """
        Load pre-defined templates or generate synthetic ones.
        
        Returns:
            Dictionary of template name to template image
        """
        templates = {}
        
        # Generate synthetic templates for common mockup elements
        
        # 1. Picture frame template (rectangular border)
        frame_template = self._generate_frame_template()
        templates['frame'] = frame_template
        
        # 2. Screen/monitor template (rectangular with thin border)
        screen_template = self._generate_screen_template()
        templates['screen'] = screen_template
        
        # 3. Device template (rounded rectangle)
        device_template = self._generate_device_template()
        templates['device'] = device_template
        
        # 4. Paper/card template (simple rectangle)
        paper_template = self._generate_paper_template()
        templates['paper'] = paper_template
        
        # 5. Surface template (textured rectangle)
        surface_template = self._generate_surface_template()
        templates['surface'] = surface_template
        
        logger.info(f"Generated {len(templates)} synthetic templates")
        return templates
    
    def _generate_frame_template(self, size: int = 100) -> np.ndarray:
        """Generate a picture frame template."""
        template = np.ones((size, size), dtype=np.uint8) * 255
        
        # Draw frame border
        border_width = size // 10
        cv2.rectangle(template, (0, 0), (size-1, size-1), 0, border_width)
        
        # Add inner border for depth
        inner_border = border_width + size // 20
        cv2.rectangle(template, 
                     (inner_border, inner_border), 
                     (size-inner_border-1, size-inner_border-1), 
                     128, 2)
        
        return template
    
    def _generate_screen_template(self, size: int = 100) -> np.ndarray:
        """Generate a screen/monitor template."""
        template = np.ones((size, size), dtype=np.uint8) * 200
        
        # Thin dark border
        cv2.rectangle(template, (0, 0), (size-1, size-1), 0, 2)
        
        # Inner bright area (screen)
        margin = size // 20
        cv2.rectangle(template, 
                     (margin, margin), 
                     (size-margin-1, size-margin-1), 
                     255, -1)
        
        return template
    
    def _generate_device_template(self, size: int = 100) -> np.ndarray:
        """Generate a device (phone/tablet) template."""
        template = np.ones((size, size), dtype=np.uint8) * 255
        
        # Rounded rectangle for device body
        radius = size // 10
        cv2.rectangle(template, (radius, 0), (size-radius-1, size-1), 50, -1)
        cv2.rectangle(template, (0, radius), (size-1, size-radius-1), 50, -1)
        cv2.circle(template, (radius, radius), radius, 50, -1)
        cv2.circle(template, (size-radius-1, radius), radius, 50, -1)
        cv2.circle(template, (radius, size-radius-1), radius, 50, -1)
        cv2.circle(template, (size-radius-1, size-radius-1), radius, 50, -1)
        
        # Screen area
        margin = size // 8
        cv2.rectangle(template, 
                     (margin, margin), 
                     (size-margin-1, size-margin-1), 
                     200, -1)
        
        return template
    
    def _generate_paper_template(self, size: int = 100) -> np.ndarray:
        """Generate a paper/card template."""
        template = np.ones((size, size), dtype=np.uint8) * 240
        
        # Simple rectangle with slight shadow effect
        cv2.rectangle(template, (2, 2), (size-1, size-1), 180, -1)
        cv2.rectangle(template, (0, 0), (size-3, size-3), 255, -1)
        
        return template
    
    def _generate_surface_template(self, size: int = 100) -> np.ndarray:
        """Generate a textured surface template."""
        template = np.ones((size, size), dtype=np.uint8) * 200
        
        # Add some texture
        noise = np.random.randint(180, 220, (size, size), dtype=np.uint8)
        template = cv2.addWeighted(template, 0.7, noise, 0.3, 0)
        
        # Add gradient for depth
        for i in range(size):
            template[i, :] = template[i, :] * (0.8 + 0.2 * i / size)
        
        return template.astype(np.uint8)
    
    def _match_template_multiscale(self, image: np.ndarray, template: np.ndarray, 
                                   template_name: str) -> List[Dict]:
        """
        Match template at multiple scales.
        
        Args:
            image: Grayscale image to search in
            template: Template to match
            template_name: Name of the template
            
        Returns:
            List of match dictionaries
        """
        matches = []
        
        for scale in self.config.template_scales:
            # Resize template
            scaled_width = int(template.shape[1] * scale)
            scaled_height = int(template.shape[0] * scale)
            
            if scaled_width > image.shape[1] or scaled_height > image.shape[0]:
                continue
            
            scaled_template = cv2.resize(template, (scaled_width, scaled_height))
            
            # Apply template matching
            result = cv2.matchTemplate(image, scaled_template, cv2.TM_CCOEFF_NORMED)
            
            # Find locations where match exceeds threshold
            locations = np.where(result >= self.config.template_match_threshold)
            
            for pt in zip(*locations[::-1]):
                match = {
                    'x': pt[0],
                    'y': pt[1],
                    'width': scaled_width,
                    'height': scaled_height,
                    'confidence': result[pt[1], pt[0]],
                    'template': template_name,
                    'scale': scale
                }
                matches.append(match)
        
        return matches
    
    def _remove_overlapping_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Remove overlapping template matches using non-maximum suppression.
        
        Args:
            matches: List of match dictionaries
            
        Returns:
            List of non-overlapping matches
        """
        if not matches:
            return []
        
        # Sort by confidence
        matches = sorted(matches, key=lambda x: x['confidence'], reverse=True)
        
        # Non-maximum suppression
        keep = []
        for i, match1 in enumerate(matches):
            should_keep = True
            
            for match2 in keep:
                # Calculate IoU
                x1 = max(match1['x'], match2['x'])
                y1 = max(match1['y'], match2['y'])
                x2 = min(match1['x'] + match1['width'], match2['x'] + match2['width'])
                y2 = min(match1['y'] + match1['height'], match2['y'] + match2['height'])
                
                if x2 > x1 and y2 > y1:
                    intersection = (x2 - x1) * (y2 - y1)
                    area1 = match1['width'] * match1['height']
                    area2 = match2['width'] * match2['height']
                    union = area1 + area2 - intersection
                    iou = intersection / union if union > 0 else 0
                    
                    if iou > 0.3:  # Overlap threshold
                        should_keep = False
                        break
            
            if should_keep:
                keep.append(match1)
        
        return keep
    
    def _matches_to_bounding_boxes(self, matches: List[Dict]) -> List[BoundingBox]:
        """
        Convert template matches to BoundingBox objects.
        
        Args:
            matches: List of match dictionaries
            
        Returns:
            List of BoundingBox objects
        """
        bounding_boxes = []
        
        for match in matches:
            # Adjust label based on template type
            label = f"template_{match['template']}"
            
            # Adjust confidence based on template type
            # Give higher confidence to frame and screen templates
            confidence_boost = 1.0
            if match['template'] in ['frame', 'screen']:
                confidence_boost = 1.1
            elif match['template'] in ['device']:
                confidence_boost = 1.05
            
            bbox = BoundingBox(
                x=float(match['x']),
                y=float(match['y']),
                width=float(match['width']),
                height=float(match['height']),
                confidence=min(match['confidence'] * confidence_boost, 1.0),
                label=label
            )
            
            bounding_boxes.append(bbox)
        
        return bounding_boxes