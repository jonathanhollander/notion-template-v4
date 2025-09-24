"""
Advanced Logging configuration for Estate Planning Concierge v4.0
Provides comprehensive debugging, API tracing, and asset deployment tracking
"""

import logging
import logging.handlers
import os
import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any
import time
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging"""

    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.filename,
            'line': record.lineno,
            'message': record.getMessage()
        }

        # Add correlation ID if present
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id

        # Add extra context if present
        if hasattr(record, 'extra_context'):
            log_data.update(record.extra_context)

        return json.dumps(log_data, ensure_ascii=False)


class RequestCorrelationFilter(logging.Filter):
    """Add correlation ID to log records for request tracing"""

    def __init__(self):
        super().__init__()
        self.correlation_id = None

    def set_correlation_id(self, correlation_id: str = None):
        """Set correlation ID for current request"""
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]

    def filter(self, record):
        if self.correlation_id:
            record.correlation_id = self.correlation_id
        return True


def setup_logging(
    log_level: str = None,
    log_file: str = None,
    log_max_size: int = None,
    log_backup_count: int = None,
    console_output: bool = True,
    debug_api: bool = False,
    debug_assets: bool = False,
    trace_requests: bool = False
) -> logging.Logger:
    """
    Configure comprehensive logging with specialized debug handlers

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_max_size: Maximum size of log file in bytes before rotation
        log_backup_count: Number of backup files to keep
        console_output: Whether to also log to console
        debug_api: Enable detailed API request/response logging
        debug_assets: Enable asset deployment pipeline logging
        trace_requests: Enable request correlation tracing

    Returns:
        Configured logger instance
    """
    # Get configuration from environment or use defaults
    log_level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    log_file = log_file or os.getenv('LOG_FILE', 'logs/deployment.log')
    log_max_size = log_max_size or int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB default
    log_backup_count = log_backup_count or int(os.getenv('LOG_BACKUP_COUNT', '5'))

    # Check for debug flags from environment
    debug_api = debug_api or os.getenv('DEBUG_API', '').lower() in ('true', '1', 'yes')
    debug_assets = debug_assets or os.getenv('DEBUG_ASSETS', '').lower() in ('true', '1', 'yes')
    trace_requests = trace_requests or os.getenv('TRACE_REQUESTS', '').lower() in ('true', '1', 'yes')

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

    # JSON formatter for structured logs
    json_formatter = JSONFormatter()

    # Request correlation formatter
    correlation_formatter = logging.Formatter(
        '%(asctime)s - [%(correlation_id)s] %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Main file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=log_max_size,
        backupCount=log_backup_count
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # Create correlation filter for request tracing
    correlation_filter = RequestCorrelationFilter()

    # Specialized debug handlers
    if debug_api:
        # API debug handler - logs all API requests and responses
        api_log_path = log_path.parent / 'deploy_debug_api.log'
        api_handler = logging.handlers.RotatingFileHandler(
            str(api_log_path),
            maxBytes=log_max_size,
            backupCount=log_backup_count
        )
        api_handler.setLevel(logging.DEBUG)
        api_handler.setFormatter(json_formatter)
        api_handler.addFilter(correlation_filter)

        # Create API logger
        api_logger = logging.getLogger('estate_planning.api')
        api_logger.addHandler(api_handler)
        api_logger.setLevel(logging.DEBUG)
        api_logger.propagate = True

    if debug_assets:
        # Asset deployment handler - logs asset processing pipeline
        assets_log_path = log_path.parent / 'deploy_debug_assets.log'
        assets_handler = logging.handlers.RotatingFileHandler(
            str(assets_log_path),
            maxBytes=log_max_size,
            backupCount=log_backup_count
        )
        assets_handler.setLevel(logging.DEBUG)
        assets_handler.setFormatter(detailed_formatter)

        # Create asset logger
        asset_logger = logging.getLogger('estate_planning.assets')
        asset_logger.addHandler(assets_handler)
        asset_logger.setLevel(logging.DEBUG)
        asset_logger.propagate = True

    if trace_requests:
        # Request tracing handler - logs request/response pairs with correlation
        trace_log_path = log_path.parent / 'deploy_debug_trace.log'
        trace_handler = logging.handlers.RotatingFileHandler(
            str(trace_log_path),
            maxBytes=log_max_size,
            backupCount=log_backup_count
        )
        trace_handler.setLevel(logging.DEBUG)
        trace_handler.setFormatter(correlation_formatter)
        trace_handler.addFilter(correlation_filter)

        # Create trace logger
        trace_logger = logging.getLogger('estate_planning.trace')
        trace_logger.addHandler(trace_handler)
        trace_logger.setLevel(logging.DEBUG)
        trace_logger.propagate = True

    # Errors-only handler
    errors_log_path = log_path.parent / 'deploy_errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        str(errors_log_path),
        maxBytes=log_max_size,
        backupCount=log_backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    logger.addHandler(error_handler)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # Store correlation filter globally for use by other modules
    logger.correlation_filter = correlation_filter
    
    # Log initial setup
    logger.info("=" * 60)
    logger.info("Estate Planning Concierge v4.0 - Enhanced Logging Initialized")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Log File: {log_file}")
    logger.info(f"Max Size: {log_max_size:,} bytes")
    logger.info(f"Backup Count: {log_backup_count}")
    logger.info(f"Debug API: {debug_api}")
    logger.info(f"Debug Assets: {debug_assets}")
    logger.info(f"Trace Requests: {trace_requests}")
    if debug_api:
        logger.info(f"API Debug Log: {log_path.parent / 'deploy_debug_api.log'}")
    if debug_assets:
        logger.info(f"Assets Debug Log: {log_path.parent / 'deploy_debug_assets.log'}")
    if trace_requests:
        logger.info(f"Trace Debug Log: {log_path.parent / 'deploy_debug_trace.log'}")
    logger.info(f"Errors Log: {log_path.parent / 'deploy_errors.log'}")
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


class APIRequestLogger:
    """Enhanced API request/response logger with detailed context"""

    def __init__(self, correlation_id: str = None):
        self.logger = logging.getLogger('estate_planning.api')
        self.trace_logger = logging.getLogger('estate_planning.trace')
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]
        self.start_time = None

    def log_request(self, method: str, url: str, headers: Dict = None,
                   payload: Any = None, files: Any = None):
        """Log outgoing API request with sanitized details"""
        self.start_time = time.time()

        # Sanitize sensitive headers
        safe_headers = self.sanitize_headers(headers or {})

        # Sanitize payload (remove tokens, keys)
        safe_payload = self.sanitize_payload(payload)

        request_data = {
            'correlation_id': self.correlation_id,
            'type': 'api_request',
            'method': method.upper(),
            'url': url,
            'headers': safe_headers,
            'payload_size': len(str(payload)) if payload else 0,
            'has_files': bool(files),
            'timestamp': datetime.now().isoformat()
        }

        # Only include payload in debug mode and if it's not too large
        if safe_payload and len(str(safe_payload)) < 5000:
            request_data['payload_preview'] = str(safe_payload)[:1000]

        self.logger.debug("API Request", extra={'extra_context': request_data})
        self.trace_logger.debug(f"→ {method} {url}", extra={'correlation_id': self.correlation_id})

    def log_response(self, response, success: bool = True):
        """Log API response with timing and content details"""
        elapsed = time.time() - self.start_time if self.start_time else 0

        response_data = {
            'correlation_id': self.correlation_id,
            'type': 'api_response',
            'status_code': getattr(response, 'status_code', 'unknown'),
            'success': success,
            'elapsed_seconds': round(elapsed, 3),
            'response_size': len(getattr(response, 'text', '')) if response else 0,
            'timestamp': datetime.now().isoformat()
        }

        # Add response content for debugging (truncated)
        if response and hasattr(response, 'text'):
            response_data['response_preview'] = response.text[:500]

            # Try to parse JSON for better logging
            try:
                json_response = response.json()
                if isinstance(json_response, dict):
                    # Log important response keys
                    important_keys = ['id', 'object', 'error', 'message', 'results']
                    response_summary = {k: v for k, v in json_response.items() if k in important_keys}
                    if response_summary:
                        response_data['response_summary'] = response_summary
            except:
                pass

        level = logging.DEBUG if success else logging.ERROR
        self.logger.log(level, "API Response", extra={'extra_context': response_data})

        status_icon = "✓" if success else "✗"
        self.trace_logger.debug(
            f"← {response_data['status_code']} ({elapsed:.2f}s) {status_icon}",
            extra={'correlation_id': self.correlation_id}
        )

    def sanitize_headers(self, headers: Dict) -> Dict:
        """Remove sensitive information from headers"""
        sensitive_keys = ['authorization', 'notion-version', 'x-api-key']
        safe_headers = {}

        for key, value in headers.items():
            if key.lower() in sensitive_keys:
                safe_headers[key] = "***REDACTED***"
            else:
                safe_headers[key] = value

        return safe_headers

    def sanitize_payload(self, payload: Any) -> Any:
        """Remove sensitive information from payload"""
        if not payload:
            return None

        if isinstance(payload, str):
            try:
                data = json.loads(payload)
                return self.sanitize_dict(data)
            except:
                return f"<string:{len(payload)} chars>"

        if isinstance(payload, dict):
            return self.sanitize_dict(payload)

        return f"<{type(payload).__name__}>"

    def sanitize_dict(self, data: Dict) -> Dict:
        """Recursively sanitize dictionary data"""
        if not isinstance(data, dict):
            return data

        sensitive_keys = ['token', 'key', 'password', 'secret']
        safe_data = {}

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_data[key] = "***REDACTED***"
            elif isinstance(value, dict):
                safe_data[key] = self.sanitize_dict(value)
            elif isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], dict):
                    safe_data[key] = [self.sanitize_dict(item) for item in value[:3]]  # Limit to first 3
                    if len(value) > 3:
                        safe_data[key].append(f"...and {len(value)-3} more items")
                else:
                    safe_data[key] = value[:10]  # Limit to first 10 items
            else:
                safe_data[key] = value

        return safe_data


class APICallLogger:
    """Context manager for logging API calls with timing (legacy compatibility)"""

    def __init__(self, logger: logging.Logger, endpoint: str, method: str = "GET"):
        self.logger = logger
        self.endpoint = endpoint
        self.method = method
        self.api_logger = APIRequestLogger()

    def __enter__(self):
        self.api_logger.log_request(self.method, self.endpoint)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        # Create mock response for compatibility
        class MockResponse:
            def __init__(self, error=None):
                self.status_code = 500 if error else 200
                self.text = str(error) if error else "Success"

        response = MockResponse(exc_val)
        self.api_logger.log_response(response, success)
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


class AssetLogger:
    """Specialized logger for asset deployment tracking"""

    def __init__(self):
        self.logger = logging.getLogger('estate_planning.assets')
        self.stats = {
            'pages_processed': 0,
            'assets_created': 0,
            'assets_skipped': 0,
            'blocks_created': 0,
            'errors': 0
        }

    def log_page_processing(self, page_title: str, total_blocks: int):
        """Log start of page content processing"""
        self.stats['pages_processed'] += 1
        self.logger.info(f"Processing page: '{page_title}' ({total_blocks} blocks)")

    def log_block_creation(self, block_type: str, content_preview: str = "", success: bool = True):
        """Log block creation with content preview"""
        if success:
            self.stats['blocks_created'] += 1
            preview = (content_preview[:100] + "...") if len(content_preview) > 100 else content_preview
            self.logger.debug(f"✓ Created {block_type} block: {preview}")
        else:
            self.stats['errors'] += 1
            self.logger.error(f"✗ Failed to create {block_type} block: {content_preview}")

    def log_asset_processing(self, asset_type: str, asset_path: str, success: bool = True):
        """Log asset processing (images, files, etc.)"""
        if success:
            self.stats['assets_created'] += 1
            self.logger.info(f"✓ Processed {asset_type}: {asset_path}")
        else:
            self.stats['assets_skipped'] += 1
            self.logger.warning(f"⚠ Skipped {asset_type}: {asset_path}")

    def log_yaml_processing(self, yaml_section: str, items_found: int):
        """Log YAML section processing"""
        self.logger.debug(f"YAML section '{yaml_section}': {items_found} items found")

    def log_content_transformation(self, from_format: str, to_format: str, item_count: int):
        """Log content format transformations"""
        self.logger.debug(f"Transformed {item_count} items: {from_format} → {to_format}")

    def log_asset_summary(self):
        """Log asset deployment summary"""
        self.logger.info("=" * 50)
        self.logger.info("ASSET DEPLOYMENT SUMMARY")
        self.logger.info(f"Pages Processed: {self.stats['pages_processed']}")
        self.logger.info(f"Blocks Created: {self.stats['blocks_created']}")
        self.logger.info(f"Assets Created: {self.stats['assets_created']}")
        self.logger.info(f"Assets Skipped: {self.stats['assets_skipped']}")
        self.logger.info(f"Errors: {self.stats['errors']}")

        if self.stats['errors'] == 0:
            self.logger.info("✓ Asset deployment completed successfully!")
        else:
            self.logger.error(f"✗ Asset deployment completed with {self.stats['errors']} errors")
        self.logger.info("=" * 50)


# Initialize default logger when module is imported
default_logger = None

def init_default_logger():
    """Initialize the default logger if not already done"""
    global default_logger
    if default_logger is None:
        default_logger = setup_logging()
    return default_logger