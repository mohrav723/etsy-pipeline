import os
import uuid
from google.cloud import storage
from dotenv import load_dotenv

load_dotenv()

def upload_image_to_storage(image_data: bytes) -> str:
    """Upload image data to Firebase Storage and return public URL"""
    storage_client = storage.Client()
    BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
    
    if not BUCKET_NAME:
        raise ValueError("FIREBASE_STORAGE_BUCKET not found in .env file.")
    
    bucket = storage_client.bucket(BUCKET_NAME)
    image_name = f"generated-art/{uuid.uuid4()}.png"
    blob = bucket.blob(image_name)
    
    print(f"--- Uploading image to: {image_name}")
    blob.upload_from_string(image_data, content_type='image/png')
    blob.make_public()
    
    print(f"--- Upload complete. Public URL: {blob.public_url}")
    return blob.public_url