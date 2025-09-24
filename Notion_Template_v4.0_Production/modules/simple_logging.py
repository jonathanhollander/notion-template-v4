"""
Simple unified logging with color-coded entries
All logs go to ONE file but with visual separation via color prefixes
"""

import logging
import os
from pathlib import Path
from datetime import datetime


class ColorCodedFormatter(logging.Formatter):
    """Format log records with color-coded prefixes based on content type"""

    def __init__(self):
        super().__init__()

    def format(self, record):
        # Get timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        # Get the message
        message = record.getMessage()
        message_lower = message.lower()

        # Determine color prefix based on content
        if any(keyword in message_lower for keyword in ['api_request', 'api_response', 'post /v1/', 'patch /v1/', 'get /v1/', 'status_code:', 'notion api']):
            prefix = "🟢 API"
        elif any(keyword in message_lower for keyword in ['asset', 'icon', 'cover', 'image', 'processing', 'block creation', 'page creation']):
            prefix = "🔵 ASSET"
        elif any(keyword in message_lower for keyword in ['error', 'failed', 'exception', 'warning', 'critical']):
            prefix = "🔴 ERROR"
        elif any(keyword in message_lower for keyword in ['correlation_id', 'request_id', 'tracing', 'elapsed_seconds']):
            prefix = "🟣 TRACE"
        elif any(keyword in message_lower for keyword in ['yaml', 'section', 'parsing', 'configuration']):
            prefix = "🟠 YAML"
        else:
            prefix = "⚫ INFO"

        # Format: [COLOR PREFIX] TIMESTAMP - LEVEL - MODULE:LINE - MESSAGE
        return f"{prefix} {timestamp} - {record.levelname} - {record.filename}:{record.lineno} - {message}"


def setup_unified_logging(log_file: str = None, log_level: str = None):
    """
    Set up unified logging - everything goes to ONE file with color prefixes

    Args:
        log_file: Path to the single log file (default: logs/debug.log)
        log_level: Log level (default: DEBUG)
    """
    # Get configuration - check environment first, then use parameter, then default
    log_file = os.getenv('LOG_FILE') or log_file or 'logs/debug.log'
    log_level = log_level or os.getenv('LOG_LEVEL', 'DEBUG')

    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Clear existing file
    if log_path.exists():
        log_path.unlink()

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(ColorCodedFormatter())

    # Add handler to root logger
    root_logger.addHandler(file_handler)

    # Also set up specific loggers we use
    loggers_to_setup = [
        'estate_planning',
        'estate_planning.api',
        'estate_planning.assets',
        'estate_planning.trace',
        'estate_planning.deployment',
        '__main__'  # For deploy.py main script logging
    ]

    for logger_name in loggers_to_setup:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = True  # Ensure messages reach root logger

    # Log initialization
    logger = logging.getLogger('estate_planning')
    logger.info("🚀 Unified debug logging initialized")
    logger.info("📝 All output will be color-coded in: {}".format(log_file))
    logger.info("🟢 = API Calls | 🔵 = Asset Processing | 🔴 = Errors | ⚫ = General | 🟣 = Requests | 🟠 = YAML Processing")

    return logger