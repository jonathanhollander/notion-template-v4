"""
Logging configuration for Estate Planning Concierge v4.0
Provides centralized logging setup with rotation and multiple handlers
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

def setup_logging(
    log_level: str = None,
    log_file: str = None,
    log_max_size: int = None,
    log_backup_count: int = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure logging with file rotation and console output
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_max_size: Maximum size of log file in bytes before rotation
        log_backup_count: Number of backup files to keep
        console_output: Whether to also log to console
    
    Returns:
        Configured logger instance
    """
    # Get configuration from environment or use defaults
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    log_file = log_file or os.getenv('LOG_FILE', 'logs/deployment.log')
    log_max_size = log_max_size or int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB default
    log_backup_count = log_backup_count or int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('estate_planning')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=log_max_size,
        backupCount=log_backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # Log initial setup
    logger.info("=" * 60)
    logger.info("Estate Planning Concierge v4.0 - Logging Initialized")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Log File: {log_file}")
    logger.info(f"Max Size: {log_max_size:,} bytes")
    logger.info(f"Backup Count: {log_backup_count}")
    logger.info("=" * 60)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific module
    
    Args:
        name: Logger name (usually __name__ from the calling module)
    
    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f'estate_planning.{name}')
    return logging.getLogger('estate_planning')


class APICallLogger:
    """Context manager for logging API calls with timing"""
    
    def __init__(self, logger: logging.Logger, endpoint: str, method: str = "GET"):
        self.logger = logger
        self.endpoint = endpoint
        self.method = method
        self.start_time = None
        
    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.debug(f"API Call Started: {self.method} {self.endpoint}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        elapsed = time.time() - self.start_time
        
        if exc_type:
            self.logger.error(
                f"API Call Failed: {self.method} {self.endpoint} "
                f"({elapsed:.2f}s) - Error: {exc_val}"
            )
        else:
            self.logger.info(
                f"API Call Completed: {self.method} {self.endpoint} ({elapsed:.2f}s)"
            )
        
        return False  # Don't suppress exceptions


class DeploymentLogger:
    """Specialized logger for deployment operations"""
    
    def __init__(self):
        self.logger = get_logger('deployment')
        self.stats = {
            'pages_created': 0,
            'databases_created': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def log_page_creation(self, page_title: str, success: bool = True):
        """Log page creation with statistics tracking"""
        if success:
            self.stats['pages_created'] += 1
            self.logger.info(f"✓ Page created: {page_title}")
        else:
            self.stats['errors'] += 1
            self.logger.error(f"✗ Failed to create page: {page_title}")
    
    def log_database_creation(self, db_name: str, success: bool = True):
        """Log database creation with statistics tracking"""
        if success:
            self.stats['databases_created'] += 1
            self.logger.info(f"✓ Database created: {db_name}")
        else:
            self.stats['errors'] += 1
            self.logger.error(f"✗ Failed to create database: {db_name}")
    
    def log_warning(self, message: str):
        """Log warning and track count"""
        self.stats['warnings'] += 1
        self.logger.warning(message)
    
    def log_summary(self):
        """Log deployment summary statistics"""
        self.logger.info("=" * 60)
        self.logger.info("DEPLOYMENT SUMMARY")
        self.logger.info(f"Pages Created: {self.stats['pages_created']}")
        self.logger.info(f"Databases Created: {self.stats['databases_created']}")
        self.logger.info(f"Errors: {self.stats['errors']}")
        self.logger.info(f"Warnings: {self.stats['warnings']}")
        
        if self.stats['errors'] == 0:
            self.logger.info("✓ Deployment completed successfully!")
        else:
            self.logger.error(f"✗ Deployment completed with {self.stats['errors']} errors")
        self.logger.info("=" * 60)


# Initialize default logger when module is imported
default_logger = None

def init_default_logger():
    """Initialize the default logger if not already done"""
    global default_logger
    if default_logger is None:
        default_logger = setup_logging()
    return default_logger