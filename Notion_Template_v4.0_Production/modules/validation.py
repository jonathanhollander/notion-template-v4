"""
Validation Module
Handles input sanitization and validation for security and data integrity
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def sanitize_input(value: Any) -> str:
    """Sanitize input to prevent injection attacks and ensure safe processing"""
    if value is None:
        return ""
    
    # Convert to string
    str_value = str(value)
    
    # Remove potentially dangerous characters
    # Keep alphanumeric, spaces, basic punctuation
    sanitized = re.sub(r'[^\w\s\-\.,!?@#$%&*()+=\[\]{}|\\:";\'<>/~`]', '', str_value)
    
    # Limit length to prevent excessive data
    if len(sanitized) > 1000:
        sanitized = sanitized[:1000]
        logger.warning(f"Input truncated to 1000 characters")
    
    return sanitized.strip()

def check_role_permission(user_role: str, required_permissions: List[str]) -> bool:
    """Check if user role has required permissions"""
    role_permissions = {
        "admin": ["read", "write", "delete", "manage", "configure"],
        "editor": ["read", "write"],
        "viewer": ["read"],
        "guest": []
    }
    
    if user_role not in role_permissions:
        logger.warning(f"Unknown user role: {user_role}")
        return False
    
    user_permissions = role_permissions[user_role]
    return all(perm in user_permissions for perm in required_permissions)

def filter_content_by_role(content: Dict, user_role: str) -> Dict:
    """Filter content based on user role permissions"""
    if user_role == "admin":
        return content  # Admin sees everything
    
    filtered_content = content.copy()
    
    # Remove sensitive fields for non-admin users
    sensitive_fields = ["api_keys", "internal_notes", "admin_settings"]
    for field in sensitive_fields:
        if field in filtered_content:
            del filtered_content[field]
    
    # Additional filtering for guest users
    if user_role == "guest":
        guest_restricted = ["edit_history", "user_data", "statistics"]
        for field in guest_restricted:
            if field in filtered_content:
                del filtered_content[field]
    
    return filtered_content