"""Type definitions for the Estate Planning Concierge v4.0 Asset Generation System.

This module provides comprehensive type hints and type aliases used throughout
the asset generation system, improving code maintainability and IDE support.
"""

from typing import (
    Dict, List, Optional, Tuple, Any, Union, Callable, 
    TypedDict, Protocol, Literal, TypeVar, Generic, 
    Awaitable, AsyncIterator, Iterator
)
from pathlib import Path
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

# Type Variables
T = TypeVar('T')
PathLike = Union[str, Path]

# Asset Types
AssetType = Literal['icons', 'covers', 'textures', 'letter_headers', 'database_icons']
GenerationMode = Literal['sample', 'production']
LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

# Configuration Types
class BudgetConfig(TypedDict):
    """Budget configuration type."""
    sample_limit: float
    production_limit: float
    daily_limit: float

class ModelConfig(TypedDict):
    """Model configuration type."""
    model_id: str
    cost_per_image: float
    timeout: int
    max_retries: int

class ReplicateConfig(TypedDict):
    """Replicate API configuration type."""
    api_key: Optional[str]
    rate_limit: float
    models: Dict[AssetType, ModelConfig]

class OutputConfig(TypedDict):
    """Output directory configuration type."""
    sample_directory: str
    production_directory: str
    backup_directory: str

class LoggingConfig(TypedDict):
    """Logging configuration type."""
    log_level: LogLevel
    log_file: str
    transaction_log: str
    max_log_size: int
    backup_count: int

class ReviewConfig(TypedDict):
    """Review server configuration type."""
    port: int
    host: str
    auto_open_browser: bool
    timeout: int

class ApplicationConfig(TypedDict):
    """Main application configuration type."""
    budget: BudgetConfig
    replicate: ReplicateConfig
    output: OutputConfig
    logging: LoggingConfig
    review: ReviewConfig

# Asset Generation Types
class AssetMetadata(TypedDict):
    """Metadata for a generated asset."""
    asset_type: AssetType
    prompt: str
    index: int
    total: int
    cost: float
    timestamp: datetime
    model_id: str
    output_url: Optional[str]
    filepath: Optional[Path]
    error: Optional[str]
    retry_count: int

class GenerationStats(TypedDict):
    """Statistics for generation run."""
    icons_generated: int
    covers_generated: int
    textures_generated: int
    regenerated_count: int
    total_cost: float
    generation_mode: GenerationMode

# Transaction Types
class Transaction(TypedDict):
    """Financial transaction record."""
    id: str
    timestamp: datetime
    asset_type: AssetType
    cost: float
    status: Literal['pending', 'completed', 'failed', 'rolled_back']
    prompt: Optional[str]
    output_url: Optional[str]
    error: Optional[str]

# API Response Types
class ReplicateResponse(TypedDict):
    """Replicate API response type."""
    id: str
    status: str
    output: Optional[Union[str, List[str]]]
    error: Optional[str]
    logs: Optional[str]

class OpenRouterResponse(TypedDict):
    """OpenRouter API response type."""
    id: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]
    model: str

# Error Types
class ErrorInfo(TypedDict):
    """Error information type."""
    error_type: str
    message: str
    timestamp: datetime
    context: Optional[Dict[str, Any]]
    stack_trace: Optional[str]

# Callback Types
ApiCallable = Callable[..., Awaitable[Any]]
DownloadCallable = Callable[[str], Awaitable[Path]]
ErrorHandler = Callable[[Exception], None]
ProgressCallback = Callable[[int, int], None]

# Protocol Definitions
class ResourceManager(Protocol):
    """Protocol for resource managers."""
    
    async def acquire(self) -> Any:
        """Acquire a resource."""
        ...
    
    async def release(self, resource: Any) -> None:
        """Release a resource."""
        ...
    
    async def cleanup(self) -> None:
        """Clean up all resources."""
        ...

class FileHandler(Protocol):
    """Protocol for file handlers."""
    
    async def read(self, path: PathLike) -> str:
        """Read file contents."""
        ...
    
    async def write(self, path: PathLike, content: str) -> None:
        """Write content to file."""
        ...
    
    async def delete(self, path: PathLike) -> None:
        """Delete a file."""
        ...

class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

# Validation Types
class ValidationResult(TypedDict):
    """Validation result type."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class PathValidationResult(TypedDict):
    """Path validation result type."""
    is_safe: bool
    sanitized_path: Optional[Path]
    error_message: Optional[str]

# Manifest Types
class ManifestEntry(TypedDict):
    """Asset manifest entry type."""
    filename: str
    asset_type: AssetType
    prompt: str
    cost: float
    timestamp: str
    model_used: str
    quality_score: Optional[float]
    file_size: Optional[int]

class GenerationManifest(TypedDict):
    """Complete generation manifest type."""
    assets: List[ManifestEntry]
    total_cost: float
    errors: List[ErrorInfo]
    timestamp: str
    production: bool
    total_generated: int
    total_expected: int
    generation_time: Optional[float]

# Rate Limiting Types
class RateLimitInfo(TypedDict):
    """Rate limit information type."""
    requests_per_second: float
    burst_capacity: int
    current_tokens: float
    last_update: float

# Session Types
class SessionInfo(TypedDict):
    """Session information type."""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_assets_generated: int
    total_cost: float
    errors_encountered: int

# Export all types
__all__ = [
    # Type Variables
    'T',
    'PathLike',
    
    # Literals
    'AssetType',
    'GenerationMode',
    'LogLevel',
    
    # Configuration Types
    'BudgetConfig',
    'ModelConfig',
    'ReplicateConfig',
    'OutputConfig',
    'LoggingConfig',
    'ReviewConfig',
    'ApplicationConfig',
    
    # Asset Types
    'AssetMetadata',
    'GenerationStats',
    
    # Transaction Types
    'Transaction',
    
    # API Types
    'ReplicateResponse',
    'OpenRouterResponse',
    
    # Error Types
    'ErrorInfo',
    
    # Callback Types
    'ApiCallable',
    'DownloadCallable',
    'ErrorHandler',
    'ProgressCallback',
    
    # Protocols
    'ResourceManager',
    'FileHandler',
    
    # Enums
    'CircuitBreakerState',
    
    # Validation Types
    'ValidationResult',
    'PathValidationResult',
    
    # Manifest Types
    'ManifestEntry',
    'GenerationManifest',
    
    # Rate Limiting
    'RateLimitInfo',
    
    # Session
    'SessionInfo',
]