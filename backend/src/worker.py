import os
import uuid
import time
from dotenv import load_dotenv
import google.cloud.firestore
from google.cloud import storage
from src.services.bfl_api import generate_art_image

load_dotenv()
db = google.cloud.firestore.Client()
storage_client = storage.Client()
BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
if not BUCKET_NAME:
    raise ValueError("FIREBASE_STORAGE_BUCKET not found in .env file.")
bucket = storage_client.bucket(BUCKET_NAME)

def upload_image_to_storage(image_data: bytes) -> str:
    image_name = f"generated-art/{uuid.uuid4()}.png"
    blob = bucket.blob(image_name)
    print(f"--- Uploading image to: {image_name}")
    blob.upload_from_string(image_data, content_type='image/png')
    blob.make_public()
    print(f"--- Upload complete. Public URL: {blob.public_url}")
    return blob.public_url

def process_job(doc_snapshot):
    job_id = doc_snapshot.id
    job_data = doc_snapshot.to_dict()
    job_ref = db.collection('jobs').document(job_id)

    print(f"[{job_id}] Received job with status: {job_data.get('status')}")
    
    try:
        # Extract all parameters from the Firestore document
        prompt = job_data.get('prompt')
        aspect_ratio = job_data.get('aspectRatio', '16:9')
        steps = job_data.get('steps', 28)
        guidance = job_data.get('guidance', 3.0)
        seed = job_data.get('seed', 42)
        prompt_upsampling = job_data.get('promptUpsampling', False)
        safety_tolerance = job_data.get('safetyTolerance', 2)

        if not prompt:
            raise ValueError("Job is missing a prompt.")

        # Pass all the parameters to the BFL service
        image_data = generate_art_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            steps=steps,
            guidance=guidance,
            seed=seed,
            prompt_upsampling=prompt_upsampling,
            safety_tolerance=safety_tolerance
        )
        
        public_url = upload_image_to_storage(image_data)

        # Update the document with the results and new status
        job_ref.update({
            'generatedImageUrl': public_url,
            'status': 'pending_review',
            'generationCount': job_data.get('generationCount', 0) + 1
        })
        print(f"[{job_id}] Process complete. Status updated to pending_review.")

    except Exception as e:
        print(f"[{job_id}] ERROR: {e}")
        job_ref.update({'status': 'error', 'errorMessage': str(e)})

def start_worker():
    collection_ref = db.collection('jobs')
    query_ref = collection_ref.where('status', '==', 'pending_art_generation')
    query_ref.on_snapshot(callback)
    print("--- Worker is now listening for 'pending_art_generation' jobs... ---")
    while True:
        time.sleep(1)

def callback(collection_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'ADDED':
            process_job(change.document)