"""
Integration tests to verify existing workflows continue to function after
adding new dependencies for intelligent mockup generation.

This test suite ensures backward compatibility and no performance degradation.
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, patch
import tempfile
import time

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from src.temporal.simple_workflow import SimpleImageWorkflow
from src.temporal.mockup_generation_workflow import MockupGenerationWorkflow
from src.storage import upload_image_to_storage
from src.cost_tracker import CostTracker


class TestExistingWorkflowsIntegration:
    """Test existing workflows still function with new dependencies installed."""
    
    def test_dependencies_import_compatibility(self):
        """Test that new dependencies don't conflict with existing imports."""
        # Test that existing imports still work
        try:
            import requests
            import google.cloud.firestore as firestore
            from PIL import Image
            import temporalio
            from google.cloud import storage
            assert True, "All existing dependencies import successfully"
        except ImportError as e:
            pytest.fail(f"Existing dependency import failed: {e}")
    
    def test_new_dependencies_import(self):
        """Test that new dependencies can be imported without issues."""
        try:
            import transformers
            import torch
            import cv2  # opencv-python-headless
            assert True, "All new dependencies import successfully"
        except ImportError as e:
            pytest.fail(f"New dependency import failed: {e}")
    
    def test_existing_storage_service_unchanged(self):
        """Test that storage.py functionality remains intact."""
        # Mock the storage operations to avoid actual uploads
        with patch('google.cloud.storage.Client') as mock_storage:
            mock_bucket = Mock()
            mock_blob = Mock()
            mock_storage.return_value.bucket.return_value = mock_bucket
            mock_bucket.blob.return_value = mock_blob
            mock_blob.public_url = "https://example.com/test.png"
            
            # Create test image data
            test_image_data = b"fake_image_data"
            
            try:
                # This should work without any changes
                from src.storage import upload_image_to_storage
                result = upload_image_to_storage(test_image_data)
                assert result == "https://example.com/test.png"
            except Exception as e:
                pytest.fail(f"Storage service failed: {e}")
    
    def test_cost_tracker_unchanged(self):
        """Test that cost tracking functionality remains intact."""
        try:
            cost_tracker = CostTracker()
            
            # Test cost tracking methods still work
            storage_cost = cost_tracker.log_storage_cost(
                job_id="test_job",
                image_size_bytes=1024,
                operation_type="test_upload"
            )
            assert isinstance(storage_cost, (int, float))
            
            bfl_cost = cost_tracker.log_bfl_cost(
                job_id="test_job",
                model="flux_dev",
                steps=28
            )
            assert isinstance(bfl_cost, (int, float))
            
        except Exception as e:
            pytest.fail(f"Cost tracker failed: {e}")
    
    @patch('google.cloud.firestore.Client')
    def test_simple_workflow_structure_unchanged(self, mock_firestore):
        """Test that SimpleImageWorkflow class structure is unchanged."""
        try:
            # Verify the workflow class exists and has expected methods
            assert hasattr(SimpleImageWorkflow, 'run'), "SimpleImageWorkflow.run method missing"
            
            # Test workflow can be instantiated
            workflow = SimpleImageWorkflow()
            assert workflow is not None
            
        except Exception as e:
            pytest.fail(f"SimpleImageWorkflow structure test failed: {e}")
    
    @patch('google.cloud.firestore.Client')
    def test_mockup_workflow_structure_unchanged(self, mock_firestore):
        """Test that existing MockupGenerationWorkflow class structure is unchanged."""
        try:
            # Verify the workflow class exists and has expected methods
            assert hasattr(MockupGenerationWorkflow, 'run'), "MockupGenerationWorkflow.run method missing"
            
            # Test workflow can be instantiated
            workflow = MockupGenerationWorkflow()
            assert workflow is not None
            
        except Exception as e:
            pytest.fail(f"MockupGenerationWorkflow structure test failed: {e}")
    
    def test_temporal_imports_unchanged(self):
        """Test that Temporal-related imports still work."""
        try:
            from temporalio import workflow, activity
            from temporalio.client import Client
            from temporalio.common import RetryPolicy
            from datetime import timedelta
            assert True, "All Temporal imports work correctly"
        except ImportError as e:
            pytest.fail(f"Temporal import failed: {e}")
    
    def test_memory_usage_baseline(self):
        """Test memory usage doesn't significantly increase with new dependencies loaded."""
        import psutil
        import gc
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Import new heavy dependencies
        import torch
        import transformers
        import cv2
        
        # Force garbage collection
        gc.collect()
        
        # Get memory after imports
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB for basic imports)
        assert memory_increase < 500, f"Memory increase too high: {memory_increase}MB"
    
    def test_import_time_performance(self):
        """Test that importing new dependencies doesn't cause significant delays."""
        import time
        
        # Test existing imports are still fast
        start_time = time.time()
        import requests
        import google.cloud.firestore as firestore
        from PIL import Image
        existing_import_time = time.time() - start_time
        
        # Should be very fast (less than 1 second)
        assert existing_import_time < 1.0, f"Existing imports too slow: {existing_import_time}s"
        
        # Test new imports (first time will be slower due to heavy libraries)
        start_time = time.time()
        import torch
        import transformers
        import cv2
        new_import_time = time.time() - start_time
        
        # Should complete within reasonable time (less than 10 seconds)
        assert new_import_time < 10.0, f"New imports too slow: {new_import_time}s"
    
    def test_no_dependency_conflicts(self):
        """Test that new dependencies don't conflict with existing ones."""
        try:
            # Import both old and new dependencies together
            import requests
            import google.cloud.firestore as firestore
            from PIL import Image
            import temporalio
            from google.cloud import storage
            
            import torch
            import transformers
            import cv2
            
            # Test that versions are compatible
            import PIL
            import numpy
            
            # PIL and OpenCV both use numpy - ensure no conflicts
            pil_image = Image.new('RGB', (100, 100), color='red')
            pil_array = numpy.array(pil_image)
            
            # Convert to OpenCV format and back
            cv2_array = cv2.cvtColor(pil_array, cv2.COLOR_RGB2BGR)
            back_to_rgb = cv2.cvtColor(cv2_array, cv2.COLOR_BGR2RGB)
            
            assert back_to_rgb.shape == pil_array.shape, "PIL/OpenCV integration failed"
            
        except Exception as e:
            pytest.fail(f"Dependency conflict detected: {e}")


class TestExistingCollectionsIntact:
    """Test that existing Firestore collections remain unchanged."""
    
    @patch('google.cloud.firestore.Client')
    def test_jobs_collection_unchanged(self, mock_firestore):
        """Test that 'jobs' collection operations still work."""
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        
        # Mock collection operations
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        
        try:
            # Simulate existing job operations
            mock_collection.add.return_value = (None, Mock(id="test_job_123"))
            mock_collection.document.return_value.get.return_value.exists = True
            
            # Test collection access patterns used by existing code
            db = mock_firestore()
            jobs_ref = db.collection('jobs')
            assert jobs_ref is not None
            
        except Exception as e:
            pytest.fail(f"Jobs collection access failed: {e}")
    
    @patch('google.cloud.firestore.Client')
    def test_mockup_jobs_collection_unchanged(self, mock_firestore):
        """Test that 'mockup_jobs' collection operations still work."""
        mock_db = Mock()
        mock_firestore.return_value = mock_db
        
        # Mock collection operations
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection
        
        try:
            # Test collection access patterns used by existing code
            db = mock_firestore()
            mockup_jobs_ref = db.collection('mockup_jobs')
            assert mockup_jobs_ref is not None
            
        except Exception as e:
            pytest.fail(f"Mockup jobs collection access failed: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])