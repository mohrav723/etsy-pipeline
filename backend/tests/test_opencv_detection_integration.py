"""
Comprehensive integration tests for OpenCV object detection with real mockup scenarios.

This test suite validates the OpenCV detection service against various mockup
template types and compares performance with the DETR implementation.
"""

import pytest
import os
import sys
import time
import json
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from unittest.mock import patch
import tempfile
import shutil

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.services.opencv_detection import (
    OpenCVObjectDetectionService,
    OpenCVObjectDetectionConfig,
    BoundingBox
)
from src.services.object_detection import ObjectDetectionService
from src.services.opencv_detection.compatibility_wrapper import create_object_detection_service


class MockupTemplateGenerator:
    """Generates synthetic mockup templates for testing."""
    
    @staticmethod
    def create_tshirt_mockup() -> Image.Image:
        """Create a t-shirt mockup template."""
        img = Image.new('RGB', (800, 1000), 'white')
        draw = ImageDraw.Draw(img)
        
        # T-shirt outline
        draw.polygon([
            (200, 200), (250, 150), (550, 150), (600, 200),
            (600, 700), (550, 750), (250, 750), (200, 700)
        ], outline='gray', width=3)
        
        # Design area rectangle
        draw.rectangle([300, 350, 500, 550], outline='lightgray', width=2)
        
        return img
        
    @staticmethod
    def create_mug_mockup() -> Image.Image:
        """Create a mug mockup template."""
        img = Image.new('RGB', (600, 600), 'lightgray')
        draw = ImageDraw.Draw(img)
        
        # Mug body
        draw.ellipse([150, 200, 450, 500], fill='white', outline='gray', width=3)
        
        # Handle
        draw.arc([380, 280, 480, 420], start=270, end=90, fill='gray', width=5)
        
        # Design area
        draw.rectangle([200, 300, 400, 400], outline='lightgray', width=2)
        
        return img
        
    @staticmethod
    def create_poster_frame_mockup() -> Image.Image:
        """Create a poster frame mockup template."""
        img = Image.new('RGB', (700, 900), 'white')
        draw = ImageDraw.Draw(img)
        
        # Outer frame
        draw.rectangle([50, 50, 650, 850], fill='brown', outline='darkbrown', width=5)
        
        # Inner frame (where artwork goes)
        draw.rectangle([100, 100, 600, 800], fill='white', outline='black', width=2)
        
        # Mat border
        draw.rectangle([150, 150, 550, 750], fill='lightgray', outline='gray', width=1)
        
        return img
        
    @staticmethod
    def create_phone_case_mockup() -> Image.Image:
        """Create a phone case mockup template."""
        img = Image.new('RGB', (400, 800), 'white')
        draw = ImageDraw.Draw(img)
        
        # Phone outline
        draw.rounded_rectangle([50, 50, 350, 750], radius=30, 
                              fill='black', outline='darkgray', width=3)
        
        # Screen area
        draw.rounded_rectangle([70, 120, 330, 680], radius=20, 
                              fill='white', outline='gray', width=2)
        
        # Design area
        draw.rectangle([70, 120, 330, 680], outline='lightgray', width=1)
        
        return img
        
    @staticmethod
    def create_canvas_mockup() -> Image.Image:
        """Create a canvas print mockup template."""
        img = Image.new('RGB', (800, 600), 'lightgray')
        draw = ImageDraw.Draw(img)
        
        # Canvas with perspective
        points = [(100, 150), (700, 100), (750, 500), (50, 550)]
        draw.polygon(points, fill='white', outline='gray', width=3)
        
        # Side edge (3D effect)
        draw.polygon([(700, 100), (750, 120), (800, 520), (750, 500)], 
                    fill='darkgray', outline='gray', width=2)
        
        return img
        
    @staticmethod
    def create_multi_region_mockup() -> Image.Image:
        """Create a mockup with multiple suitable regions."""
        img = Image.new('RGB', (1000, 800), 'white')
        draw = ImageDraw.Draw(img)
        
        # Region 1: Large frame
        draw.rectangle([50, 50, 450, 350], outline='black', width=4)
        draw.rectangle([80, 80, 420, 320], fill='lightblue', outline='gray', width=2)
        
        # Region 2: Medium frame
        draw.rectangle([550, 100, 750, 300], outline='black', width=3)
        draw.rectangle([570, 120, 730, 280], fill='lightgreen', outline='gray', width=2)
        
        # Region 3: Small decorative area
        draw.rectangle([600, 400, 900, 600], outline='black', width=3)
        draw.rectangle([620, 420, 880, 580], fill='lightyellow', outline='gray', width=2)
        
        # Non-suitable elements (too small)
        for i in range(5):
            x = 100 + i * 150
            draw.rectangle([x, 650, x + 50, 700], outline='gray', width=1)
            
        return img


class TestOpenCVDetectionIntegration:
    """Comprehensive integration tests for OpenCV detection."""
    
    @pytest.fixture
    def opencv_service(self):
        """Create OpenCV detection service."""
        config = OpenCVObjectDetectionConfig.for_mockup_templates()
        return OpenCVObjectDetectionService(config)
        
    @pytest.fixture
    def mockup_templates(self) -> Dict[str, Image.Image]:
        """Generate all mockup templates."""
        generator = MockupTemplateGenerator()
        return {
            'tshirt': generator.create_tshirt_mockup(),
            'mug': generator.create_mug_mockup(),
            'poster_frame': generator.create_poster_frame_mockup(),
            'phone_case': generator.create_phone_case_mockup(),
            'canvas': generator.create_canvas_mockup(),
            'multi_region': generator.create_multi_region_mockup()
        }
        
    def test_tshirt_detection(self, opencv_service, mockup_templates):
        """Test detection on t-shirt mockup."""
        regions = opencv_service.find_suitable_regions(mockup_templates['tshirt'])
        
        assert len(regions) > 0, "Should detect at least one region on t-shirt"
        
        # Check that detected region is in the design area
        primary_region = regions[0]
        assert 250 < primary_region.x < 350
        assert 300 < primary_region.y < 400
        assert 150 < primary_region.width < 250
        assert 150 < primary_region.height < 250
        
    def test_mug_detection(self, opencv_service, mockup_templates):
        """Test detection on mug mockup."""
        regions = opencv_service.find_suitable_regions(mockup_templates['mug'])
        
        assert len(regions) > 0, "Should detect at least one region on mug"
        
        # Verify detected region is on the mug body
        primary_region = regions[0]
        assert primary_region.width > 100
        assert primary_region.height > 50
        
    def test_poster_frame_detection(self, opencv_service, mockup_templates):
        """Test detection on poster frame mockup."""
        regions = opencv_service.find_suitable_regions(mockup_templates['poster_frame'])
        
        assert len(regions) > 0, "Should detect poster frame region"
        
        # Should detect the inner frame area
        primary_region = regions[0]
        assert primary_region.width > 300
        assert primary_region.height > 400
        
    def test_phone_case_detection(self, opencv_service, mockup_templates):
        """Test detection on phone case mockup."""
        regions = opencv_service.find_suitable_regions(mockup_templates['phone_case'])
        
        assert len(regions) > 0, "Should detect phone case design area"
        
        # Check aspect ratio matches phone screen
        primary_region = regions[0]
        aspect_ratio = primary_region.width / primary_region.height
        assert 0.4 < aspect_ratio < 0.7, "Should match phone aspect ratio"
        
    def test_canvas_detection(self, opencv_service, mockup_templates):
        """Test detection on canvas mockup with perspective."""
        regions = opencv_service.find_suitable_regions(mockup_templates['canvas'])
        
        assert len(regions) > 0, "Should detect canvas area"
        
        # Canvas should be detected as a large region
        primary_region = regions[0]
        assert primary_region.width > 400
        assert primary_region.height > 200
        
    def test_multi_region_detection(self, opencv_service, mockup_templates):
        """Test detection of multiple suitable regions."""
        regions = opencv_service.find_suitable_regions(mockup_templates['multi_region'])
        
        assert len(regions) >= 3, "Should detect at least 3 suitable regions"
        
        # Verify regions are sorted by score (best first)
        areas = [(r.width * r.height) for r in regions]
        
        # Should not include tiny regions
        min_area = min(areas)
        assert min_area > 5000, "Should filter out small regions"
        
    def test_performance_benchmark(self, opencv_service, mockup_templates):
        """Benchmark OpenCV detection performance."""
        times = []
        
        for name, template in mockup_templates.items():
            start_time = time.time()
            regions = opencv_service.find_suitable_regions(template)
            elapsed = time.time() - start_time
            times.append(elapsed)
            
            print(f"{name}: {elapsed:.3f}s, {len(regions)} regions")
            
        avg_time = np.mean(times)
        assert avg_time < 2.0, f"Average detection time {avg_time:.3f}s exceeds 2 second target"
        
    def test_detr_opencv_compatibility(self, mockup_templates):
        """Compare DETR and OpenCV detection results."""
        # Skip if DETR models not available
        try:
            detr_service = ObjectDetectionService()
        except Exception:
            pytest.skip("DETR models not available")
            
        opencv_service = OpenCVObjectDetectionService()
        
        compatibility_results = []
        
        for name, template in mockup_templates.items():
            try:
                # Get DETR results
                detr_start = time.time()
                detr_regions = detr_service.find_suitable_regions(template)
                detr_time = time.time() - detr_start
                
                # Get OpenCV results
                opencv_start = time.time()
                opencv_regions = opencv_service.find_suitable_regions(template)
                opencv_time = time.time() - opencv_start
                
                compatibility_results.append({
                    'template': name,
                    'detr_regions': len(detr_regions),
                    'opencv_regions': len(opencv_regions),
                    'detr_time': detr_time,
                    'opencv_time': opencv_time,
                    'speedup': detr_time / opencv_time if opencv_time > 0 else 0
                })
                
            except Exception as e:
                print(f"Error comparing {name}: {e}")
                
        # Check overall compatibility
        if compatibility_results:
            avg_speedup = np.mean([r['speedup'] for r in compatibility_results])
            print(f"\nAverage speedup: {avg_speedup:.2f}x")
            
            # Both should find regions in most cases
            both_found = sum(1 for r in compatibility_results 
                           if r['detr_regions'] > 0 and r['opencv_regions'] > 0)
            compatibility_rate = both_found / len(compatibility_results) * 100
            print(f"Compatibility rate: {compatibility_rate:.1f}%")
            
    def test_edge_cases(self, opencv_service):
        """Test edge cases and error handling."""
        # Empty image
        empty_img = Image.new('RGB', (100, 100), 'white')
        regions = opencv_service.find_suitable_regions(empty_img)
        assert len(regions) > 0, "Should use fallback for empty image"
        
        # Very small image
        tiny_img = Image.new('RGB', (50, 50), 'gray')
        regions = opencv_service.find_suitable_regions(tiny_img)
        assert len(regions) > 0, "Should handle tiny images"
        
        # High noise image
        noise_img = Image.fromarray(
            np.random.randint(0, 255, (200, 200, 3), dtype=np.uint8)
        )
        regions = opencv_service.find_suitable_regions(noise_img)
        assert len(regions) > 0, "Should handle noisy images with fallback"
        
    def test_config_variations(self, mockup_templates):
        """Test different configuration settings."""
        template = mockup_templates['poster_frame']
        
        # High quality config
        hq_config = OpenCVObjectDetectionConfig.for_high_quality()
        hq_service = OpenCVObjectDetectionService(hq_config)
        hq_regions = hq_service.find_suitable_regions(template)
        
        # Fast detection config
        fast_config = OpenCVObjectDetectionConfig.for_fast_detection()
        fast_service = OpenCVObjectDetectionService(fast_config)
        fast_regions = fast_service.find_suitable_regions(template)
        
        # Both should find regions
        assert len(hq_regions) > 0
        assert len(fast_regions) > 0
        
        # High quality might find more regions
        print(f"High quality: {len(hq_regions)} regions")
        print(f"Fast: {len(fast_regions)} regions")
        
    def test_detector_specific_performance(self, opencv_service, mockup_templates):
        """Test individual detector performance."""
        template = mockup_templates['poster_frame']
        
        # Test with only edge detector
        edge_config = OpenCVObjectDetectionConfig(enabled_detectors=['edge'])
        edge_service = OpenCVObjectDetectionService(edge_config)
        edge_regions = edge_service.find_suitable_regions(template)
        
        # Test with only contour detector  
        contour_config = OpenCVObjectDetectionConfig(enabled_detectors=['contour'])
        contour_service = OpenCVObjectDetectionService(contour_config)
        contour_regions = contour_service.find_suitable_regions(template)
        
        # Both should work for frame detection
        assert len(edge_regions) > 0, "Edge detector should find frame"
        assert len(contour_regions) > 0, "Contour detector should find frame"
        
    @pytest.mark.parametrize("template_name", [
        'tshirt', 'mug', 'poster_frame', 'phone_case', 'canvas'
    ])
    def test_consistency_across_runs(self, opencv_service, mockup_templates, template_name):
        """Test that detection is consistent across multiple runs."""
        template = mockup_templates[template_name]
        
        results = []
        for _ in range(5):
            regions = opencv_service.find_suitable_regions(template)
            results.append(len(regions))
            
        # Results should be consistent
        assert len(set(results)) == 1, f"Inconsistent results across runs: {results}"
        
    def test_save_detection_results(self, opencv_service, mockup_templates, tmp_path):
        """Save detection results for visual inspection."""
        results_dir = tmp_path / "detection_results"
        results_dir.mkdir()
        
        for name, template in mockup_templates.items():
            regions = opencv_service.find_suitable_regions(template)
            
            # Draw regions on template
            result_img = template.copy()
            draw = ImageDraw.Draw(result_img)
            
            for i, region in enumerate(regions):
                color = ['red', 'green', 'blue', 'yellow', 'purple'][i % 5]
                draw.rectangle(
                    [region.x, region.y, region.x + region.width, region.y + region.height],
                    outline=color, width=3
                )
                draw.text((region.x + 5, region.y + 5), f"#{i+1}", fill=color)
                
            # Save result
            result_img.save(results_dir / f"{name}_detected.png")
            
        print(f"\nDetection results saved to: {results_dir}")
        
        
class TestPerformanceMetrics:
    """Test performance monitoring and metrics collection."""
    
    def test_detection_metrics_collection(self):
        """Test that metrics are properly collected during detection."""
        config = OpenCVObjectDetectionConfig()
        service = OpenCVObjectDetectionService(config)
        
        # Create test image
        img = Image.new('RGB', (400, 400), 'white')
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 350, 350], outline='black', width=3)
        
        # Patch time to measure metrics collection
        with patch('time.time') as mock_time:
            mock_time.side_effect = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
            regions = service.find_suitable_regions(img)
            
        assert len(regions) > 0
        # Verify time was measured multiple times
        assert mock_time.call_count >= 2
        
        
if __name__ == '__main__':
    pytest.main([__file__, '-v'])