#\!/bin/bash

echo "=== OpenCV Detection Configuration Status ==="
echo

# Check environment variables
echo "Environment Variables:"
echo "USE_OPENCV_DETECTION: ${USE_OPENCV_DETECTION:-not set}"
echo "OPENCV_DETECTION_PERCENTAGE: ${OPENCV_DETECTION_PERCENTAGE:-not set}"
echo

# Set them if not set
export USE_OPENCV_DETECTION=true
export OPENCV_DETECTION_PERCENTAGE=100

echo "After setting:"
echo "USE_OPENCV_DETECTION: $USE_OPENCV_DETECTION"
echo "OPENCV_DETECTION_PERCENTAGE: $OPENCV_DETECTION_PERCENTAGE"
echo

# Check Python feature flags
source venv/bin/activate
python -c "
from src.services.feature_flags import FeatureFlags
ff = FeatureFlags()
print('Python Feature Flags:')
print(f'  USE_OPENCV_DETECTION: {ff.is_enabled(ff.USE_OPENCV_DETECTION)}')
print(f'  OPENCV_DETECTION_PERCENTAGE: {ff.get(ff.OPENCV_DETECTION_PERCENTAGE)}')
print(f'  Should use OpenCV: {ff.should_use_opencv_detection(\"test-job\")}')
"

echo
echo "✅ OpenCV detection is configured for 100% rollout"
echo "🔄 Workers should be restarted to apply these settings"
