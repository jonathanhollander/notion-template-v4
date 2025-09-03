"""Pydantic models for configuration and validation."""

from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime


class BudgetConfig(BaseModel):
    """Budget configuration model."""
    model_config = ConfigDict(extra='forbid')
    
    sample_limit: float = Field(
        default=1.0, 
        gt=0, 
        le=10.0,
        description="Maximum budget for sample generation in dollars"
    )
    production_limit: float = Field(
        default=25.0,
        gt=0,
        le=100.0,
        description="Maximum budget for production generation in dollars"
    )
    daily_limit: float = Field(
        default=50.0,
        gt=0,
        le=200.0,
        description="Maximum daily spending limit in dollars"
    )
    
    @validator('production_limit')
    def production_must_exceed_sample(cls, v, values):
        if 'sample_limit' in values and v <= values['sample_limit']:
            raise ValueError('Production limit must exceed sample limit')
        return v


class ModelConfig(BaseModel):
    """Model configuration for image generation."""
    model_config = ConfigDict(extra='forbid')
    
    model_id: str = Field(
        ...,
        min_length=1,
        description="Replicate model ID"
    )
    cost_per_image: float = Field(
        ...,
        gt=0,
        le=1.0,
        description="Cost per image in dollars"
    )
    timeout: int = Field(
        default=60,
        gt=0,
        le=300,
        description="API timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )


class ReplicateConfig(BaseModel):
    """Replicate API configuration."""
    model_config = ConfigDict(extra='forbid')
    
    api_key: Optional[str] = Field(
        default=None,
        description="Replicate API key (can use environment variable)"
    )
    rate_limit: float = Field(
        default=2.0,
        gt=0,
        le=10.0,
        description="Requests per second rate limit"
    )
    models: Dict[str, ModelConfig] = Field(
        ...,
        description="Model configurations by asset type"
    )
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if v and not v.startswith('${') and len(v) < 10:
            raise ValueError('Invalid API key format')
        return v


class OutputConfig(BaseModel):
    """Output directory configuration."""
    model_config = ConfigDict(extra='forbid')
    
    sample_directory: str = Field(
        default="output/samples",
        description="Directory for sample images"
    )
    production_directory: str = Field(
        default="output/production",
        description="Directory for production images"
    )
    backup_directory: str = Field(
        default="output/backup",
        description="Directory for backups"
    )
    
    @validator('*')
    def validate_directory_path(cls, v):
        # Basic validation - no absolute paths or traversal
        if v.startswith('/') or '..' in v:
            raise ValueError(f'Invalid directory path: {v}')
        return v


class LoggingConfig(BaseModel):
    """Logging configuration."""
    model_config = ConfigDict(extra='forbid')
    
    log_level: str = Field(
        default="INFO",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level"
    )
    log_file: str = Field(
        default="logs/asset_generation.log",
        description="Path to log file"
    )
    transaction_log: str = Field(
        default="logs/transactions.json",
        description="Path to transaction log"
    )
    max_log_size: int = Field(
        default=10485760,  # 10MB
        gt=0,
        description="Maximum log file size in bytes"
    )
    backup_count: int = Field(
        default=5,
        ge=0,
        le=20,
        description="Number of backup log files to keep"
    )


class ReviewConfig(BaseModel):
    """Review server configuration."""
    model_config = ConfigDict(extra='forbid')
    
    port: int = Field(
        default=4500,
        ge=1024,
        le=65535,
        description="Review server port"
    )
    host: str = Field(
        default="127.0.0.1",
        description="Review server host"
    )
    auto_open_browser: bool = Field(
        default=True,
        description="Automatically open browser for review"
    )
    timeout: int = Field(
        default=600,
        gt=0,
        description="Review timeout in seconds"
    )


class ApplicationConfig(BaseModel):
    """Main application configuration."""
    model_config = ConfigDict(extra='forbid')
    
    budget: BudgetConfig
    replicate: ReplicateConfig
    output: OutputConfig
    logging: LoggingConfig
    review: ReviewConfig
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationConfig':
        """Create config from dictionary with validation.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            Validated ApplicationConfig instance
        """
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return self.model_dump()


class AssetGenerationRequest(BaseModel):
    """Request model for asset generation."""
    model_config = ConfigDict(extra='forbid')
    
    asset_type: str = Field(
        ...,
        pattern="^(icons|covers|textures|letter_headers|database_icons)$",
        description="Type of asset to generate"
    )
    prompt: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Generation prompt"
    )
    index: int = Field(
        ...,
        ge=1,
        description="Asset index number"
    )
    total: int = Field(
        ...,
        ge=1,
        description="Total number of assets"
    )
    
    @validator('total')
    def index_must_not_exceed_total(cls, v, values):
        if 'index' in values and values['index'] > v:
            raise ValueError('Index cannot exceed total')
        return v


class AssetGenerationResponse(BaseModel):
    """Response model for asset generation."""
    model_config = ConfigDict(extra='allow')
    
    asset_type: str
    prompt: str
    output_url: Optional[str] = None
    filepath: Optional[Path] = None
    cost: float
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None
    retry_count: int = 0
    
    @validator('filepath')
    def validate_filepath(cls, v):
        if v and not isinstance(v, Path):
            return Path(v)
        return v


class ManifestEntry(BaseModel):
    """Manifest entry for generated assets."""
    model_config = ConfigDict(extra='allow')
    
    filename: str
    asset_type: str
    prompt: str
    cost: float
    timestamp: str
    model_used: str
    quality_score: Optional[float] = None
    file_size: Optional[int] = None
    
    @validator('cost')
    def cost_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('Cost must be non-negative')
        return v
    
    @validator('quality_score')
    def quality_score_range(cls, v):
        if v is not None and not (0 <= v <= 1):
            raise ValueError('Quality score must be between 0 and 1')
        return v


class GenerationManifest(BaseModel):
    """Complete manifest for a generation run."""
    model_config = ConfigDict(extra='allow')
    
    assets: List[ManifestEntry]
    total_cost: float
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    production: bool = False
    total_generated: int = 0
    total_expected: int = 0
    generation_time: Optional[float] = None
    
    @validator('total_cost')
    def validate_total_cost(cls, v, values):
        if 'assets' in values:
            calculated = sum(a.cost for a in values['assets'])
            if abs(v - calculated) > 0.01:  # Allow small floating point differences
                raise ValueError(f'Total cost mismatch: {v} != {calculated}')
        return v


class YAMLPageConfig(BaseModel):
    """Configuration for a YAML page."""
    model_config = ConfigDict(extra='allow')
    
    id: str
    title: str
    description: Optional[str] = None
    icon: Optional[str] = None
    cover: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    parent: Optional[str] = None
    
    @validator('id')
    def validate_id(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Page ID must be at least 3 characters')
        return v


def validate_config_file(config_path: Union[str, Path]) -> ApplicationConfig:
    """Validate a configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Validated ApplicationConfig
        
    Raises:
        ValidationError: If configuration is invalid
    """
    import json
    
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        data = json.load(f)
    
    return ApplicationConfig.from_dict(data)