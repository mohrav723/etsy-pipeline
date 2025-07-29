"""
Feature flag configuration for controlling system behavior.

This module provides centralized feature flag management for gradual rollouts
and A/B testing of new features.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeatureFlags:
    """Manages feature flags for the application."""
    
    # Feature flag keys
    USE_OPENCV_DETECTION = "use_opencv_detection"
    OPENCV_DETECTION_PERCENTAGE = "opencv_detection_percentage"
    OPENCV_DETECTION_ENABLED_JOBS = "opencv_detection_enabled_jobs"
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize feature flags.
        
        Args:
            config_file: Path to JSON config file (optional)
        """
        self._flags: Dict[str, Any] = {}
        self._config_file = config_file
        self._load_flags()
        
    def _load_flags(self) -> None:
        """Load feature flags from environment and config file."""
        # Default values
        self._flags = {
            self.USE_OPENCV_DETECTION: False,
            self.OPENCV_DETECTION_PERCENTAGE: 0,  # Percentage rollout (0-100)
            self.OPENCV_DETECTION_ENABLED_JOBS: []  # Specific job IDs to enable
        }
        
        # Load from environment variables
        if os.environ.get('USE_OPENCV_DETECTION', '').lower() == 'true':
            self._flags[self.USE_OPENCV_DETECTION] = True
            
        if os.environ.get('OPENCV_DETECTION_PERCENTAGE'):
            try:
                percentage = int(os.environ['OPENCV_DETECTION_PERCENTAGE'])
                self._flags[self.OPENCV_DETECTION_PERCENTAGE] = max(0, min(100, percentage))
            except ValueError:
                logger.error("Invalid OPENCV_DETECTION_PERCENTAGE value")
                
        # Load from config file if provided
        if self._config_file and os.path.exists(self._config_file):
            try:
                with open(self._config_file, 'r') as f:
                    file_config = json.load(f)
                    self._flags.update(file_config.get('feature_flags', {}))
                    logger.info(f"Loaded feature flags from {self._config_file}")
            except Exception as e:
                logger.error(f"Failed to load feature flags from file: {e}")
                
    def get(self, flag_name: str, default: Any = None) -> Any:
        """
        Get the value of a feature flag.
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if flag not found
            
        Returns:
            The flag value or default
        """
        return self._flags.get(flag_name, default)
        
    def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a boolean feature flag is enabled.
        
        Args:
            flag_name: Name of the feature flag
            
        Returns:
            True if enabled, False otherwise
        """
        return bool(self._flags.get(flag_name, False))
        
    def should_use_opencv_detection(self, job_id: Optional[str] = None) -> bool:
        """
        Determine if OpenCV detection should be used for a specific job.
        
        Args:
            job_id: Optional job ID for targeted rollout
            
        Returns:
            True if OpenCV should be used, False otherwise
        """
        # Check if globally enabled
        if self.is_enabled(self.USE_OPENCV_DETECTION):
            return True
            
        # Check if job is in enabled list
        if job_id and job_id in self.get(self.OPENCV_DETECTION_ENABLED_JOBS, []):
            return True
            
        # Check percentage rollout
        percentage = self.get(self.OPENCV_DETECTION_PERCENTAGE, 0)
        if percentage > 0 and job_id:
            # Use consistent hashing based on job_id
            hash_value = hash(job_id) % 100
            return hash_value < percentage
            
        return False
        
    def update(self, flag_name: str, value: Any) -> None:
        """
        Update a feature flag value (runtime only, doesn't persist).
        
        Args:
            flag_name: Name of the feature flag
            value: New value
        """
        self._flags[flag_name] = value
        logger.info(f"Updated feature flag {flag_name} to {value}")
        
    def get_all_flags(self) -> Dict[str, Any]:
        """Get all current feature flag values."""
        return self._flags.copy()
        
    def log_flag_status(self) -> None:
        """Log current feature flag status."""
        logger.info("Current feature flags:")
        for flag, value in self._flags.items():
            logger.info(f"  {flag}: {value}")
            

# Global instance
_feature_flags = None


def get_feature_flags() -> FeatureFlags:
    """Get the global feature flags instance."""
    global _feature_flags
    if _feature_flags is None:
        config_file = os.environ.get('FEATURE_FLAGS_CONFIG')
        _feature_flags = FeatureFlags(config_file)
    return _feature_flags


def should_use_opencv_detection(job_id: Optional[str] = None) -> bool:
    """
    Convenience function to check if OpenCV detection should be used.
    
    Args:
        job_id: Optional job ID for targeted rollout
        
    Returns:
        True if OpenCV should be used, False otherwise
    """
    return get_feature_flags().should_use_opencv_detection(job_id)