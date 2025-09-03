"""Batch processing service for efficient asset generation.

Optimizes batch generation through intelligent grouping, parallel processing,
and rate limiting.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, AsyncIterator
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass
import uuid

from ..services.asset_service import AssetGenerationService, AssetRequest, AssetResponse
from ..utils.progress_tracker import ProgressTracker
from ..utils.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    max_concurrent: int = 3
    requests_per_second: float = 2.0
    group_by_model: bool = True
    prioritize_uncached: bool = True
    enable_progress_bar: bool = True
    checkpoint_interval: int = 10
    retry_failed: bool = True
    

class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(self, requests_per_second: float = 2.0):
        """Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            
            self.last_request_time = asyncio.get_event_loop().time()
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.acquire()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class BatchProcessingService:
    """Service for optimized batch asset generation.
    
    Features:
        - Intelligent request grouping
        - Parallel processing with rate limiting
        - Progress tracking with resume capability
        - Priority-based processing
        - Failed request retry
    """
    
    def __init__(
        self,
        asset_service: AssetGenerationService,
        config: Optional[BatchConfig] = None
    ):
        """Initialize batch processing service.
        
        Args:
            asset_service: Asset generation service
            config: Batch processing configuration
        """
        self.asset_service = asset_service
        self.config = config or BatchConfig()
        self.rate_limiter = RateLimiter(self.config.requests_per_second)
        
        # Statistics
        self.batch_stats = {
            'total_batches': 0,
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'cached': 0,
            'retried': 0
        }
    
    def group_by_model(self, requests: List[AssetRequest]) -> Dict[str, List[AssetRequest]]:
        """Group requests by model for efficiency.
        
        Args:
            requests: List of asset requests
            
        Returns:
            Dictionary mapping model to requests
        """
        grouped = defaultdict(list)
        
        for request in requests:
            model = request.model or 'flux-schnell'
            grouped[model].append(request)
        
        logger.info(f"Grouped {len(requests)} requests into {len(grouped)} model groups")
        for model, reqs in grouped.items():
            logger.debug(f"  {model}: {len(reqs)} requests")
        
        return grouped
    
    async def prioritize_requests(self, requests: List[AssetRequest]) -> List[AssetRequest]:
        """Prioritize requests based on caching and other factors.
        
        Args:
            requests: List of asset requests
            
        Returns:
            Prioritized list of requests
        """
        if not self.config.prioritize_uncached:
            return requests
        
        # Check cache status for each request
        cached_requests = []
        uncached_requests = []
        
        for request in requests:
            cached_path = await self.asset_service.cache.check_exists(
                request.prompt,
                request.asset_type,
                request.model
            )
            
            if cached_path and not request.force_regenerate:
                cached_requests.append(request)
            else:
                uncached_requests.append(request)
        
        # Process uncached first (they take longer)
        prioritized = uncached_requests + cached_requests
        
        logger.info(f"Prioritized {len(uncached_requests)} uncached, {len(cached_requests)} cached requests")
        
        return prioritized
    
    async def generate_batch(
        self,
        requests: List[AssetRequest],
        run_id: Optional[str] = None,
        resume: bool = True
    ) -> Tuple[List[AssetResponse], Dict[str, Any]]:
        """Process batch of asset generation requests.
        
        Args:
            requests: List of asset requests
            run_id: Optional run ID for tracking
            resume: Whether to resume interrupted batch
            
        Returns:
            Tuple of (responses, statistics)
        """
        start_time = datetime.now()
        
        if not run_id:
            run_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        self.batch_stats['total_batches'] += 1
        self.batch_stats['total_requests'] += len(requests)
        
        logger.info(f"Starting batch {run_id} with {len(requests)} requests")
        
        # Initialize progress tracking
        await self.asset_service.progress.start_run(
            run_id=run_id,
            total_assets=len(requests),
            mode='batch',
            metadata={'batch_config': self.config.__dict__}
        )
        
        # Check for resume
        start_index = 0
        if resume and await self.asset_service.progress.can_resume(run_id):
            start_index, state = await self.asset_service.progress.resume_run(run_id)
            logger.info(f"Resuming batch from index {start_index}")
            requests = requests[start_index:]
        
        # Group and prioritize requests
        if self.config.group_by_model:
            grouped = self.group_by_model(requests)
        else:
            grouped = {'all': requests}
        
        # Process each group
        all_responses = []
        failed_requests = []
        
        for model, model_requests in grouped.items():
            logger.info(f"Processing {len(model_requests)} requests for model: {model}")
            
            # Prioritize within group
            prioritized = await self.prioritize_requests(model_requests)
            
            # Process with parallel execution
            responses = await self._process_parallel(
                prioritized,
                run_id,
                start_index
            )
            
            # Collect results
            for request, response in zip(prioritized, responses):
                all_responses.append(response)
                
                if response.success:
                    self.batch_stats['successful'] += 1
                    if response.cached:
                        self.batch_stats['cached'] += 1
                else:
                    self.batch_stats['failed'] += 1
                    failed_requests.append(request)
            
            start_index += len(model_requests)
        
        # Retry failed requests if configured
        if self.config.retry_failed and failed_requests:
            logger.info(f"Retrying {len(failed_requests)} failed requests")
            retry_responses = await self._retry_failed(failed_requests)
            
            # Update responses
            for i, response in enumerate(all_responses):
                if not response.success:
                    # Find corresponding retry response
                    for retry_response in retry_responses:
                        # Match by some criteria (simplified here)
                        all_responses[i] = retry_response
                        if retry_response.success:
                            self.batch_stats['retried'] += 1
                            self.batch_stats['successful'] += 1
                            self.batch_stats['failed'] -= 1
                        break
        
        # Complete run and get statistics
        final_stats = await self.asset_service.progress.complete_run()
        
        # Calculate batch statistics
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        batch_statistics = {
            'run_id': run_id,
            'total_requests': len(requests) + start_index,
            'processed': len(all_responses),
            'successful': self.batch_stats['successful'],
            'failed': self.batch_stats['failed'],
            'cached': self.batch_stats['cached'],
            'retried': self.batch_stats['retried'],
            'total_cost': final_stats.get('total_cost', 0),
            'elapsed_time': elapsed_time,
            'requests_per_second': len(all_responses) / elapsed_time if elapsed_time > 0 else 0,
            'success_rate': (self.batch_stats['successful'] / max(len(all_responses), 1)) * 100
        }
        
        logger.info(f"Batch {run_id} complete:")
        logger.info(f"  Processed: {batch_statistics['processed']}")
        logger.info(f"  Success rate: {batch_statistics['success_rate']:.1f}%")
        logger.info(f"  Total cost: ${batch_statistics['total_cost']:.2f}")
        logger.info(f"  Time: {batch_statistics['elapsed_time']:.1f}s")
        
        return all_responses, batch_statistics
    
    async def _process_parallel(
        self,
        requests: List[AssetRequest],
        run_id: str,
        start_index: int
    ) -> List[AssetResponse]:
        """Process requests in parallel with rate limiting.
        
        Args:
            requests: List of asset requests
            run_id: Run ID for tracking
            start_index: Starting index for progress
            
        Returns:
            List of responses
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def process_with_rate_limit(request: AssetRequest, index: int):
            """Process single request with rate limiting."""
            async with semaphore:
                async with self.rate_limiter:
                    # Update request index for progress tracking
                    request.index = start_index + index + 1
                    response = await self.asset_service.generate_asset(request)
                    
                    # Checkpoint periodically
                    if (index + 1) % self.config.checkpoint_interval == 0:
                        progress = await self.asset_service.progress.get_progress()
                        logger.info(
                            f"Checkpoint at {index + 1}: "
                            f"{progress.get('progress_percentage', 0):.1f}% complete"
                        )
                    
                    return response
        
        # Create tasks
        tasks = [
            process_with_rate_limit(request, i)
            for i, request in enumerate(requests)
        ]
        
        # Execute with progress tracking
        if self.config.enable_progress_bar:
            responses = await self._process_with_progress(tasks)
        else:
            responses = await asyncio.gather(*tasks)
        
        return responses
    
    async def _process_with_progress(self, tasks: List) -> List[AssetResponse]:
        """Process tasks with progress bar.
        
        Args:
            tasks: List of async tasks
            
        Returns:
            List of responses
        """
        responses = []
        total = len(tasks)
        
        # Simple text progress (tqdm not imported to avoid dependency)
        for i, task in enumerate(asyncio.as_completed(tasks)):
            response = await task
            responses.append(response)
            
            # Update progress
            progress = ((i + 1) / total) * 100
            bar_length = 40
            filled = int(bar_length * (i + 1) / total)
            bar = '█' * filled + '░' * (bar_length - filled)
            
            print(f'\rProgress: [{bar}] {progress:.1f}% ({i + 1}/{total})', end='', flush=True)
        
        print()  # New line after progress bar
        
        return responses
    
    async def _retry_failed(self, failed_requests: List[AssetRequest]) -> List[AssetResponse]:
        """Retry failed requests.
        
        Args:
            failed_requests: List of failed requests
            
        Returns:
            List of retry responses
        """
        retry_responses = []
        
        for request in failed_requests:
            # Simple retry with delay
            await asyncio.sleep(2)
            
            try:
                response = await self.asset_service.generate_asset(request)
                retry_responses.append(response)
            except Exception as e:
                logger.error(f"Retry failed for request: {e}")
                retry_responses.append(
                    AssetResponse(
                        success=False,
                        error=f"Retry failed: {str(e)}"
                    )
                )
        
        return retry_responses
    
    async def generate_stream(
        self,
        requests: List[AssetRequest],
        chunk_size: int = 10
    ) -> AsyncIterator[AssetResponse]:
        """Generate assets in streaming fashion.
        
        Args:
            requests: List of asset requests
            chunk_size: Size of chunks to process
            
        Yields:
            Asset responses as they complete
        """
        # Process in chunks
        for i in range(0, len(requests), chunk_size):
            chunk = requests[i:i + chunk_size]
            
            # Process chunk
            tasks = [
                self.asset_service.generate_asset(request)
                for request in chunk
            ]
            
            # Yield results as they complete
            for task in asyncio.as_completed(tasks):
                response = await task
                yield response
    
    async def optimize_batch(
        self,
        requests: List[AssetRequest],
        target_cost: Optional[float] = None,
        target_time: Optional[float] = None
    ) -> List[AssetRequest]:
        """Optimize batch for cost or time constraints.
        
        Args:
            requests: List of asset requests
            target_cost: Target maximum cost
            target_time: Target maximum time
            
        Returns:
            Optimized list of requests
        """
        optimized = []
        estimated_cost = 0.0
        estimated_time = 0.0
        
        # Sort by priority (could be customized)
        sorted_requests = sorted(
            requests,
            key=lambda r: (r.force_regenerate, r.asset_type, r.index)
        )
        
        for request in sorted_requests:
            # Estimate cost and time
            req_cost = request.estimated_cost
            req_time = 2.0  # Estimated seconds per request
            
            # Check constraints
            if target_cost and estimated_cost + req_cost > target_cost:
                logger.info(f"Cost limit reached: ${estimated_cost:.2f}/{target_cost:.2f}")
                break
            
            if target_time and estimated_time + req_time > target_time:
                logger.info(f"Time limit reached: {estimated_time:.1f}s/{target_time:.1f}s")
                break
            
            optimized.append(request)
            estimated_cost += req_cost
            estimated_time += req_time
        
        logger.info(
            f"Optimized batch: {len(optimized)}/{len(requests)} requests, "
            f"Est. cost: ${estimated_cost:.2f}, Est. time: {estimated_time:.1f}s"
        )
        
        return optimized
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get batch processing statistics.
        
        Returns:
            Dictionary with batch statistics
        """
        return {
            **self.batch_stats,
            'average_success_rate': (
                (self.batch_stats['successful'] / 
                 max(self.batch_stats['total_requests'], 1)) * 100
            ),
            'cache_hit_rate': (
                (self.batch_stats['cached'] / 
                 max(self.batch_stats['successful'], 1)) * 100
            ),
            'retry_success_rate': (
                (self.batch_stats['retried'] / 
                 max(self.batch_stats['failed'], 1)) * 100
                if self.batch_stats['failed'] > 0 else 0
            )
        }