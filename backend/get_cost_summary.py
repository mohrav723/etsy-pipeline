#!/usr/bin/env python3
"""
Cost summary script - can be run manually or as an API endpoint
"""
import sys
import json
from src.cost_tracker import CostTracker

def main():
    """Get cost summary for different periods"""
    cost_tracker = CostTracker()
    
    # Get summaries for different periods
    summary_7_days = cost_tracker.get_cost_summary(days=7)
    summary_30_days = cost_tracker.get_cost_summary(days=30)
    
    result = {
        'last_7_days': summary_7_days,
        'last_30_days': summary_30_days,
        'status': 'success'
    }
    
    # If called with --json, output JSON for API use
    if '--json' in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        # Human-readable output
        print("🏷️  COST SUMMARY")
        print("=" * 50)
        
        print(f"\n📊 Last 7 Days:")
        print(f"   Total: ${summary_7_days['total_cost_usd']:.4f}")
        print(f"   BFL API: ${summary_7_days['bfl_api']['cost_usd']:.4f} ({summary_7_days['bfl_api']['count']} requests)")
        print(f"   Storage: ${summary_7_days['google_storage']['cost_usd']:.6f} ({summary_7_days['google_storage']['count']} ops)")
        
        print(f"\n📊 Last 30 Days:")
        print(f"   Total: ${summary_30_days['total_cost_usd']:.4f}")
        print(f"   BFL API: ${summary_30_days['bfl_api']['cost_usd']:.4f} ({summary_30_days['bfl_api']['count']} requests)")
        print(f"   Storage: ${summary_30_days['google_storage']['cost_usd']:.6f} ({summary_30_days['google_storage']['count']} ops)")
        
        if summary_30_days['total_cost_usd'] > 10:
            print(f"\n⚠️  WARNING: High usage detected!")
        elif summary_30_days['total_cost_usd'] > 5:
            print(f"\n💡 INFO: Consider monitoring usage closely")
        else:
            print(f"\n✅ INFO: Costs are reasonable")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if '--json' in sys.argv:
            print(json.dumps({'error': str(e), 'status': 'error'}))
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)