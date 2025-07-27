"""
Simple test to verify our Temporal workflow imports work correctly
"""
import os
import sys

def test_imports():
    """Test if we can import our existing services"""
    try:
        print("Testing imports...")
        
        # Test BFL API import
        from src.services.bfl_api import generate_art_image
        print("✅ BFL API import successful")
        
        # Test worker import  
        from src.worker import upload_image_to_storage
        print("✅ Worker upload function import successful")
        
        # Test Firestore
        import google.cloud.firestore as firestore
        db = firestore.Client()
        print("✅ Firestore client created successfully")
        
        # Test Temporal workflow import
        from simple_workflow import SimpleImageWorkflow, generate_and_store_image, update_firestore_job
        print("✅ Temporal workflow imports successful")
        
        print("\n🎉 All imports working! Ready to test workflow.")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_job_data():
    """Test workflow with sample job data"""
    sample_job = {
        'job_id': 'test_123',
        'prompt': 'A beautiful sunset over mountains',
        'aspectRatio': '16:9',
        'steps': 28,
        'guidance': 3.0,
        'seed': 42,
        'promptUpsampling': False,
        'safetyTolerance': 2,
        'generationCount': 0
    }
    
    print("Sample job data:")
    for key, value in sample_job.items():
        print(f"  {key}: {value}")
    
    return sample_job

if __name__ == "__main__":
    print("🧪 Testing Temporal Migration Setup\n")
    
    if test_imports():
        sample_job = test_job_data()
        print(f"\n✅ Ready to test with job: {sample_job['job_id']}")
    else:
        print("\n❌ Fix imports before proceeding")