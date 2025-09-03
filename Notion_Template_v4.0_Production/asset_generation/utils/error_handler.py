"""Comprehensive error handling and retry logic."""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, TypeVar, Union
from datetime import datetime
import traceback

from .exceptions import (
    APIError, NetworkError, ValidationError,
    BudgetExceededError, TransactionError
)

T = TypeVar('T')


class ErrorHandler:
    """Comprehensive error handling with retry logic and logging."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler.
        
        Args:
            logger: Logger instance (creates default if not provided)
        """
        self.logger = logger or logging.getLogger(__name__)
        self.error_counts = {}
        self.last_errors = {}
    
    def with_retry(
        self,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: tuple = (APIError, NetworkError)
    ):
        """Decorator for functions with retry logic.
        
        Args:
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries in seconds
            backoff: Backoff multiplier for each retry
            exceptions: Tuple of exceptions to retry on
        
        Returns:
            Decorated function with retry logic
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < max_retries:
                            self.logger.warning(
                                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}"
                                f" Retrying in {current_delay:.1f}s..."
                            )
                            await asyncio.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            self.logger.error(
                                f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                            )
                            raise
                    except Exception as e:
                        # Don't retry on unexpected exceptions
                        self.logger.error(f"Unexpected error in {func.__name__}: {e}")
                        raise
                
                if last_exception:
                    raise last_exception
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt < max_retries:
                            self.logger.warning(
                                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}"
                                f" Retrying in {current_delay:.1f}s..."
                            )
                            import time
                            time.sleep(current_delay)
                            current_delay *= backoff
                        else:
                            self.logger.error(
                                f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                            )
                            raise
                    except Exception as e:
                        # Don't retry on unexpected exceptions
                        self.logger.error(f"Unexpected error in {func.__name__}: {e}")
                        raise
                
                if last_exception:
                    raise last_exception
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def with_error_boundary(
        self,
        default_return: Any = None,
        log_errors: bool = True,
        raise_critical: bool = True
    ):
        """Decorator to add error boundary around functions.
        
        Args:
            default_return: Value to return on error
            log_errors: Whether to log errors
            raise_critical: Whether to raise critical errors
        
        Returns:
            Decorated function with error boundary
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                try:
                    return await func(*args, **kwargs)
                except (BudgetExceededError, ValidationError) as e:
                    # Critical errors that should always be raised
                    if raise_critical:
                        raise
                    if log_errors:
                        self.logger.error(f"Critical error in {func.__name__}: {e}")
                    return default_return
                except Exception as e:
                    if log_errors:
                        self.logger.error(
                            f"Error in {func.__name__}: {e}\n"
                            f"Traceback:\n{traceback.format_exc()}"
                        )
                    
                    # Track error statistics
                    func_name = func.__name__
                    self.error_counts[func_name] = self.error_counts.get(func_name, 0) + 1
                    self.last_errors[func_name] = {
                        'error': str(e),
                        'timestamp': datetime.now().isoformat(),
                        'traceback': traceback.format_exc()
                    }
                    
                    return default_return
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                try:
                    return func(*args, **kwargs)
                except (BudgetExceededError, ValidationError) as e:
                    # Critical errors that should always be raised
                    if raise_critical:
                        raise
                    if log_errors:
                        self.logger.error(f"Critical error in {func.__name__}: {e}")
                    return default_return
                except Exception as e:
                    if log_errors:
                        self.logger.error(
                            f"Error in {func.__name__}: {e}\n"
                            f"Traceback:\n{traceback.format_exc()}"
                        )
                    
                    # Track error statistics
                    func_name = func.__name__
                    self.error_counts[func_name] = self.error_counts.get(func_name, 0) + 1
                    self.last_errors[func_name] = {
                        'error': str(e),
                        'timestamp': datetime.now().isoformat(),
                        'traceback': traceback.format_exc()
                    }
                    
                    return default_return
            
            # Return appropriate wrapper based on function type
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    async def safe_execute(
        self,
        func: Callable,
        *args,
        default_return: Any = None,
        error_message: str = "Operation failed",
        **kwargs
    ) -> Any:
        """Safely execute a function with error handling.
        
        Args:
            func: Function to execute
            *args: Function arguments
            default_return: Value to return on error
            error_message: Custom error message
            **kwargs: Function keyword arguments
        
        Returns:
            Function result or default_return on error
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return await asyncio.to_thread(func, *args, **kwargs)
        except Exception as e:
            self.logger.error(f"{error_message}: {e}")
            return default_return
    
    def get_error_summary(self) -> dict:
        """Get summary of all errors encountered.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts,
            'last_errors': self.last_errors
        }
    
    def clear_error_stats(self):
        """Clear error statistics."""
        self.error_counts.clear()
        self.last_errors.clear()


def create_error_handler(logger: Optional[logging.Logger] = None) -> ErrorHandler:
    """Create and configure an error handler instance.
    
    Args:
        logger: Logger instance
    
    Returns:
        Configured ErrorHandler instance
    """
    return ErrorHandler(logger)