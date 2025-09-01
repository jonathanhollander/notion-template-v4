"""
Authentication Module
Handles Notion API token validation and authentication
"""

import logging
import requests

logger = logging.getLogger(__name__)

def validate_token(token: str) -> bool:
    """Validate Notion API token format"""
    if not token:
        return False
    # Support both old and new token formats
    return token.startswith("secret_") or token.startswith("ntn_")

def validate_token_with_api(token: str, base_url: str, notion_api_version: str) -> bool:
    """Validate Notion API token with the API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": notion_api_version
    }
    response = requests.get(f"{base_url}/users/me", headers=headers)
    return response.status_code == 200