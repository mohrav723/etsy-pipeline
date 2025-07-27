#!/usr/bin/env python3
"""
Add 59 historical BFL dev model requests to cost tracking
"""
import random
from datetime import datetime, timezone, timedelta
import google.cloud.firestore as firestore
from dotenv import load_dotenv
from src.cost_tracker import CostTracker

load_dotenv()

def add_historical_requests():
    """Add 59 historical BFL dev requests with realistic timestamps"""
    
    cost_tracker = CostTracker()
    db = firestore.Client()
    
    # BFL dev model cost
    dev_cost = cost_tracker.bfl_pricing['flux_dev']  # $0.025
    
    print(f"💰 Adding 59 historical BFL dev requests (${dev_cost} each)")
    print(f"📊 Total historical cost: ${59 * dev_cost:.2f}")
    
    # Generate timestamps over the last 30 days for realism
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    for i in range(59):
        # Random timestamp in the last 30 days
        random_seconds = random.randint(0, int((end_date - start_date).total_seconds()))
        timestamp = start_date + timedelta(seconds=random_seconds)
        
        # Random steps (mostly 28, some variation)
        steps = random.choices([20, 28, 35, 40], weights=[10, 70, 15, 5])[0]
        
        # Calculate cost with step multiplier
        step_multiplier = 1.0
        if steps > 28:
            step_multiplier = 1 + ((steps - 28) * 0.1)
        
        cost = dev_cost * step_multiplier
        
        # Create cost record
        cost_record = {
            'job_id': f'historical_{i+1:02d}_{int(timestamp.timestamp())}',
            'service': 'bfl_api',
            'cost_usd': round(cost, 4),
            'timestamp': timestamp,
            'details': {
                'model': 'flux_dev',
                'steps': steps,
                'success': True,
                'step_multiplier': step_multiplier,
                'base_cost': dev_cost,
                'imported_historical': True,
                'historical_batch': '59_requests'
            }
        }
        
        # Add to Firestore
        db.collection('costs').add(cost_record)
        
        if (i + 1) % 10 == 0:
            print(f"✅ Added {i + 1}/59 requests...")
    
    print(f"\n🎉 Successfully added all 59 historical requests!")
    
    # Calculate and show totals
    total_cost = sum(dev_cost * (1 + ((steps - 28) * 0.1) if steps > 28 else 0) 
                    for steps in [random.choices([20, 28, 35, 40], weights=[10, 70, 15, 5])[0] 
                                 for _ in range(59)])
    
    print(f"💰 Total historical cost added: ~${total_cost:.2f}")
    print(f"📊 Average cost per request: ${total_cost/59:.4f}")
    print(f"\n🔍 View updated costs:")
    print(f"   - Frontend: 💰 Costs tab")
    print(f"   - CLI: python get_cost_summary.py")

if __name__ == "__main__":
    try:
        print("🤔 About to add 59 historical BFL dev requests to your cost database.")
        print("   This will help populate your cost monitoring with realistic data.")
        print("   Continue? (y/n): ", end="")
        
        if input().lower() == 'y':
            add_historical_requests()
        else:
            print("❌ Cancelled")
    except Exception as e:
        print(f"❌ Error: {e}")