"""
Estate Planning Concierge v4.0 - Modular Architecture
Refactored modules for better maintainability and organization
"""

from .config import initialize_config, load_config, validate_config
from .auth import validate_token, validate_token_with_api
from .notion_api import req, expect_ok, j, throttle, create_session
from .validation import sanitize_input, check_role_permission, filter_content_by_role
from .database import create_database_entry, update_rollup_properties, complete_database_relationships

__version__ = "4.0.0"
__all__ = [
    "initialize_config", "load_config", "validate_config",
    "validate_token", "validate_token_with_api", 
    "req", "expect_ok", "j", "throttle", "create_session",
    "sanitize_input", "check_role_permission", "filter_content_by_role",
    "create_database_entry", "update_rollup_properties", "complete_database_relationships"
]