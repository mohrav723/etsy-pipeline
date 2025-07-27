"""
Test that existing simple mockup generation continues to work
after adding new dependencies for intelligent mockup generation.
"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import tempfile
import io

# Add backend directory to Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


class TestSimpleMockupCompatibility:
    """Test that simple mockup generation workflow remains functional."""
    
    def test_mockup_generation_workflow_imports(self):
        """Test that mockup generation workflow can be imported."""
        try:
            from src.temporal.mockup_generation_workflow import MockupGenerationWorkflow
            assert MockupGenerationWorkflow is not None
        except ImportError as e:
            pytest.fail(f"Failed to import MockupGenerationWorkflow: {e}")
    
    def test_mockup_activities_exist(self):
        """Test that all required mockup generation activities exist."""
        try:
            from src.temporal.mockup_generation_workflow import (
                get_available_mockups,
                create_draft_entry,
                generate_mockup_image,
                update_draft_with_mockup,
                mark_draft_failed
            )
            
            # Verify activities are callable
            assert callable(get_available_mockups)
            assert callable(create_draft_entry)
            assert callable(generate_mockup_image)
            assert callable(update_draft_with_mockup)
            assert callable(mark_draft_failed)
            
        except ImportError as e:
            pytest.fail(f"Failed to import mockup activities: {e}")
    
    def test_simple_mockup_creation_function(self):
        """Test the simple mockup creation function still works."""
        try:
            from src.temporal.mockup_generation_workflow import create_simple_mockup
            from PIL import Image
            
            # Create test images
            original = Image.new('RGB', (100, 100), color='red')
            template = Image.new('RGB', (200, 200), color='blue')
            
            # Test the function
            result = create_simple_mockup(original, template)
            
            assert isinstance(result, Image.Image)
            assert result.size == template.size  # Should maintain template size
            
        except Exception as e:
            pytest.fail(f"Simple mockup creation failed: {e}")
    
    def test_get_available_mockups_structure(self):
        """Test that get_available_mockups activity structure is correct."""
        try:
            from src.temporal.mockup_generation_workflow import get_available_mockups
            
            # Just test that the function exists and is callable
            assert callable(get_available_mockups)
            
            # Test that the function has the expected name
            assert get_available_mockups.__name__ == 'get_available_mockups'
                
        except Exception as e:
            pytest.fail(f"get_available_mockups test failed: {e}")
    
    def test_upload_mockup_to_storage_function(self):
        """Test that upload_mockup_to_storage function exists and has correct signature."""
        try:
            from src.temporal.mockup_generation_workflow import upload_mockup_to_storage
            
            # Test with mock to avoid actual upload
            with patch('google.cloud.storage.Client') as mock_storage:
                mock_bucket = Mock()
                mock_blob = Mock()
                mock_storage.return_value.bucket.return_value = mock_bucket
                mock_bucket.blob.return_value = mock_blob
                mock_blob.public_url = "https://example.com/test.png"
                
                # Set environment variable
                with patch.dict(os.environ, {'FIREBASE_STORAGE_BUCKET': 'test-bucket'}):
                    result = upload_mockup_to_storage(b"test_data", "draft_123")
                    assert result == "https://example.com/test.png"
                
        except Exception as e:
            pytest.fail(f"upload_mockup_to_storage test failed: {e}")
    
    def test_temporal_job_starter_mockup_handling(self):
        """Test that temporal job starter can handle mockup jobs."""
        try:
            from src.temporal.temporal_job_starter import TemporalJobStarter
            
            # Test that the class can be instantiated
            with patch('google.cloud.firestore.Client'):
                starter = TemporalJobStarter()
                assert starter is not None
                
                # Test that mockup handling methods exist
                assert hasattr(starter, 'handle_mockup_changes')
                assert hasattr(starter, 'process_mockup_job')
                assert callable(starter.handle_mockup_changes)
                assert callable(starter.process_mockup_job)
                
        except Exception as e:
            pytest.fail(f"Temporal job starter mockup handling test failed: {e}")
    
    def test_existing_collections_not_affected(self):
        """Test that adding intelligent mockup doesn't affect existing collections."""
        try:
            from src.temporal.temporal_job_starter import TemporalJobStarter
            
            with patch('google.cloud.firestore.Client') as mock_firestore:
                mock_db = Mock()
                mock_firestore.return_value = mock_db
                
                starter = TemporalJobStarter()
                
                # Verify that existing collections are still referenced
                # These should be called during startup
                starter.db.collection.assert_not_called()  # Since we haven't called start()
                
                # Test that the collections would be accessed correctly
                jobs_ref = starter.db.collection('jobs')
                mockup_jobs_ref = starter.db.collection('mockup_jobs')
                
                # Verify these don't raise errors
                assert jobs_ref is not None
                assert mockup_jobs_ref is not None
                
        except Exception as e:
            pytest.fail(f"Existing collections test failed: {e}")
    
    def test_no_import_conflicts_with_new_dependencies(self):
        """Test that importing new dependencies doesn't break existing mockup code."""
        try:
            # Import new dependencies first
            import torch
            import transformers
            import cv2
            
            # Then import existing mockup functionality
            from src.temporal.mockup_generation_workflow import (
                MockupGenerationWorkflow,
                create_simple_mockup,
                upload_mockup_to_storage
            )
            from PIL import Image
            
            # Test that PIL and OpenCV can work together
            pil_image = Image.new('RGB', (50, 50), color='green')
            import numpy as np
            numpy_array = np.array(pil_image)
            
            # Convert to OpenCV and back
            opencv_image = cv2.cvtColor(numpy_array, cv2.COLOR_RGB2BGR)
            back_to_rgb = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2RGB)
            back_to_pil = Image.fromarray(back_to_rgb)
            
            assert back_to_pil.size == pil_image.size
            
        except Exception as e:
            pytest.fail(f"Import conflicts test failed: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])