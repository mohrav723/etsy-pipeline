#!/usr/bin/env python3
"""Test script to verify OpenCV detection is working"""

import os
import sys

# Set environment variables
os.environ['USE_OPENCV_DETECTION'] = 'true'
os.environ['OPENCV_DETECTION_PERCENTAGE'] = '100'

# Add the backend directory to Python path
backend_path = os.path.abspath(os.path.dirname(__file__))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.services.opencv_detection.compatibility_wrapper import create_object_detection_service
from src.services.feature_flags import FeatureFlags
from PIL import Image
import numpy as np

# Check feature flags
flags = FeatureFlags()
print(f"USE_OPENCV_DETECTION: {flags.is_enabled(flags.USE_OPENCV_DETECTION)}")
print(f"OPENCV_DETECTION_PERCENTAGE: {flags.get(flags.OPENCV_DETECTION_PERCENTAGE)}")
print(f"Should use OpenCV for test job: {flags.should_use_opencv_detection('test-job')}")

# Create a test image
print("\nCreating test image...")
test_image = Image.new('RGB', (800, 600), color='white')
pixels = np.array(test_image)
# Add a black rectangle (mock frame)
pixels[100:500, 100:700] = [0, 0, 0]  # Black frame
pixels[150:450, 150:650] = [255, 255, 255]  # White interior
test_image = Image.fromarray(pixels)

# Test detection service
print("\nCreating detection service...")
detection_service = create_object_detection_service(job_id='test-job')
service_type = "OpenCV" if detection_service.use_opencv else "DETR"
print(f"Using {service_type} detection service")

# Find regions
print("\nDetecting regions...")
try:
    regions = detection_service.find_suitable_regions(test_image)
    print(f"Found {len(regions)} regions:")
    for i, region in enumerate(regions):
        print(f"  Region {i+1}: {region.label} at ({region.x}, {region.y}) "
              f"size {region.width}x{region.height} confidence {region.confidence:.3f}")
except Exception as e:
    print(f"Error during detection: {e}")
    import traceback
    traceback.print_exc()

print("\nTest complete!")