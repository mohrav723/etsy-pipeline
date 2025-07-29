"""
Log sanitizer utility for removing sensitive information from logs.

This module provides functions to sanitize log data by removing or masking
sensitive information like API keys, URLs with tokens, and personal data.
"""

import re
import os
from typing import Any, Dict, List, Union, Set
from copy import deepcopy
import logging

logger = logging.getLogger(__name__)


class LogSanitizer:
    """Sanitizes log data by removing or masking sensitive information."""
    
    # Default sensitive field names to sanitize
    DEFAULT_SENSITIVE_FIELDS = {
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
        'auth', 'authorization', 'cookie', 'session', 'private_key', 'privatekey',
        'access_token', 'refresh_token', 'bearer', 'credentials', 'credit_card',
        'ssn', 'social_security', 'tax_id', 'bank_account', 'routing_number'
    }
    
    # Patterns to detect sensitive data
    PATTERNS = {
        # API Keys and tokens (generic pattern for alphanumeric strings)
        'api_key': re.compile(r'(?i)(api[_-]?key|token|bearer|auth)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9\-_]{20,})["\']?'),
        # URLs with potential tokens or keys
        'url_with_token': re.compile(r'(https?://[^\s]+[?&])(token|key|auth|api_key)=([^&\s]+)'),
        # Email addresses
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        # Credit card numbers (basic pattern)
        'credit_card': re.compile(r'\b(?:\d{4}[\s\-]?){3}\d{4}\b'),
        # Social Security Numbers
        'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        # Firebase/GCS URLs with specific paths
        'storage_url': re.compile(r'(https?://[^/]+/[^?]+)(\?[^\s]+)?'),
    }
    
    def __init__(self, 
                 sensitive_fields: Set[str] = None,
                 mask_char: str = '*',
                 mask_length: int = 8,
                 preserve_structure: bool = True):
        """
        Initialize the log sanitizer.
        
        Args:
            sensitive_fields: Set of field names to sanitize (case-insensitive)
            mask_char: Character to use for masking
            mask_length: Length of mask for replaced values
            preserve_structure: If True, preserve some structure (e.g., show first/last chars)
        """
        self.sensitive_fields = sensitive_fields or self.DEFAULT_SENSITIVE_FIELDS
        self.sensitive_fields = {field.lower() for field in self.sensitive_fields}
        self.mask_char = mask_char
        self.mask_length = mask_length
        self.preserve_structure = preserve_structure
        
        # Add fields from environment
        env_fields = os.getenv('LOG_SENSITIVE_FIELDS', '').split(',')
        self.sensitive_fields.update(field.strip().lower() for field in env_fields if field.strip())
    
    def mask_value(self, value: str, preserve_ends: bool = True) -> str:
        """
        Mask a sensitive value.
        
        Args:
            value: The value to mask
            preserve_ends: If True and preserve_structure is True, show first/last chars
            
        Returns:
            Masked value
        """
        if not value:
            return value
            
        value_str = str(value)
        
        if self.preserve_structure and preserve_ends and len(value_str) > 4:
            # Show first 2 and last 2 characters
            return f"{value_str[:2]}{self.mask_char * self.mask_length}{value_str[-2:]}"
        else:
            # Complete mask
            return self.mask_char * self.mask_length
    
    def sanitize_string(self, text: str) -> str:
        """
        Sanitize a string by applying pattern-based replacements.
        
        Args:
            text: The string to sanitize
            
        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            return text
        
        # Apply pattern replacements
        for pattern_name, pattern in self.PATTERNS.items():
            if pattern_name == 'api_key':
                # Special handling for API keys
                text = pattern.sub(lambda m: f"{m.group(1)}={self.mask_value(m.group(2))}", text)
            elif pattern_name == 'url_with_token':
                # Special handling for URLs with tokens
                text = pattern.sub(lambda m: f"{m.group(1)}{m.group(2)}={self.mask_value(m.group(3))}", text)
            elif pattern_name == 'email' and self.preserve_structure:
                # Partially mask emails
                text = pattern.sub(
                    lambda m: self._mask_email(m.group(0)),
                    text
                )
            elif pattern_name == 'storage_url':
                # Preserve base URL but mask query params
                text = pattern.sub(
                    lambda m: m.group(1) + (f"?{self.mask_value('params')}" if m.group(2) else ""),
                    text
                )
            else:
                # Complete replacement
                text = pattern.sub(self.mask_value(''), text)
        
        return text
    
    def _mask_email(self, email: str) -> str:
        """Mask email address while preserving structure."""
        if '@' not in email:
            return self.mask_value(email)
        
        local, domain = email.split('@', 1)
        if len(local) > 2:
            masked_local = f"{local[0]}{self.mask_char * 4}{local[-1]}"
        else:
            masked_local = self.mask_char * 4
        
        return f"{masked_local}@{domain}"
    
    def sanitize_dict(self, data: Dict[str, Any], depth: int = 0, max_depth: int = 10) -> Dict[str, Any]:
        """
        Recursively sanitize a dictionary.
        
        Args:
            data: Dictionary to sanitize
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized dictionary
        """
        if depth > max_depth:
            return {"_error": "Max depth exceeded"}
        
        if not isinstance(data, dict):
            return data
        
        # Create a copy to avoid modifying original
        sanitized = {}
        
        for key, value in data.items():
            # Check if key indicates sensitive data
            if any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                sanitized[key] = self.mask_value(str(value)) if value is not None else None
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                sanitized[key] = self.sanitize_dict(value, depth + 1, max_depth)
            elif isinstance(value, list):
                # Sanitize lists
                sanitized[key] = self.sanitize_list(value, depth + 1, max_depth)
            elif isinstance(value, str):
                # Sanitize string values
                sanitized[key] = self.sanitize_string(value)
            else:
                # Keep other types as-is
                sanitized[key] = value
        
        return sanitized
    
    def sanitize_list(self, data: List[Any], depth: int = 0, max_depth: int = 10) -> List[Any]:
        """
        Sanitize a list.
        
        Args:
            data: List to sanitize
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized list
        """
        if depth > max_depth:
            return ["_error: Max depth exceeded"]
        
        sanitized = []
        for item in data:
            if isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item, depth + 1, max_depth))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item, depth + 1, max_depth))
            elif isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            else:
                sanitized.append(item)
        
        return sanitized
    
    def sanitize(self, data: Any) -> Any:
        """
        Sanitize any data type.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        if isinstance(data, dict):
            return self.sanitize_dict(data)
        elif isinstance(data, list):
            return self.sanitize_list(data)
        elif isinstance(data, str):
            return self.sanitize_string(data)
        else:
            return data


# Global instance for convenience
_default_sanitizer = None


def get_sanitizer() -> LogSanitizer:
    """Get the default log sanitizer instance."""
    global _default_sanitizer
    if _default_sanitizer is None:
        _default_sanitizer = LogSanitizer()
    return _default_sanitizer


def sanitize_log_data(data: Any) -> Any:
    """
    Convenience function to sanitize log data using the default sanitizer.
    
    Args:
        data: Data to sanitize
        
    Returns:
        Sanitized data
    """
    return get_sanitizer().sanitize(data)


def configure_sanitizer(**kwargs) -> LogSanitizer:
    """
    Configure and return the global sanitizer instance.
    
    Args:
        **kwargs: Arguments to pass to LogSanitizer constructor
        
    Returns:
        Configured LogSanitizer instance
    """
    global _default_sanitizer
    _default_sanitizer = LogSanitizer(**kwargs)
    return _default_sanitizer