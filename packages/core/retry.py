"""Retry logic with exponential backoff."""

import asyncio
import random
import time
from typing import Any, Callable, Optional, Type, Union
from functools import wraps

from .exceptions import RetryableError, FatalError
from .logging import get_logger

logger = get_logger("retry")


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> float:
    """Calculate backoff delay with exponential backoff and jitter."""
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    
    if jitter:
        # Add random jitter (±25%)
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
    
    return max(0, delay)


def retry_on_exception(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Union[Type[Exception], tuple] = RetryableError,
    reraise_on: Union[Type[Exception], tuple] = FatalError
):
    """Decorator for retrying functions with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except reraise_on:
                    # Don't retry fatal errors
                    raise
                except retry_on as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    delay = calculate_backoff(
                        attempt, base_delay, max_delay, exponential_base, jitter
                    )
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    
                    time.sleep(delay)
                except Exception as e:
                    # Unexpected exception, don't retry
                    logger.error(f"Function {func.__name__} failed with unexpected error: {e}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def async_retry_on_exception(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_on: Union[Type[Exception], tuple] = RetryableError,
    reraise_on: Union[Type[Exception], tuple] = FatalError
):
    """Decorator for retrying async functions with exponential backoff."""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except reraise_on:
                    # Don't retry fatal errors
                    raise
                except retry_on as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    delay = calculate_backoff(
                        attempt, base_delay, max_delay, exponential_base, jitter
                    )
                    
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {delay:.2f}s: {e}"
                    )
                    
                    await asyncio.sleep(delay)
                except Exception as e:
                    # Unexpected exception, don't retry
                    logger.error(f"Async function {func.__name__} failed with unexpected error: {e}")
                    raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


class RetryManager:
    """Class-based retry manager for more complex retry scenarios."""
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if exception should be retried."""
        if attempt >= self.max_retries:
            return False
        
        if isinstance(exception, FatalError):
            return False
        
        if isinstance(exception, RetryableError):
            return True
        
        return False

    def get_delay(self, attempt: int) -> float:
        """Get delay for retry attempt."""
        return calculate_backoff(
            attempt,
            self.base_delay,
            self.max_delay,
            self.exponential_base,
            self.jitter
        )

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if not self.should_retry(e, attempt):
                    raise
                
                delay = self.get_delay(attempt)
                logger.warning(
                    f"Retrying {func.__name__} in {delay:.2f}s (attempt {attempt + 1}): {e}"
                )
                time.sleep(delay)

    async def async_execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with retry logic."""
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if not self.should_retry(e, attempt):
                    raise
                
                delay = self.get_delay(attempt)
                logger.warning(
                    f"Retrying {func.__name__} in {delay:.2f}s (attempt {attempt + 1}): {e}"
                )
                await asyncio.sleep(delay)