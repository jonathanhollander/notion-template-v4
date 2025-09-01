"""
Custom Exception Classes for Estate Planning Concierge
Provides specific exception types for better error handling
"""

class ConfigurationError(Exception):
    """Raised when there's an issue with configuration loading or validation"""
    pass

class NotionAPIError(Exception):
    """Raised when Notion API requests fail"""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body

class ValidationError(Exception):
    """Raised when input validation fails"""
    pass

class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass

class RateLimitExceededError(Exception):
    """Raised when rate limits are exceeded"""
    pass

class DatabaseOperationError(Exception):
    """Raised when database operations fail"""
    pass