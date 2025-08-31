"""
Notion API Client Module
Handles HTTP requests with retry logic and rate limiting
"""
import time
import json
import requests
from typing import Dict, Any, Optional
from auth import NotionAuth

class NotionAPIClient:
    """HTTP client for Notion API with retry and rate limiting"""
    
    BASE_URL = "https://api.notion.com/v1"
    
    def __init__(self, auth: NotionAuth):
        self.auth = auth
        self.session = requests.Session()
        self.request_count = 0
        self.last_request_time = 0
        
    def _throttle(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Ensure at least 0.3 seconds between requests
        if time_since_last < 0.3:
            time.sleep(0.3 - time_since_last)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _retry_with_backoff(self, func, max_retries: int = 3):
        """Retry with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return func()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                print(f"Request failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    def request(self, method: str, endpoint: str, 
                data: Optional[Dict] = None, 
                files: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request with retry logic"""
        self._throttle()
        
        url = f"{self.BASE_URL}/{endpoint}"
        headers = self.auth.get_headers() if not files else self.auth.get_upload_headers()
        
        def make_request():
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                if files:
                    response = self.session.post(url, headers=headers, files=files)
                else:
                    response = self.session.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = self.session.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
        
        return self._retry_with_backoff(make_request)
    
    def create_page(self, parent_id: str, properties: Dict) -> Dict:
        """Create a new page"""
        data = {
            "parent": {"page_id": parent_id},
            "properties": properties
        }
        return self.request("POST", "pages", data)
    
    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """Update page properties"""
        return self.request("PATCH", f"pages/{page_id}", {"properties": properties})
    
    def append_blocks(self, block_id: str, children: list) -> Dict:
        """Append blocks to a page or block"""
        return self.request("PATCH", f"blocks/{block_id}/children", {"children": children})