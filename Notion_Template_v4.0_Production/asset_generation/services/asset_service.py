"""Asset generation service with clean separation of concerns.

Provides a high-level interface for asset generation with integrated
caching, retry logic, progress tracking, and cost management.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import uuid

from ..utils.database_manager import DatabaseManager
from ..utils.cache_manager import AssetCache, CachingStrategy
from ..utils.progress_tracker import ProgressTracker, CheckpointStatus
from ..utils.smart_retry import SmartRetryManager, CircuitBreaker
from ..utils.transaction_safety import TransactionManager
from ..utils.async_file_handler import AsyncFileHandler
from ..utils.path_validator import PathValidator
from ..models.config_models import BudgetConfig

logger = logging.getLogger(__name__)


@dataclass
class AssetRequest:
    """Request for asset generation."""
    prompt: str
    asset_type: str
    index: int
    total: int
    model: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    force_regenerate: bool = False
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def estimated_cost(self) -> float:
        """Estimate generation cost."""
        # Model-specific cost estimates
        model_costs = {
            'flux-schnell': 0.003,
            'flux-dev': 0.03,
            'stable-diffusion-xl-base-1.0': 0.00125,
            'sdxl-lightning-4step': 0.0006,
        }
        return model_costs.get(self.model or 'flux-schnell', 0.003)


@dataclass
class AssetResponse:
    """Response from asset generation."""
    success: bool
    path: Optional[Path] = None
    url: Optional[str] = None
    cost: float = 0.0
    cached: bool = False
    is_generic: bool = False
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    generation_time: float = 0.0


class AssetGenerationService:
    """Main service for asset generation with all integrated features.
    
    Features:
        - Cache-first generation
        - Smart retry with fallbacks
        - Progress tracking and resume
        - Cost management
        - Circuit breaker protection
        - Parallel processing
    """
    
    def __init__(
        self,
        api_client,  # ReplicateClient instance
        db_path: str = "asset_generation.db",
        cache_dir: str = "cache/assets",
        checkpoint_dir: str = ".progress",
        budget_config: Optional[BudgetConfig] = None
    ):
        """Initialize asset generation service.
        
        Args:
            api_client: API client for generation
            db_path: Path to SQLite database
            cache_dir: Directory for cached assets
            checkpoint_dir: Directory for checkpoints
            budget_config: Budget configuration
        """
        self.api_client = api_client
        
        # Initialize components
        self.db = DatabaseManager(db_path)
        self.cache = AssetCache(self.db, Path(cache_dir))
        self.caching_strategy = CachingStrategy(self.cache)
        self.progress = ProgressTracker(self.db, Path(checkpoint_dir))
        self.retry_manager = SmartRetryManager(self.db)
        self.transaction_manager = TransactionManager(budget_config)
        self.file_handler = AsyncFileHandler()
        self.path_validator = PathValidator()
        
        # Circuit breaker for API protection
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        
        # Rate limiting
        self._last_request_time = None
        self._min_request_interval = 0.5  # seconds between requests
        
        # Statistics
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'retries_attempted': 0,
            'retries_successful': 0,
            'generic_fallbacks': 0
        }
    
    async def initialize(self) -> None:
        """Initialize service components."""
        await self.db.initialize()
        await self.cache.warm_cache(recent_hours=24)
        logger.info("Asset generation service initialized")
    
    async def generate_asset(self, request: AssetRequest) -> AssetResponse:
        """Generate a single asset with all features.
        
        Args:
            request: Asset generation request
            
        Returns:
            AssetResponse with generation result
        """
        start_time = datetime.now()
        
        try:
            # Rate limiting
            await self._enforce_rate_limit()
            
            # Check cache first unless forced regeneration
            if not request.force_regenerate:
                use_cache, cached_path = await self.caching_strategy.should_use_cache(
                    request.prompt,
                    request.asset_type,
                    force_regenerate=False
                )
                
                if use_cache and cached_path:
                    self.stats['cache_hits'] += 1
                    logger.info(f"Cache hit for {request.asset_type} {request.index}/{request.total}")
                    
                    # Record in progress tracker
                    await self.progress.checkpoint(
                        asset_type=request.asset_type,
                        index=request.index,
                        total=request.total,
                        status=CheckpointStatus.COMPLETED,
                        cost=0.0,
                        prompt=request.prompt,
                        output_path=str(cached_path)
                    )
                    
                    return AssetResponse(
                        success=True,
                        path=cached_path,
                        cost=0.0,
                        cached=True,
                        generation_time=(datetime.now() - start_time).total_seconds()
                    )
            
            self.stats['cache_misses'] += 1
            
            # Check budget before generation
            can_afford, remaining = await self.transaction_manager.check_budget(
                request.estimated_cost
            )
            if not can_afford:
                logger.error(f"Budget exceeded. Remaining: ${remaining:.2f}")
                return AssetResponse(
                    success=False,
                    error=f"Budget exceeded. Remaining: ${remaining:.2f}"
                )
            
            # Generate with circuit breaker protection
            result = await self.circuit_breaker.call(
                self._generate_with_retry,
                request
            )
            
            if result:
                generation_time = (datetime.now() - start_time).total_seconds()
                
                # Cache the result
                if result.get('path'):
                    await self.cache.store(
                        prompt=request.prompt,
                        asset_type=request.asset_type,
                        file_path=Path(result['path']),
                        model=request.model,
                        cost=result.get('cost', 0.0),
                        metadata={
                            'generation_time': generation_time,
                            'is_generic': result.get('is_generic', False)
                        }
                    )
                
                # Record in progress tracker
                await self.progress.checkpoint(
                    asset_type=request.asset_type,
                    index=request.index,
                    total=request.total,
                    status=CheckpointStatus.COMPLETED,
                    cost=result.get('cost', 0.0),
                    prompt=request.prompt,
                    output_path=result.get('path')
                )
                
                # Record transaction
                await self.transaction_manager.record_transaction(
                    asset_type=request.asset_type,
                    cost=result.get('cost', 0.0),
                    success=True
                )
                
                if result.get('is_generic'):
                    self.stats['generic_fallbacks'] += 1
                
                return AssetResponse(
                    success=True,
                    path=Path(result['path']) if result.get('path') else None,
                    url=result.get('url'),
                    cost=result.get('cost', 0.0),
                    is_generic=result.get('is_generic', False),
                    generation_time=generation_time
                )
            else:
                # Generation failed
                await self.progress.checkpoint(
                    asset_type=request.asset_type,
                    index=request.index,
                    total=request.total,
                    status=CheckpointStatus.FAILED,
                    prompt=request.prompt,
                    error="Generation failed after retries"
                )
                
                return AssetResponse(
                    success=False,
                    error="Generation failed after all retry attempts"
                )
                
        except Exception as e:
            logger.error(f"Asset generation error: {e}")
            
            # Record failure
            await self.progress.checkpoint(
                asset_type=request.asset_type,
                index=request.index,
                total=request.total,
                status=CheckpointStatus.FAILED,
                prompt=request.prompt,
                error=str(e)
            )
            
            return AssetResponse(
                success=False,
                error=str(e)
            )
    
    async def _generate_with_retry(self, request: AssetRequest) -> Optional[Dict[str, Any]]:
        """Generate asset with retry logic.
        
        Args:
            request: Asset generation request
            
        Returns:
            Generation result or None
        """
        # Prepare API request
        api_request = {
            'prompt': request.prompt,
            'asset_type': request.asset_type,
            'model': request.model or 'flux-schnell',
            **(request.parameters or {})
        }
        
        try:
            # Try initial generation
            result = await self.api_client.generate(api_request)
            
            if result and result.get('output'):
                # Download the generated image
                output_url = result['output'][0] if isinstance(result['output'], list) else result['output']
                
                # Generate unique filename
                filename = f"{request.asset_type}_{request.index}_{uuid.uuid4().hex[:8]}.png"
                output_path = Path('output') / request.asset_type / filename
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Download with transaction safety
                await self.file_handler.download_file(output_url, output_path)
                
                return {
                    'path': str(output_path),
                    'url': output_url,
                    'cost': request.estimated_cost,
                    'is_generic': False
                }
            else:
                raise Exception("No output from API")
                
        except Exception as e:
            logger.warning(f"Initial generation failed: {e}")
            self.stats['retries_attempted'] += 1
            
            # Try retry strategies
            result = await self.retry_manager.retry_with_strategies(
                api_request,
                self._generate_api_call,
                error=e
            )
            
            if result:
                self.stats['retries_successful'] += 1
                return result
            
            return None
    
    async def _generate_api_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Make API call for generation.
        
        Args:
            request: API request
            
        Returns:
            API response
        """
        result = await self.api_client.generate(request)
        
        if result and result.get('output'):
            output_url = result['output'][0] if isinstance(result['output'], list) else result['output']
            
            # Generate filename
            asset_type = request.get('asset_type', 'asset')
            filename = f"{asset_type}_{uuid.uuid4().hex[:8]}.png"
            output_path = Path('output') / asset_type / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            await self.file_handler.download_file(output_url, output_path)
            
            return {
                'path': str(output_path),
                'url': output_url,
                'cost': 0.003,  # Default cost estimate
                'is_generic': request.get('is_generic', False)
            }
        
        raise Exception("No output from API")
    
    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self._min_request_interval:
                await asyncio.sleep(self._min_request_interval - elapsed)
        
        self._last_request_time = datetime.now()
    
    async def generate_batch(
        self,
        requests: List[AssetRequest],
        max_concurrent: int = 3,
        run_id: Optional[str] = None
    ) -> List[AssetResponse]:
        """Generate multiple assets in batch.
        
        Args:
            requests: List of asset requests
            max_concurrent: Maximum concurrent generations
            run_id: Optional run ID for tracking
            
        Returns:
            List of generation responses
        """
        if not run_id:
            run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start progress tracking
        total_assets = len(requests)
        await self.progress.start_run(run_id, total_assets)
        
        # Check for resumable run
        if await self.progress.can_resume(run_id):
            last_index, state = await self.progress.resume_run(run_id)
            # Skip already completed assets
            requests = requests[last_index:]
            logger.info(f"Resuming from index {last_index}")
        
        responses = []
        
        # Process in batches with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(request):
            async with semaphore:
                return await self.generate_asset(request)
        
        # Create tasks for parallel processing
        tasks = [generate_with_semaphore(req) for req in requests]
        
        # Process with progress updates
        for i, task in enumerate(asyncio.as_completed(tasks)):
            response = await task
            responses.append(response)
            
            # Log progress periodically
            if (i + 1) % 10 == 0:
                progress = await self.progress.get_progress()
                logger.info(
                    f"Batch progress: {progress['completed']}/{total_assets} "
                    f"({progress.get('progress_percentage', 0):.1f}%) "
                    f"- ETA: {progress.get('eta_formatted', 'unknown')}"
                )
        
        # Complete run
        final_stats = await self.progress.complete_run()
        logger.info(f"Batch generation complete: {final_stats}")
        
        return responses
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        cache_stats = await self.cache.get_cache_stats()
        progress_stats = await self.progress.get_progress()
        retry_analysis = await self.retry_manager.analyze_retry_patterns()
        
        return {
            'service_stats': self.stats,
            'cache_stats': cache_stats,
            'progress_stats': progress_stats,
            'retry_analysis': retry_analysis,
            'circuit_breaker_state': self.circuit_breaker.state,
            'database_stats': await self.db.get_statistics()
        }
    
    async def cleanup(self) -> None:
        """Clean up service resources."""
        # Clean old checkpoints
        await self.progress.cleanup_old_checkpoints(days=7)
        
        # Clear expired cache
        await self.cache.clear_expired()
        
        # Close database
        await self.db.close()
        
        logger.info("Asset generation service cleaned up")