import os
import time
from dotenv import load_dotenv
import google.cloud.firestore

# --- Setup & Initialization ---
load_dotenv()
db = google.cloud.firestore.Client()

# --- Core Worker Logic ---
def process_job(doc_snapshot):
    job_id = doc_snapshot.id
    job_data = doc_snapshot.to_dict()
    print(f"[{job_id}] Received new job with status: {job_data.get('status')}")
    # We will add the AI logic here in the next step

def listen_for_jobs():
    """
    Listens to the 'jobs' collection and triggers processing for new jobs.
    """
    collection_ref = db.collection('jobs')
    
    # --- THIS IS THE FIX ---
    # Update the query to listen for the correct status from the frontend.
    query_ref = collection_ref.where('status', '==', 'pending_prompt_generation')

    # watch() creates a real-time listener
    query_ref.on_snapshot(callback)

    print("--- Worker is now listening for 'pending_prompt_generation' jobs... ---")
    
    while True:
        time.sleep(1)

def callback(collection_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == 'ADDED':
            process_job(change.document)

# --- Main Execution ---
if __name__ == "__main__":
    listen_for_jobs()