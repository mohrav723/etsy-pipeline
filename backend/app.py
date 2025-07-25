import os
import time
from dotenv import load_dotenv
import google.cloud.firestore

# --- Setup & Initialization ---

# Load environment variables from .env file (for GOOGLE_APPLICATION_CREDENTIALS)
load_dotenv()

# Authenticate to Firestore
# This uses the GOOGLE_APPLICATION_CREDENTIALS environment variable automatically
db = google.cloud.firestore.Client()

# --- Core Worker Logic ---

def process_job(doc_snapshot):
    """
    Processes a single job document from Firestore.
    """
    job_id = doc_snapshot.id
    job_data = doc_snapshot.to_dict()

    # Right now, we'll just print the job details.
    # In future steps, this is where you'll call the Flux API, etc.
    print(f"[{job_id}] Received new job with status: {job_data.get('status')}")
    print(f"   > Prompt: {job_data.get('prompt')}")

def listen_for_jobs():
    """
    Listens to the 'jobs' collection and triggers processing for new jobs.
    """
    # Create a query to find jobs that need to be processed
    # For now, let's just listen for jobs with the status 'pending_generation'
    collection_ref = db.collection('jobs')
    query_ref = collection_ref.where('status', '==', 'pending_generation')

    # watch() creates a real-time listener
    snapshot = query_ref.on_snapshot(callback)

    print("--- Worker is now listening for jobs... ---")
    
    # Keep the script running to continue listening
    while True:
        time.sleep(1)

def callback(collection_snapshot, changes, read_time):
    """
    This function is called every time there's a change in the query results.
    """
    for change in changes:
        # We only care about new documents being added
        if change.type.name == 'ADDED':
            process_job(change.document)

# --- Main Execution ---

if __name__ == "__main__":
    listen_for_jobs()