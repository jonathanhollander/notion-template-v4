"""
Notion API Client Module
Handles core API communication, rate limiting, and session management
"""

import time
import logging
from typing import Dict, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Rate limiting state
_last_request_time = [0.0]

def throttle(rate_limit_rps: float):
    """Implement rate limiting at specified requests per second"""
    if rate_limit_rps <= 0:
        return
    min_interval = 1.0 / rate_limit_rps
    now = time.time()
    elapsed = now - _last_request_time[0]
    if elapsed < min_interval:
        sleep_time = min_interval - elapsed
        time.sleep(sleep_time)
    _last_request_time[0] = time.time()

def create_session(max_retries: int = 5, backoff_base: float = 1.5) -> requests.Session:
    """Create a requests session with retry strategy"""
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PATCH"],
        backoff_factor=backoff_base
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def req(method: str, url: str, headers: Dict = None, data: str = None, 
        files=None, timeout: int = None, session=None, rate_limit_rps: float = 2.5,
        notion_api_version: str = "2022-06-28") -> requests.Response:
    """
    Make a request to Notion API with proper error handling and rate limiting
    """
    throttle(rate_limit_rps)  # Apply rate limiting
    
    headers = headers or {}
    
    # Set required headers
    if "Notion-Version" not in headers:
        headers["Notion-Version"] = notion_api_version
    
    # Use provided session or create default one
    if session is None:
        session = requests
    
    try:
        if method.upper() == "GET":
            response = session.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            if files:
                response = session.post(url, headers=headers, files=files, timeout=timeout)
            else:
                response = session.post(url, headers=headers, data=data, timeout=timeout)
        elif method.upper() == "PATCH":
            response = session.patch(url, headers=headers, data=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = session.delete(url, headers=headers, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {method} {url} - {e}")
        raise

def expect_ok(response: requests.Response) -> Dict:
    """Validate response status and return JSON data"""
    if response.status_code not in [200, 201]:
        logger.error(f"API request failed with status {response.status_code}: {response.text}")
        raise requests.exceptions.HTTPError(f"API request failed with status {response.status_code}")
    
    try:
        return response.json()
    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return {}

def j(response: requests.Response) -> Dict:
    """Extract JSON from response with error handling"""
    try:
        return response.json()
    except Exception as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return {}