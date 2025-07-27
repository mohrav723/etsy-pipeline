"""
Cost tracking module for monitoring BFL API and Google Cloud Storage costs
"""
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import google.cloud.firestore as firestore
from dotenv import load_dotenv

load_dotenv()

class CostTracker:
    def __init__(self):
        self.db = firestore.Client()
        
        # BFL API Pricing (update these based on current BFL pricing)
        self.bfl_pricing = {
            'flux_pro': 0.05,      # $0.05 per image
            'flux_dev': 0.025,     # $0.025 per image  
            'flux_schnell': 0.01,  # $0.01 per image
            'default': 0.025       # Default to dev pricing
        }
        
        # Google Cloud Storage pricing (approximate)
        self.storage_pricing = {
            'storage_per_gb_month': 0.020,  # $0.020 per GB/month
            'operations_per_1k': 0.005,     # $0.005 per 1,000 operations
            'network_egress_per_gb': 0.12   # $0.12 per GB (first 1GB free)
        }

    def log_bfl_cost(self, job_id: str, model: str = 'default', steps: int = 28, 
                     success: bool = True, error_message: Optional[str] = None) -> float:
        """
        Log BFL API cost for an image generation
        
        Args:
            job_id: The job ID
            model: The model used (flux_pro, flux_dev, flux_schnell)
            steps: Number of steps (affects cost for some models)
            success: Whether the generation was successful
            error_message: Error message if failed
            
        Returns:
            Cost in USD
        """
        base_cost = self.bfl_pricing.get(model, self.bfl_pricing['default'])
        
        # Some models might have step-based pricing adjustments
        step_multiplier = 1.0
        if steps > 28:  # Higher steps might cost more
            step_multiplier = 1 + ((steps - 28) * 0.1)  # 10% more per 10 extra steps
        
        cost = base_cost * step_multiplier
        
        # Failed requests might still incur costs
        if not success:
            cost = cost * 0.5  # Half cost for failed requests
        
        cost_record = {
            'job_id': job_id,
            'service': 'bfl_api',
            'cost_usd': round(cost, 4),
            'timestamp': firestore.SERVER_TIMESTAMP,
            'details': {
                'model': model,
                'steps': steps,
                'success': success,
                'step_multiplier': step_multiplier,
                'base_cost': base_cost
            }
        }
        
        if error_message:
            cost_record['details']['error'] = error_message
        
        # Store in costs collection
        self.db.collection('costs').add(cost_record)
        
        # Also update the job document with cost info
        try:
            job_ref = self.db.collection('jobs').document(job_id)
            job_ref.update({
                'bfl_cost_usd': cost,
                'bfl_model': model,
                'bfl_steps': steps
            })
        except Exception as e:
            print(f"Warning: Could not update job {job_id} with cost info: {e}")
        
        return cost

    def log_storage_cost(self, job_id: str, image_size_bytes: int, 
                        operation_type: str = 'upload') -> float:
        """
        Log Google Cloud Storage cost
        
        Args:
            job_id: The job ID
            image_size_bytes: Size of the image in bytes
            operation_type: Type of operation (upload, download, etc.)
            
        Returns:
            Estimated cost in USD
        """
        # Convert bytes to GB
        size_gb = image_size_bytes / (1024 * 1024 * 1024)
        
        # Calculate storage cost (prorated for a month)
        # This is very rough - actual billing is more complex
        storage_cost = size_gb * self.storage_pricing['storage_per_gb_month'] / 30  # Daily rate
        
        # Operation cost
        operation_cost = self.storage_pricing['operations_per_1k'] / 1000
        
        total_cost = storage_cost + operation_cost
        
        cost_record = {
            'job_id': job_id,
            'service': 'google_storage',
            'cost_usd': round(total_cost, 6),
            'timestamp': firestore.SERVER_TIMESTAMP,
            'details': {
                'image_size_bytes': image_size_bytes,
                'image_size_gb': round(size_gb, 6),
                'operation_type': operation_type,
                'storage_cost': round(storage_cost, 6),
                'operation_cost': round(operation_cost, 6)
            }
        }
        
        # Store in costs collection
        self.db.collection('costs').add(cost_record)
        
        # Update job document
        try:
            job_ref = self.db.collection('jobs').document(job_id)
            job_ref.update({
                'storage_cost_usd': total_cost,
                'image_size_bytes': image_size_bytes
            })
        except Exception as e:
            print(f"Warning: Could not update job {job_id} with storage cost: {e}")
        
        return total_cost

    def get_cost_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get cost summary for the last N days
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with cost breakdown
        """
        from datetime import timedelta
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Query costs
        costs_ref = self.db.collection('costs')
        costs_query = costs_ref.where('timestamp', '>=', start_date).where('timestamp', '<=', end_date)
        
        bfl_total = 0
        storage_total = 0
        bfl_count = 0
        storage_count = 0
        
        for doc in costs_query.stream():
            data = doc.data()
            if data['service'] == 'bfl_api':
                bfl_total += data['cost_usd']
                bfl_count += 1
            elif data['service'] == 'google_storage':
                storage_total += data['cost_usd']
                storage_count += 1
        
        total_cost = bfl_total + storage_total
        
        return {
            'period_days': days,
            'total_cost_usd': round(total_cost, 4),
            'bfl_api': {
                'cost_usd': round(bfl_total, 4),
                'count': bfl_count,
                'avg_per_request': round(bfl_total / max(bfl_count, 1), 4)
            },
            'google_storage': {
                'cost_usd': round(storage_total, 6),
                'count': storage_count,
                'avg_per_operation': round(storage_total / max(storage_count, 1), 6)
            },
            'generated_at': datetime.now(timezone.utc).isoformat()
        }

