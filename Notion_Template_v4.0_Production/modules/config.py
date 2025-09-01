"""
Configuration Management Module
Handles loading, validation, and management of configuration settings
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict
import yaml

logger = logging.getLogger(__name__)

def load_config(path: Path) -> Dict:
    """Load configuration from YAML file with robust error handling"""
    try:
        if not path.exists():
            logger.error(f"Configuration file not found: {path}")
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        if not path.is_file():
            logger.error(f"Configuration path is not a file: {path}")
            raise ValueError(f"Configuration path is not a file: {path}")
            
        logger.info(f"Loading configuration from {path}")
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if config is None:
            logger.error(f"Configuration file is empty or invalid: {path}")
            raise ValueError(f"Configuration file is empty or invalid: {path}")
            
        if not isinstance(config, dict):
            logger.error(f"Configuration must be a dictionary, got {type(config)}")
            raise ValueError(f"Configuration must be a dictionary, got {type(config)}")
            
        logger.info(f"Successfully loaded configuration with {len(config)} keys")
        return config
        
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {path}: {e}")
        raise ValueError(f"YAML parsing error in {path}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading configuration from {path}: {e}")
        raise

def validate_config(config: Dict) -> Dict:
    """Validate and set defaults for configuration parameters"""
    required_keys = ["base_url", "notion_api_version"]
    missing_keys = [key for key in required_keys if key not in config or config[key] is None]
    
    if missing_keys:
        logger.error(f"Missing required configuration keys: {missing_keys}")
        raise ValueError(f"Missing required configuration keys: {missing_keys}")
    
    # Set defaults for optional parameters with type validation
    defaults = {
        "rate_limit_rps": 2.5,
        "default_timeout": 30,
        "max_retries": 5,
        "backoff_base": 1.5
    }
    
    for key, default_value in defaults.items():
        if key not in config or config[key] is None:
            logger.info(f"Using default value for {key}: {default_value}")
            config[key] = default_value
        else:
            # Type validation
            expected_type = type(default_value)
            if not isinstance(config[key], expected_type):
                try:
                    config[key] = expected_type(config[key])
                    logger.info(f"Converted {key} to {expected_type.__name__}: {config[key]}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid type for {key}: expected {expected_type.__name__}, got {type(config[key])}")
                    raise ValueError(f"Invalid type for {key}: expected {expected_type.__name__}")
    
    # Validate BASE_URL format
    if not config["base_url"].startswith("https://"):
        logger.error(f"Invalid base_url format: {config['base_url']} (must start with https://)")
        raise ValueError(f"Invalid base_url format: {config['base_url']} (must start with https://)")
    
    # Validate rate limit is positive
    if config["rate_limit_rps"] <= 0:
        logger.error(f"Invalid rate_limit_rps: {config['rate_limit_rps']} (must be positive)")
        raise ValueError(f"Invalid rate_limit_rps: {config['rate_limit_rps']} (must be positive)")
    
    return config

def initialize_config(config_path: str = "config.yaml") -> Dict:
    """Initialize configuration with error handling and validation"""
    try:
        config = load_config(Path(config_path))
        config = validate_config(config)
        
        logger.info(f"Configuration loaded successfully - BASE_URL: {config['base_url']}, API Version: {config['notion_api_version']}")
        return config
        
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.error("Please check your config.yaml file and ensure all required parameters are present")
        sys.exit(1)