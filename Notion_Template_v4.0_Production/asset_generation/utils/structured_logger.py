"""Enhanced logging with structured context for the asset generation system.

Provides rich, structured logging with context preservation, performance metrics,
and integration with external logging services.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from contextlib import contextmanager
import traceback
from dataclasses import dataclass, asdict
import asyncio
from functools import wraps
import time

# Try to import rich for better console output (optional)
try:
    from rich.logging import RichHandler
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class LogContext:
    """Structured context for logging."""
    run_id: Optional[str] = None
    asset_type: Optional[str] = None
    prompt: Optional[str] = None
    model: Optional[str] = None
    index: Optional[int] = None
    total: Optional[int] = None
    cost: Optional[float] = None
    duration: Optional[float] = None
    error_type: Optional[str] = None
    retry_count: Optional[int] = None
    cache_hit: Optional[bool] = None
    is_generic: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


class StructuredLogger:
    """Enhanced logger with structured context and performance tracking.
    
    Features:
        - Structured logging with context
        - Performance metrics
        - Error tracking with full context
        - Log aggregation
        - Rich console output (if available)
    """
    
    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_file: Optional[Path] = None,
        json_logs: bool = False,
        use_rich: bool = True
    ):
        """Initialize structured logger.
        
        Args:
            name: Logger name
            log_level: Logging level
            log_file: Optional log file path
            json_logs: Whether to output JSON formatted logs
            use_rich: Whether to use rich formatting if available
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.json_logs = json_logs
        self.context_stack: List[LogContext] = []
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # Console handler
        if use_rich and RICH_AVAILABLE:
            console_handler = RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=True
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
        
        # Set formatter
        if json_logs:
            console_handler.setFormatter(JsonFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
            )
        
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            if json_logs:
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(
                    logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
                )
            self.logger.addHandler(file_handler)
        
        # Performance metrics
        self.metrics = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'warnings': 0,
            'total_cost': 0.0,
            'total_duration': 0.0
        }
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager for structured logging context.
        
        Usage:
            with logger.context(run_id="abc", asset_type="icon"):
                logger.info("Processing asset")
        """
        context = LogContext(**kwargs)
        self.context_stack.append(context)
        try:
            yield context
        finally:
            self.context_stack.pop()
    
    def _get_current_context(self) -> Dict[str, Any]:
        """Get merged current context."""
        merged = {}
        for context in self.context_stack:
            merged.update(context.to_dict())
        return merged
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ):
        """Log message with current context."""
        context = self._get_current_context()
        if extra:
            context.update(extra)
        
        if self.json_logs:
            # For JSON logs, include context in extra
            self.logger.log(level, message, extra={'context': context})
        else:
            # For text logs, append key context items
            if context:
                context_str = ' - '.join(f"{k}={v}" for k, v in context.items())
                message = f"{message} [{context_str}]"
            self.logger.log(level, message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.metrics['warnings'] += 1
        self._log_with_context(logging.WARNING, message, kwargs)
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with context and exception details."""
        self.metrics['errors'] += 1
        
        if exception:
            kwargs['error_type'] = type(exception).__name__
            kwargs['error_message'] = str(exception)
            if self.logger.level == logging.DEBUG:
                kwargs['traceback'] = traceback.format_exc()
        
        self._log_with_context(logging.ERROR, message, kwargs)
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        **kwargs
    ):
        """Log performance metrics."""
        self.metrics['total_duration'] += duration
        
        level = logging.INFO if success else logging.WARNING
        message = f"{operation} completed in {duration:.2f}s"
        
        self._log_with_context(level, message, {
            'operation': operation,
            'duration': duration,
            'success': success,
            **kwargs
        })
    
    def log_api_call(
        self,
        endpoint: str,
        duration: float,
        success: bool,
        cost: Optional[float] = None,
        **kwargs
    ):
        """Log API call with metrics."""
        self.metrics['api_calls'] += 1
        if cost:
            self.metrics['total_cost'] += cost
        
        message = f"API call to {endpoint}"
        if cost:
            message += f" (${cost:.4f})"
        
        self.log_performance(message, duration, success, cost=cost, **kwargs)
    
    def log_cache_access(self, hit: bool, key: str, **kwargs):
        """Log cache access."""
        if hit:
            self.metrics['cache_hits'] += 1
            self.info(f"Cache hit: {key[:16]}...", cache_hit=True, **kwargs)
        else:
            self.metrics['cache_misses'] += 1
            self.debug(f"Cache miss: {key[:16]}...", cache_hit=False, **kwargs)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = self.metrics.copy()
        
        # Calculate rates
        total_cache_access = metrics['cache_hits'] + metrics['cache_misses']
        if total_cache_access > 0:
            metrics['cache_hit_rate'] = (metrics['cache_hits'] / total_cache_access) * 100
        else:
            metrics['cache_hit_rate'] = 0
        
        # Average API call duration
        if metrics['api_calls'] > 0:
            metrics['avg_api_duration'] = metrics['total_duration'] / metrics['api_calls']
        else:
            metrics['avg_api_duration'] = 0
        
        return metrics
    
    def print_metrics_table(self):
        """Print metrics in a formatted table."""
        metrics = self.get_metrics()
        
        if RICH_AVAILABLE:
            console = Console()
            table = Table(title="Performance Metrics")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("API Calls", str(metrics['api_calls']))
            table.add_row("Cache Hits", str(metrics['cache_hits']))
            table.add_row("Cache Misses", str(metrics['cache_misses']))
            table.add_row("Cache Hit Rate", f"{metrics['cache_hit_rate']:.1f}%")
            table.add_row("Total Errors", str(metrics['errors']))
            table.add_row("Total Warnings", str(metrics['warnings']))
            table.add_row("Total Cost", f"${metrics['total_cost']:.2f}")
            table.add_row("Total Duration", f"{metrics['total_duration']:.1f}s")
            table.add_row("Avg API Duration", f"{metrics['avg_api_duration']:.2f}s")
            
            console.print(table)
        else:
            print("\n=== Performance Metrics ===")
            for key, value in metrics.items():
                if isinstance(value, float):
                    if 'cost' in key:
                        print(f"{key}: ${value:.2f}")
                    elif 'rate' in key:
                        print(f"{key}: {value:.1f}%")
                    else:
                        print(f"{key}: {value:.2f}")
                else:
                    print(f"{key}: {value}")


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add context if present
        if hasattr(record, 'context'):
            log_obj['context'] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_obj)


def log_execution_time(logger: StructuredLogger):
    """Decorator to log execution time of functions.
    
    Args:
        logger: StructuredLogger instance
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(f"{func.__name__}", duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_performance(f"{func.__name__}", duration, success=False)
                logger.error(f"Error in {func.__name__}", exception=e)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(f"{func.__name__}", duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_performance(f"{func.__name__}", duration, success=False)
                logger.error(f"Error in {func.__name__}", exception=e)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class LogAggregator:
    """Aggregates logs for batch processing and analysis."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize log aggregator.
        
        Args:
            max_size: Maximum number of logs to buffer
        """
        self.buffer: List[Dict[str, Any]] = []
        self.max_size = max_size
    
    def add(self, log_entry: Dict[str, Any]):
        """Add log entry to buffer."""
        self.buffer.append({
            **log_entry,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        if len(self.buffer) >= self.max_size:
            self.flush()
    
    def flush(self) -> List[Dict[str, Any]]:
        """Flush and return buffered logs."""
        logs = self.buffer.copy()
        self.buffer.clear()
        return logs
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of buffered logs."""
        if not self.buffer:
            return {'count': 0}
        
        levels = {}
        operations = {}
        errors = []
        
        for log in self.buffer:
            # Count by level
            level = log.get('level', 'UNKNOWN')
            levels[level] = levels.get(level, 0) + 1
            
            # Count by operation
            if 'operation' in log:
                op = log['operation']
                operations[op] = operations.get(op, 0) + 1
            
            # Collect errors
            if log.get('level') == 'ERROR':
                errors.append({
                    'message': log.get('message'),
                    'error_type': log.get('error_type'),
                    'timestamp': log.get('timestamp')
                })
        
        return {
            'count': len(self.buffer),
            'levels': levels,
            'operations': operations,
            'errors': errors[:10],  # Limit to 10 most recent
            'timespan': {
                'start': self.buffer[0].get('timestamp'),
                'end': self.buffer[-1].get('timestamp')
            }
        }


# Global logger instance
logger = StructuredLogger("asset_generation", log_level="INFO")


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_logs: bool = False,
    use_rich: bool = True
) -> StructuredLogger:
    """Setup and return configured logger.
    
    Args:
        log_level: Logging level
        log_file: Optional log file path
        json_logs: Whether to use JSON formatting
        use_rich: Whether to use rich console output
        
    Returns:
        Configured StructuredLogger instance
    """
    global logger
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        log_path = None
    
    logger = StructuredLogger(
        "asset_generation",
        log_level=log_level,
        log_file=log_path,
        json_logs=json_logs,
        use_rich=use_rich
    )
    
    return logger