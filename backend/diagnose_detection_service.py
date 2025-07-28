#!/usr/bin/env python3
"""Diagnose which detection service is actually being used"""

import os
import sys

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("=== Detection Service Diagnostic ===\n")

# Check environment variables
print("1. Environment Variables:")
print(f"   USE_OPENCV_DETECTION: {os.environ.get('USE_OPENCV_DETECTION', 'not set')}")
print(f"   OPENCV_DETECTION_PERCENTAGE: {os.environ.get('OPENCV_DETECTION_PERCENTAGE', 'not set')}")

# Check feature flags
from src.services.feature_flags import FeatureFlags
flags = FeatureFlags()
print("\n2. Feature Flags:")
print(f"   USE_OPENCV_DETECTION: {flags.is_enabled(flags.USE_OPENCV_DETECTION)}")
print(f"   OPENCV_DETECTION_PERCENTAGE: {flags.get(flags.OPENCV_DETECTION_PERCENTAGE)}")
print(f"   Should use OpenCV for 'test-job': {flags.should_use_opencv_detection('test-job')}")

# Check what service is created
from src.services.opencv_detection.compatibility_wrapper import create_object_detection_service
print("\n3. Detection Service Creation:")
for job_id in ['test-job', 'real-intelligent-aad8a3f9', None]:
    service = create_object_detection_service(job_id=job_id)
    service_type = "OpenCV" if service.use_opencv else "DETR"
    print(f"   Job ID '{job_id}': {service_type}")

# Test with a real image to see the labels
print("\n4. Testing Detection Labels:")
from PIL import Image
import numpy as np

# Create test image with a rectangle
test_image = Image.new('RGB', (800, 600), color='white')
pixels = np.array(test_image)
pixels[100:500, 100:700] = [200, 200, 200]  # Gray rectangle
test_image = Image.fromarray(pixels)

# Test with both forced OpenCV and forced DETR
print("\n   Forced OpenCV:")
opencv_service = create_object_detection_service(use_opencv=True)
try:
    regions = opencv_service.find_suitable_regions(test_image)
    if regions:
        print(f"   - Found {len(regions)} regions")
        for r in regions[:3]:
            print(f"     Label: {r.label}, Confidence: {r.confidence:.3f}")
except Exception as e:
    print(f"   - Error: {e}")

print("\n   Forced DETR:")
detr_service = create_object_detection_service(use_opencv=False)
try:
    regions = detr_service.find_suitable_regions(test_image)
    if regions:
        print(f"   - Found {len(regions)} regions")
        for r in regions[:3]:
            print(f"     Label: {r.label}, Confidence: {r.confidence:.3f}")
except Exception as e:
    print(f"   - Error: {e}")

print("\n✅ Diagnostic complete!")