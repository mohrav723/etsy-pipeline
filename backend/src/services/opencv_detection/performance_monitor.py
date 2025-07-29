"""
Performance monitoring for OpenCV object detection service.

This module provides detailed metrics collection and logging for monitoring
the performance of the OpenCV detection service in production.
"""

import time
import logging
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import deque
import numpy as np
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


@dataclass
class DetectionMetrics:
    """Metrics for a single detection operation."""
    job_id: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    total_time: float = 0.0
    image_size: tuple = (0, 0)
    regions_detected: int = 0
    detector_timings: Dict[str, float] = field(default_factory=dict)
    preprocessing_time: float = 0.0
    merging_time: float = 0.0
    ranking_time: float = 0.0
    service_type: str = "opencv"
    success: bool = True
    error: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert metrics to JSON string."""
        return json.dumps(self.to_dict())


class PerformanceMonitor:
    """Monitor and collect performance metrics for object detection."""
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize performance monitor.
        
        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self._metrics_history = deque(maxlen=max_history)
        self._current_metrics: Optional[DetectionMetrics] = None
        self._lock = threading.Lock()
        self._callbacks: List[Callable[[DetectionMetrics], None]] = []
        
    @contextmanager
    def measure_detection(self, job_id: Optional[str] = None, 
                         image_size: tuple = (0, 0)):
        """
        Context manager to measure overall detection time.
        
        Args:
            job_id: Optional job identifier
            image_size: Size of the input image (width, height)
        """
        self._current_metrics = DetectionMetrics(
            job_id=job_id,
            image_size=image_size
        )
        
        start_time = time.time()
        try:
            yield self._current_metrics
            self._current_metrics.success = True
        except GeneratorExit:
            # Handle generator cleanup properly
            self._current_metrics.total_time = time.time() - start_time
            self._record_metrics(self._current_metrics)
            raise
        except Exception as e:
            self._current_metrics.success = False
            self._current_metrics.error = str(e)
            raise
        finally:
            if self._current_metrics.total_time == 0:  # Not yet recorded
                self._current_metrics.total_time = time.time() - start_time
                self._record_metrics(self._current_metrics)
            
    @contextmanager
    def measure_phase(self, phase_name: str):
        """
        Context manager to measure a specific phase of detection.
        
        Args:
            phase_name: Name of the phase (e.g., 'preprocessing', 'edge_detector')
        """
        if not self._current_metrics:
            yield
            return
            
        start_time = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start_time
            
            if phase_name in ['preprocessing', 'merging', 'ranking']:
                setattr(self._current_metrics, f"{phase_name}_time", elapsed)
            else:
                self._current_metrics.detector_timings[phase_name] = elapsed
                
    def record_regions_detected(self, count: int):
        """Record the number of regions detected."""
        if self._current_metrics:
            self._current_metrics.regions_detected = count
            
    def record_memory_usage(self, memory_mb: float):
        """Record memory usage in megabytes."""
        if self._current_metrics:
            self._current_metrics.memory_usage_mb = memory_mb
            
    def _record_metrics(self, metrics: DetectionMetrics):
        """Record metrics and trigger callbacks."""
        with self._lock:
            self._metrics_history.append(metrics)
            
        # Log metrics
        logger.info(
            f"Detection completed: job_id={metrics.job_id}, "
            f"time={metrics.total_time:.3f}s, regions={metrics.regions_detected}, "
            f"success={metrics.success}"
        )
        
        # Trigger callbacks
        for callback in self._callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in metrics callback: {e}")
                
    def add_callback(self, callback: Callable[[DetectionMetrics], None]):
        """Add a callback to be triggered when metrics are recorded."""
        self._callbacks.append(callback)
        
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary statistics of recent detections."""
        with self._lock:
            if not self._metrics_history:
                return {}
                
            metrics_list = list(self._metrics_history)
            
        # Calculate statistics
        total_times = [m.total_time for m in metrics_list if m.success]
        regions_counts = [m.regions_detected for m in metrics_list if m.success]
        success_count = sum(1 for m in metrics_list if m.success)
        error_count = sum(1 for m in metrics_list if not m.success)
        
        summary = {
            'total_detections': len(metrics_list),
            'successful_detections': success_count,
            'failed_detections': error_count,
            'success_rate': success_count / len(metrics_list) * 100 if metrics_list else 0,
            'avg_detection_time': np.mean(total_times) if total_times else 0,
            'p50_detection_time': np.percentile(total_times, 50) if total_times else 0,
            'p95_detection_time': np.percentile(total_times, 95) if total_times else 0,
            'p99_detection_time': np.percentile(total_times, 99) if total_times else 0,
            'avg_regions_detected': np.mean(regions_counts) if regions_counts else 0,
            'detector_performance': self._get_detector_performance(metrics_list)
        }
        
        return summary
        
    def _get_detector_performance(self, metrics_list: List[DetectionMetrics]) -> Dict[str, Any]:
        """Calculate per-detector performance statistics."""
        detector_times = {}
        
        for metrics in metrics_list:
            if not metrics.success:
                continue
                
            for detector, timing in metrics.detector_timings.items():
                if detector not in detector_times:
                    detector_times[detector] = []
                detector_times[detector].append(timing)
                
        performance = {}
        for detector, times in detector_times.items():
            performance[detector] = {
                'avg_time': np.mean(times),
                'p95_time': np.percentile(times, 95),
                'call_count': len(times)
            }
            
        return performance
        
    def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent detection metrics."""
        with self._lock:
            recent = list(self._metrics_history)[-limit:]
            
        return [m.to_dict() for m in recent]
        
    def export_metrics(self, filepath: str):
        """Export metrics history to a JSON file."""
        metrics_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'summary': self.get_metrics_summary(),
            'metrics': self.get_recent_metrics(limit=None)
        }
        
        with open(filepath, 'w') as f:
            json.dump(metrics_data, f, indent=2)
            
        logger.info(f"Exported {len(metrics_data['metrics'])} metrics to {filepath}")
        

class MetricsLogger:
    """Logger specifically for metrics that can be consumed by monitoring systems."""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize metrics logger.
        
        Args:
            log_file: Optional file path for metrics logs
        """
        self.logger = logging.getLogger('opencv_detection_metrics')
        self.logger.setLevel(logging.INFO)
        
        # Add JSON formatter
        formatter = logging.Formatter('%(message)s')
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
    def log_metrics(self, metrics: DetectionMetrics):
        """Log metrics in JSON format for monitoring systems."""
        self.logger.info(metrics.to_json())
        

# Global performance monitor instance
_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
        
        # Add metrics logger callback
        metrics_logger = MetricsLogger()
        _monitor.add_callback(metrics_logger.log_metrics)
        
    return _monitor


def log_detection_metrics(job_id: Optional[str], image_size: tuple, 
                         regions_count: int, total_time: float,
                         service_type: str = "opencv"):
    """
    Convenience function to log detection metrics.
    
    Args:
        job_id: Job identifier
        image_size: Image dimensions (width, height)
        regions_count: Number of regions detected
        total_time: Total detection time in seconds
        service_type: Type of detection service used
    """
    metrics = DetectionMetrics(
        job_id=job_id,
        image_size=image_size,
        regions_detected=regions_count,
        total_time=total_time,
        service_type=service_type
    )
    
    monitor = get_performance_monitor()
    monitor._record_metrics(metrics)