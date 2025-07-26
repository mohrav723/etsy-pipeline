import os
import time
import uuid
from dotenv import load_dotenv
import google.cloud.firestore
from google.cloud import storage

# --- THIS IS THE FIX ---
# The '.' makes this a relative import, looking inside the 'src' package.
from .services.bfl_api import generate_art_image

# --- Setup & Initialization ---
load_dotenv()
db = google.cloud.firestore.Client()
storage_client = storage.Client()
BUCKET_NAME = os.getenv("FIREBASE_STORAGE_BUCKET")
if not BUCKET_NAME:
    raise ValueError("FIREBASE_STORAGE_BUCKET not found in .env file.")
bucket = storage_client.bucket(BUCKET_NAME)


# --- Helper Function ---
def upload_image_to_storage(image_data: bytes) -> str:
    """Uploads image data to Firebase Storage and returns the public URL."""
    image_name = f"generated-art/{uuid.uuid4()}.png"
    blob = bucket.blob(image_name)
    
    print(f"--- Uploading image to: {image_name}")
    blob.upload_from_string(image_data, content_type='image/png')
    blob.make_public()
    
    print(f"--- Upload complete. Public URL: {blob.public_url}")
    return blob.public_url

# --- Core Worker Logic ---
def process_job(doc_snapshot):
    job_id = doc_snapshot.id
    job_data = doc_snapshot.to_dict()
    job_ref = db.collection('jobs').document(job_id)

    print(f"[{job_id}] Received job with status: {job_data.get('status')}")
    
    try:
        prompt = job_data.get('prompt')
        if not prompt:
            raise ValueError("Job is missing a prompt.")

        image_data = generate_art_image(prompt=prompt)
        public_url = upload_image_to_storage(image_data)

        job_ref.update({
            'generatedImageUrl': public_url,
            'status': 'pending_review'
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