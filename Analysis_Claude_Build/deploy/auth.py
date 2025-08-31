"""
Notion API Authentication Module
Handles token management and header construction
"""
import os
from typing import Dict, Optional

class NotionAuth:
    """Manages Notion API authentication"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize with token from environment or parameter"""
        self.token = token or os.getenv("NOTION_TOKEN")
        if not self.token:
            raise ValueError("NOTION_TOKEN environment variable not set")
        
        # Support both old (secret_) and new (ntn_) token formats
        if not (self.token.startswith("secret_") or self.token.startswith("ntn_")):
            raise ValueError("Invalid token format. Must start with 'secret_' or 'ntn_'")
        
        self.api_version = os.getenv("NOTION_VERSION", "2025-09-03")
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Notion API requests"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": self.api_version
        }
    
    def get_upload_headers(self) -> Dict[str, str]:
        """Get headers for file upload requests"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": self.api_version
            # Content-Type will be set automatically for multipart
        }