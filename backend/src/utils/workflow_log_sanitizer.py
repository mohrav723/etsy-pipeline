"""
Workflow-safe log sanitizer for Temporal workflows.

This module provides a simplified log sanitizer that doesn't use os.getenv
or other restricted functions, making it safe to use within Temporal workflows.
"""

import re
from typing import Any, Dict, List, Union, Set
from copy import deepcopy


class WorkflowSafeLogSanitizer:
    """
    A simplified log sanitizer that's safe to use in Temporal workflows.
    
    This version doesn't use os.getenv or other restricted functions.
    """
    
    # Default sensitive field names to sanitize (hardcoded for workflow safety)
    DEFAULT_SENSITIVE_FIELDS = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
        'auth', 'authorization', 'cookie', 'session', 'private_key', 'privatekey',
        'access_token', 'refresh_token', 'bearer', 'credentials', 'credit_card',
        'ssn', 'social_security', 'tax_id', 'bank_account', 'routing_number',
        # Project-specific fields
        'bfl_api_key', 'firebase_storage_bucket', 'artwork_url', 'template_url', 'imageurl'
    }
    
    def __init__(self, mask_char: str = '*', mask_length: int = 8):
        """Initialize the workflow-safe sanitizer."""
        self.sensitive_fields = {field.lower() for field in self.DEFAULT_SENSITIVE_FIELDS}
        self.mask_char = mask_char
        self.mask_length = mask_length
        
        # Compile patterns once for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for sensitive data detection."""
        self.patterns = {
            # API Keys and tokens
            'api_key': re.compile(
                r'(?i)(api[_-]?key|token|bearer|auth)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?'
            ),
            # URLs with tokens
            'url_with_token': re.compile(
                r'(https?://[^\s]+[?&])(token|key|auth|api_key)=([^&\s]+)'
            ),
            # Storage URLs
            'storage_url': re.compile(
                r'(https?://[^/]+/[^?]+)(\?[^\s]+)?'
            ),
        }
    
    def mask_value(self, value: str, preserve_ends: bool = True) -> str:
        """Mask a sensitive value."""
        if not value:
            return value
            
        value_str = str(value)
        
        if preserve_ends and len(value_str) > 4:
            # Show first 2 and last 2 characters
            return f"{value_str[:2]}{self.mask_char * self.mask_length}{value_str[-2:]}"
        else:
            # Complete mask
            return self.mask_char * self.mask_length
    
    def sanitize_string(self, text: str) -> str:
        """Sanitize a string by applying pattern-based replacements."""
        if not isinstance(text, str):
            return text
        
        # Apply pattern replacements
        for pattern_name, pattern in self.patterns.items():
            if pattern_name == 'api_key':
                text = pattern.sub(
                    lambda m: f"{m.group(1)}={self.mask_value(m.group(2))}", 
                    text
                )
            elif pattern_name == 'url_with_token':
                text = pattern.sub(
                    lambda m: f"{m.group(1)}{m.group(2)}={self.mask_value(m.group(3))}", 
                    text
                )
            elif pattern_name == 'storage_url':
                text = pattern.sub(
                    lambda m: m.group(1) + (f"?{self.mask_value('params')}" if m.group(2) else ""),
                    text
                )
        
        return text
    
    def sanitize_dict(self, data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
        """Recursively sanitize a dictionary."""
        if depth > 10:  # Prevent infinite recursion
            return {"_error": "Max depth exceeded"}
        
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        for key, value in data.items():
            # Check if key indicates sensitive data
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.sensitive_fields):
                sanitized[key] = self.mask_value(str(value)) if value is not None else None
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_dict(value, depth + 1)
            elif isinstance(value, list):
                sanitized[key] = self.sanitize_list(value, depth + 1)
            elif isinstance(value, str):
                sanitized[key] = self.sanitize_string(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def sanitize_list(self, data: List[Any], depth: int = 0) -> List[Any]:
        """Sanitize a list."""
        if depth > 10:
            return ["_error: Max depth exceeded"]
        
        sanitized = []
        for item in data:
            if isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item, depth + 1))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item, depth + 1))
            elif isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def sanitize(self, data: Any) -> Any:
        """Sanitize any data type."""
        if isinstance(data, dict):
            return self.sanitize_dict(data)
        elif isinstance(data, list):
            return self.sanitize_list(data)
        elif isinstance(data, str):
            return self.sanitize_string(data)
        else:
            return data


# Create a singleton instance for workflow use
_workflow_sanitizer = WorkflowSafeLogSanitizer()


def sanitize_for_workflow(data: Any) -> Any:
    """
    Sanitize data for use in workflows.
    
    This function is safe to use in Temporal workflows as it doesn't
    access any restricted functions like os.getenv.
    """
    return _workflow_sanitizer.sanitize(data)