"""Smart retry manager with intelligent fallback strategies.

Implements multiple retry strategies for failed asset generation including
prompt simplification, model switching, parameter adjustment, and generic fallbacks.
"""

import asyncio
import logging
import re
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Available retry strategies."""
    IMMEDIATE_RETRY = "immediate_retry"
    SIMPLIFIED_PROMPT = "simplified_prompt"
    ALTERNATIVE_MODEL = "alternative_model"
    ADJUSTED_PARAMETERS = "adjusted_parameters"
    GENERIC_FALLBACK = "generic_fallback"
    DELAYED_RETRY = "delayed_retry"
    SKIP_ASSET = "skip_asset"


@dataclass
class RetryContext:
    """Context for retry operations."""
    original_request: Dict[str, Any]
    attempt_number: int
    total_attempts: int
    last_error: Optional[str]
    strategies_tried: List[RetryStrategy]
    cost_so_far: float
    start_time: datetime
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def should_continue(self) -> bool:
        """Check if retry should continue."""
        # Stop after 5 attempts or 5 minutes
        return (
            self.attempt_number < self.total_attempts and
            self.elapsed_time < 300  # 5 minutes
        )


class SmartRetryManager:
    """Intelligent retry manager with multiple fallback strategies.
    
    Features:
        - Multiple retry strategies
        - Automatic strategy selection based on error type
        - Cost-aware retries
        - Model fallback chains
        - Prompt simplification
        - Generic asset fallbacks
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        max_attempts: int = 5,
        max_retry_cost: float = 1.0
    ):
        """Initialize retry manager.
        
        Args:
            db_manager: Database manager instance
            max_attempts: Maximum retry attempts
            max_retry_cost: Maximum cost for retries
        """
        self.db = db_manager
        self.max_attempts = max_attempts
        self.max_retry_cost = max_retry_cost
        
        # Strategy functions
        self.strategies = {
            RetryStrategy.IMMEDIATE_RETRY: self._immediate_retry,
            RetryStrategy.SIMPLIFIED_PROMPT: self._retry_with_simplified_prompt,
            RetryStrategy.ALTERNATIVE_MODEL: self._retry_with_alternative_model,
            RetryStrategy.ADJUSTED_PARAMETERS: self._retry_with_adjusted_parameters,
            RetryStrategy.GENERIC_FALLBACK: self._fallback_to_generic_asset,
            RetryStrategy.DELAYED_RETRY: self._delayed_retry,
        }
        
        # Model fallback chains
        self.model_fallbacks = {
            'flux-schnell': ['stable-diffusion-xl-base-1.0', 'sdxl-lightning-4step'],
            'flux-dev': ['flux-schnell', 'stable-diffusion-xl-base-1.0'],
            'stable-diffusion-xl-base-1.0': ['sdxl-lightning-4step', 'playground-v2-1024px-aesthetic'],
        }
        
        # Error patterns and their strategies
        self.error_strategies = {
            r'rate.?limit': [RetryStrategy.DELAYED_RETRY, RetryStrategy.ALTERNATIVE_MODEL],
            r'timeout|timed?.?out': [RetryStrategy.IMMEDIATE_RETRY, RetryStrategy.ADJUSTED_PARAMETERS],
            r'nsfw|safety|inappropriate': [RetryStrategy.SIMPLIFIED_PROMPT, RetryStrategy.GENERIC_FALLBACK],
            r'invalid.?prompt|prompt.?too.?long': [RetryStrategy.SIMPLIFIED_PROMPT],
            r'model.?not.?found|unavailable': [RetryStrategy.ALTERNATIVE_MODEL],
            r'insufficient.?funds|quota': [RetryStrategy.SKIP_ASSET],
            r'server.?error|500|502|503': [RetryStrategy.DELAYED_RETRY, RetryStrategy.IMMEDIATE_RETRY],
        }
    
    async def retry_with_strategies(
        self,
        original_request: Dict[str, Any],
        generate_func: Callable,
        error: Optional[Exception] = None
    ) -> Optional[Dict[str, Any]]:
        """Retry generation with multiple strategies.
        
        Args:
            original_request: Original generation request
            generate_func: Function to call for generation
            error: Original error that triggered retry
            
        Returns:
            Successful result or None if all strategies fail
        """
        context = RetryContext(
            original_request=original_request.copy(),
            attempt_number=0,
            total_attempts=self.max_attempts,
            last_error=str(error) if error else None,
            strategies_tried=[],
            cost_so_far=0.0,
            start_time=datetime.now()
        )
        
        # Determine initial strategies based on error
        strategies = self._select_strategies(context.last_error)
        
        for strategy in strategies:
            if not context.should_continue:
                logger.warning("Retry limit reached, stopping retries")
                break
            
            if strategy in context.strategies_tried:
                continue  # Skip already tried strategies
            
            context.attempt_number += 1
            context.strategies_tried.append(strategy)
            
            logger.info(f"Attempting retry {context.attempt_number}/{self.max_attempts} with strategy: {strategy.value}")
            
            try:
                # Execute strategy
                result = await self.strategies[strategy](context, generate_func)
                
                if result:
                    # Log successful retry
                    await self.db.log_retry(
                        asset_type=original_request.get('asset_type'),
                        prompt=original_request.get('prompt'),
                        strategy=strategy.value,
                        attempt_number=context.attempt_number,
                        success=True,
                        error_message=None,
                        metadata={
                            'total_time': context.elapsed_time,
                            'strategies_tried': [s.value for s in context.strategies_tried]
                        }
                    )
                    
                    logger.info(f"Retry successful with strategy: {strategy.value}")
                    return result
                    
            except Exception as e:
                context.last_error = str(e)
                logger.error(f"Strategy {strategy.value} failed: {e}")
                
                # Log failed attempt
                await self.db.log_retry(
                    asset_type=original_request.get('asset_type'),
                    prompt=original_request.get('prompt'),
                    strategy=strategy.value,
                    attempt_number=context.attempt_number,
                    success=False,
                    error_message=str(e)
                )
        
        logger.error(f"All retry strategies exhausted for request")
        return None
    
    def _select_strategies(self, error_message: Optional[str]) -> List[RetryStrategy]:
        """Select appropriate strategies based on error.
        
        Args:
            error_message: Error message to analyze
            
        Returns:
            Ordered list of strategies to try
        """
        if not error_message:
            # Default strategies for unknown errors
            return [
                RetryStrategy.IMMEDIATE_RETRY,
                RetryStrategy.ADJUSTED_PARAMETERS,
                RetryStrategy.ALTERNATIVE_MODEL,
                RetryStrategy.GENERIC_FALLBACK
            ]
        
        strategies = []
        error_lower = error_message.lower()
        
        # Match error patterns
        for pattern, strategy_list in self.error_strategies.items():
            if re.search(pattern, error_lower, re.IGNORECASE):
                strategies.extend(strategy_list)
        
        # Add default fallbacks if no specific match
        if not strategies:
            strategies = [
                RetryStrategy.IMMEDIATE_RETRY,
                RetryStrategy.SIMPLIFIED_PROMPT,
                RetryStrategy.ALTERNATIVE_MODEL
            ]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_strategies = []
        for s in strategies:
            if s not in seen:
                seen.add(s)
                unique_strategies.append(s)
        
        return unique_strategies
    
    async def _immediate_retry(
        self,
        context: RetryContext,
        generate_func: Callable
    ) -> Optional[Dict[str, Any]]:
        """Retry immediately with same parameters.
        
        Args:
            context: Retry context
            generate_func: Generation function
            
        Returns:
            Result or None
        """
        logger.debug("Attempting immediate retry with same parameters")
        
        # Small delay to avoid hammering the API
        await asyncio.sleep(1)
        
        try:
            result = await generate_func(context.original_request)
            return result
        except Exception as e:
            logger.debug(f"Immediate retry failed: {e}")
            return None
    
    async def _delayed_retry(
        self,
        context: RetryContext,
        generate_func: Callable
    ) -> Optional[Dict[str, Any]]:
        """Retry after a delay.
        
        Args:
            context: Retry context
            generate_func: Generation function
            
        Returns:
            Result or None
        """
        # Exponential backoff
        delay = min(2 ** context.attempt_number, 30)  # Max 30 seconds
        logger.info(f"Waiting {delay} seconds before retry")
        await asyncio.sleep(delay)
        
        try:
            result = await generate_func(context.original_request)
            return result
        except Exception as e:
            logger.debug(f"Delayed retry failed: {e}")
            return None
    
    async def _retry_with_simplified_prompt(
        self,
        context: RetryContext,
        generate_func: Callable
    ) -> Optional[Dict[str, Any]]:
        """Retry with simplified prompt.
        
        Args:
            context: Retry context
            generate_func: Generation function
            
        Returns:
            Result or None
        """
        original_prompt = context.original_request.get('prompt', '')
        simplified = self._simplify_prompt(original_prompt)
        
        if simplified == original_prompt:
            logger.debug("Prompt already simple, skipping simplification")
            return None
        
        logger.info(f"Retrying with simplified prompt: {simplified[:100]}...")
        
        request = context.original_request.copy()
        request['prompt'] = simplified
        
        try:
            result = await generate_func(request)
            return result
        except Exception as e:
            logger.debug(f"Simplified prompt retry failed: {e}")
            return None
    
    def _simplify_prompt(self, prompt: str) -> str:
        """Simplify a complex prompt.
        
        Args:
            prompt: Original prompt
            
        Returns:
            Simplified prompt
        """
        # Remove complex modifiers
        simplifications = [
            (r'\b(ultra|hyper|super|extremely|very|highly)\s+', ''),  # Remove intensifiers
            (r'\b\d+k\b', ''),  # Remove resolution specs
            (r'masterpiece|best quality|high quality', 'good quality'),  # Simplify quality
            (r'intricate|detailed|complex', 'simple'),  # Simplify complexity
            (r',\s*,+', ','),  # Remove multiple commas
            (r'\s+', ' '),  # Normalize whitespace
        ]
        
        simplified = prompt
        for pattern, replacement in simplifications:
            simplified = re.sub(pattern, replacement, simplified, flags=re.IGNORECASE)
        
        # Truncate if too long
        if len(simplified) > 200:
            # Keep most important parts (beginning)
            simplified = simplified[:200].rsplit(' ', 1)[0] + '...'
        
        return simplified.strip()
    
    async def _retry_with_alternative_model(
        self,
        context: RetryContext,
        generate_func: Callable
    ) -> Optional[Dict[str, Any]]:
        """Retry with alternative model.
        
        Args:
            context: Retry context
            generate_func: Generation function
            
        Returns:
            Result or None
        """
        current_model = context.original_request.get('model', 'flux-schnell')
        alternatives = self.model_fallbacks.get(current_model, [])
        
        if not alternatives:
            logger.debug(f"No alternative models for {current_model}")
            return None
        
        for alt_model in alternatives:
            logger.info(f"Trying alternative model: {alt_model}")
            
            request = context.original_request.copy()
            request['model'] = alt_model
            
            # Adjust parameters for different model
            request = self._adjust_for_model(request, alt_model)
            
            try:
                result = await generate_func(request)
                if result:
                    logger.info(f"Success with alternative model: {alt_model}")
                    return result
            except Exception as e:
                logger.debug(f"Alternative model {alt_model} failed: {e}")
                continue
        
        return None
    
    def _adjust_for_model(self, request: Dict[str, Any], model: str) -> Dict[str, Any]:
        """Adjust parameters for specific model.
        
        Args:
            request: Generation request
            model: Target model
            
        Returns:
            Adjusted request
        """
        # Model-specific adjustments
        if 'lightning' in model.lower():
            # Lightning models are faster but less detailed
            request['num_inference_steps'] = 4
            request['guidance_scale'] = 0
        elif 'turbo' in model.lower():
            # Turbo models need fewer steps
            request['num_inference_steps'] = 1
        elif 'stable-diffusion' in model.lower():
            # SD models have different parameter ranges
            if 'guidance_scale' in request:
                request['guidance_scale'] = min(request['guidance_scale'], 15)
        
        return request
    
    async def _retry_with_adjusted_parameters(
        self,
        context: RetryContext,
        generate_func: Callable
    ) -> Optional[Dict[str, Any]]:
        """Retry with adjusted generation parameters.
        
        Args:
            context: Retry context
            generate_func: Generation function
            
        Returns:
            Result or None
        """
        request = context.original_request.copy()
        
        # Adjustments based on attempt number
        adjustments = [
            {'num_inference_steps': 20},  # Reduce steps
            {'guidance_scale': 3.5},  # Reduce guidance
            {'width': 512, 'height': 512},  # Reduce resolution
            {'num_outputs': 1},  # Reduce outputs
        ]
        
        if context.attempt_number <= len(adjustments):
            adjustment = adjustments[context.attempt_number - 1]
            request.update(adjustment)
            logger.info(f"Retrying with adjusted parameters: {adjustment}")
            
            try:
                result = await generate_func(request)
                return result
            except Exception as e:
                logger.debug(f"Adjusted parameters retry failed: {e}")
        
        return None
    
    async def _fallback_to_generic_asset(
        self,
        context: RetryContext,
        generate_func: Callable
    ) -> Optional[Dict[str, Any]]:
        """Fallback to generic asset generation.
        
        Args:
            context: Retry context
            generate_func: Generation function
            
        Returns:
            Result or None
        """
        asset_type = context.original_request.get('asset_type', 'icon')
        
        # Generic prompts by asset type
        generic_prompts = {
            'icons': 'simple icon, minimalist design, clean lines',
            'covers': 'abstract background, gradient colors, modern design',
            'textures': 'seamless pattern, repeating texture, simple design',
            'letter_headers': 'letterhead design, professional, clean layout',
            'database_icons': 'database icon, simple symbol, flat design'
        }
        
        generic_prompt = generic_prompts.get(asset_type, 'simple design')
        logger.info(f"Falling back to generic {asset_type}: {generic_prompt}")
        
        request = context.original_request.copy()
        request['prompt'] = generic_prompt
        request['num_inference_steps'] = 20  # Faster generation
        request['guidance_scale'] = 3.5  # Lower guidance
        
        try:
            result = await generate_func(request)
            if result:
                # Mark as generic in result
                result['is_generic'] = True
                result['original_prompt'] = context.original_request.get('prompt')
            return result
        except Exception as e:
            logger.error(f"Generic fallback failed: {e}")
            return None
    
    async def analyze_retry_patterns(self) -> Dict[str, Any]:
        """Analyze retry patterns for optimization.
        
        Returns:
            Analysis of retry patterns
        """
        # Get retry statistics from database
        analysis = await self.db.get_retry_statistics()
        
        # Calculate success rates by strategy
        strategy_stats = {}
        for strategy in RetryStrategy:
            strategy_stats[strategy.value] = {
                'attempts': 0,
                'successes': 0,
                'success_rate': 0.0
            }
        
        # Process retry data (would come from database)
        # This is a placeholder for actual database analysis
        
        return {
            'total_retries': analysis.get('total_retries', 0),
            'successful_retries': analysis.get('successful_retries', 0),
            'strategy_statistics': strategy_stats,
            'most_effective_strategy': analysis.get('most_effective_strategy'),
            'average_attempts_to_success': analysis.get('average_attempts', 0)
        }


class CircuitBreaker:
    """Circuit breaker for preventing cascade failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_requests: int = 3
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_requests: Requests to try in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        self.half_open_count = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half_open'
                self.half_open_count = 0
            else:
                raise Exception("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        return (
            self.last_failure_time and
            (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        if self.state == 'half_open':
            self.half_open_count += 1
            if self.half_open_count >= self.half_open_requests:
                self.state = 'closed'
                self.failure_count = 0
                logger.info("Circuit breaker closed")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
        elif self.state == 'half_open':
            self.state = 'open'
            logger.warning("Circuit breaker reopened during half-open state")