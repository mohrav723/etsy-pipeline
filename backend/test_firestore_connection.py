import os
import sys
from dotenv import load_dotenv
import google.cloud.firestore as firestore

# Load environment
load_dotenv()

# Test Firestore connection
try:
    db = firestore.Client()
    print("✅ Connected to Firestore successfully")
    
    # Check intelligent mockup jobs
    collection = db.collection('intelligent_mockup_jobs')
    query = collection.where(filter=firestore.FieldFilter('status', '==', 'pending'))
    docs = list(query.stream())
    
    print(f"📋 Found {len(docs)} pending intelligent mockup jobs")
    
    for doc in docs:
        data = doc.to_dict()
        print(f"  - Job ID: {doc.id}, Status: {data.get('status')}")
        
except Exception as e:
    print(f"❌ Error connecting to Firestore: {e}")
    print("Make sure your Firebase credentials are properly configured")