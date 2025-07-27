#!/usr/bin/env python3
"""
Fix the timestamps for historical requests to show they were all made today
"""
import random
from datetime import datetime, timezone, timedelta
import google.cloud.firestore as firestore
from dotenv import load_dotenv

load_dotenv()

def fix_historical_dates():
    """Update all historical requests to show they were made today"""
    
    db = firestore.Client()
    
    print("🔍 Finding historical cost records...")
    
    # Find all historical records
    costs_ref = db.collection('costs')
    query = costs_ref.where('details.imported_historical', '==', True)
    
    historical_docs = list(query.stream())
    
    if not historical_docs:
        print("❌ No historical records found")
        return
    
    print(f"📊 Found {len(historical_docs)} historical records to update")
    
    # Generate timestamps for today only
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = today + timedelta(days=1)
    
    updated_count = 0
    
    for doc in historical_docs:
        # Generate random time within today
        random_seconds = random.randint(0, int((end_of_day - today).total_seconds() - 1))
        new_timestamp = today + timedelta(seconds=random_seconds)
        
        # Update the document
        doc.reference.update({
            'timestamp': new_timestamp
        })
        
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"✅ Updated {updated_count}/{len(historical_docs)} records...")
    
    print(f"\n🎉 Successfully updated all {updated_count} historical records!")
    print(f"📅 All requests now show as made today ({today.strftime('%Y-%m-%d')})")
    print(f"\n🔍 View updated costs:")
    print(f"   - Frontend: 💰 Costs tab")
    print(f"   - CLI: python get_cost_summary.py")

if __name__ == "__main__":
    try:
        print("🔧 About to update historical request timestamps to today.")
        print("   This will make all 59 requests show as made today instead of spread over 30 days.")
        print("   Continue? (y/n): ", end="")
        
        if input().lower() == 'y':
            fix_historical_dates()
        else:
            print("❌ Cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")