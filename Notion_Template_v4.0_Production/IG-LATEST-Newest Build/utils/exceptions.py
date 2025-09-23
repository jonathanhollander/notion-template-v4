"""Custom exception types for the image generation system."""


class ImageGenerationError(Exception):
    """Base exception for image generation errors."""
    pass


class BudgetExceededError(ImageGenerationError):
    """Raised when an operation would exceed the budget limit."""
    pass


class APIError(ImageGenerationError):
    """Base exception for API-related errors."""
    pass


class ReplicateAPIError(APIError):
    """Raised when Replicate API calls fail."""
    pass


class OpenRouterAPIError(APIError):
    """Raised when OpenRouter API calls fail."""
    pass


class NetworkError(ImageGenerationError):
    """Raised when network operations fail."""
    pass


class ImageDownloadError(NetworkError):
    """Raised when image download fails."""
    pass


class ValidationError(ImageGenerationError):
    """Raised when input validation fails."""
    pass


class PathTraversalError(ValidationError):
    """Raised when path traversal is attempted."""
    pass


class TransactionError(ImageGenerationError):
    """Raised when transaction operations fail."""
    pass


class RollbackError(TransactionError):
    """Raised when transaction rollback fails."""
    pass