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

# Import the enhanced logging system
try:
    from .logging_config import APIRequestLogger
except ImportError:
    # Fallback for testing or standalone usage
    APIRequestLogger = None

# Check if we should use simple unified logging
import os
use_simple_logging = os.getenv('USE_SIMPLE_LOGGING', '').lower() in ('true', '1', 'yes')

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
    Make a request to Notion API with comprehensive logging and error handling
    """
    # Initialize API logger for this request
    if use_simple_logging:
        # Use simple unified logging
        api_logger = None
    else:
        api_logger = APIRequestLogger() if APIRequestLogger else None

    throttle(rate_limit_rps)  # Apply rate limiting

    headers = headers or {}

    # Set required headers
    if "Notion-Version" not in headers:
        headers["Notion-Version"] = notion_api_version

    # Use provided session or create default one
    if session is None:
        session = requests

    # Log the outgoing request
    if api_logger:
        api_logger.log_request(method, url, headers, data, files)

    # Log API requests for unified color-coded logging
    logger.info(f"API_REQUEST {method.upper()} {url}")
    if data:
        payload_preview = str(data)[:200] + ('...' if len(str(data)) > 200 else '')
        logger.debug(f"API_REQUEST payload: {payload_preview}")
    if files:
        logger.debug(f"API_REQUEST includes files: {list(files.keys()) if files else 'none'}")

    try:
        # Make the actual HTTP request
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

        # Log the response
        success = response.status_code in [200, 201]

        if api_logger:
            api_logger.log_response(response, success)

        # Log API responses for unified color-coded logging
        logger.info(f"API_RESPONSE {response.status_code} - {len(response.text)} chars")
        if success:
            response_preview = response.text[:300] + ('...' if len(response.text) > 300 else '')
            logger.debug(f"API_RESPONSE content: {response_preview}")
        else:
            logger.error(f"API_RESPONSE error: {response.text[:500]}")

        return response

    except requests.exceptions.RequestException as e:
        # Log the exception
        if api_logger:
            # Create a mock error response for logging
            class ErrorResponse:
                def __init__(self, error):
                    self.status_code = 500
                    self.text = str(error)

            api_logger.log_response(ErrorResponse(e), success=False)

        logger.error(f"Request failed: {method} {url} - {e}")
        raise

def expect_ok(response: requests.Response, context: str = "API request") -> Dict:
    """Validate response status and return JSON data with enhanced error logging"""
    if response.status_code not in [200, 201]:
        # Log detailed error information
        error_info = {
            'context': context,
            'status_code': response.status_code,
            'url': response.url,
            'headers': dict(response.headers),
            'response_text': response.text[:1000]  # Limit to first 1000 chars
        }

        logger.error(f"{context} failed with status {response.status_code}")
        logger.error(f"URL: {response.url}")
        logger.error(f"Response: {response.text}")

        # Try to parse error details from JSON response
        try:
            error_json = response.json()
            if 'message' in error_json:
                logger.error(f"Notion API Error: {error_json['message']}")
            if 'code' in error_json:
                logger.error(f"Error Code: {error_json['code']}")
        except:
            pass

        raise requests.exceptions.HTTPError(f"{context} failed with status {response.status_code}")

    try:
        json_data = response.json()
        logger.debug(f"{context} successful - Response keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'non-dict response'}")
        return json_data
    except ValueError as e:
        logger.error(f"Failed to parse JSON response for {context}: {e}")
        logger.error(f"Raw response: {response.text}")
        return {}


def j(response: requests.Response) -> Dict:
    """Extract JSON from response with enhanced error handling and logging"""
    try:
        json_data = response.json()

        # Log useful response information
        if isinstance(json_data, dict):
            if 'object' in json_data:
                logger.debug(f"Response object type: {json_data['object']}")
            if 'results' in json_data and isinstance(json_data['results'], list):
                logger.debug(f"Results count: {len(json_data['results'])}")
            if 'has_more' in json_data:
                logger.debug(f"Has more results: {json_data['has_more']}")

        return json_data
    except Exception as e:
        logger.warning(f"Failed to parse JSON response: {e}")
        logger.debug(f"Raw response text: {response.text[:500]}{'...' if len(response.text) > 500 else ''}")
        return {}