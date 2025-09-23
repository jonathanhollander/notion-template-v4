"""
Estate Planning v4.0 - Mass Generation Queue System
Manages efficient batching and queueing of image generation requests
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from enum import Enum
from queue import PriorityQueue
import logging
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class GenerationPriority(Enum):
    """Priority levels for generation tasks"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4

class GenerationStatus(Enum):
    """Status of generation tasks"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class GenerationTask:
    """Represents a single generation task"""
    task_id: str
    prompt: str
    asset_type: str
    priority: GenerationPriority = GenerationPriority.NORMAL
    status: GenerationStatus = GenerationStatus.QUEUED
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """For priority queue comparison"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at

@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    batch_size: int = 5
    batch_delay: float = 1.0  # Delay between batches
    rate_limit: int = 10  # Requests per minute
    concurrent_limit: int = 3  # Concurrent API calls
    cost_limit: float = 10.0  # Maximum cost per batch
    safety_check: bool = True  # Enable prompt safety checks

class MassGenerationQueue:
    """Manages queuing and batch processing of generation tasks"""
    
    def __init__(
        self,
        batch_config: Optional[BatchConfig] = None,
        rate_limiter: Optional[Any] = None,
        cost_tracker: Optional[Any] = None
    ):
        """
        Initialize the generation queue
        
        Args:
            batch_config: Batch processing configuration
            rate_limiter: Rate limiting implementation
            cost_tracker: Cost tracking implementation
        """
        self.batch_config = batch_config or BatchConfig()
        self.rate_limiter = rate_limiter
        self.cost_tracker = cost_tracker
        
        # Queue management
        self.task_queue = asyncio.Queue()
        self.priority_queue = PriorityQueue()
        self.active_tasks: Dict[str, GenerationTask] = {}
        self.completed_tasks: Dict[str, GenerationTask] = {}
        self.failed_tasks: Dict[str, GenerationTask] = {}
        
        # Processing state
        self.is_processing = False
        self.processing_task = None
        self.semaphore = asyncio.Semaphore(self.batch_config.concurrent_limit)
        
        # Statistics
        self.stats = {
            'total_queued': 0,
            'total_processed': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_cancelled': 0,
            'total_cost': 0.0,
            'total_time': 0.0,
            'batches_processed': 0
        }
    
    def add_task(self, task: GenerationTask) -> str:
        """
        Add a task to the queue
        
        Args:
            task: Generation task to add
            
        Returns:
            Task ID
        """
        self.priority_queue.put(task)
        self.stats['total_queued'] += 1
        logger.info(f"Added task {task.task_id} to queue with priority {task.priority.name}")
        return task.task_id
    
    def add_batch(self, prompts: List[str], asset_type: str, priority: GenerationPriority = GenerationPriority.NORMAL) -> List[str]:
        """
        Add multiple tasks as a batch
        
        Args:
            prompts: List of prompts to generate
            asset_type: Type of asset to generate
            priority: Priority level for the batch
            
        Returns:
            List of task IDs
        """
        task_ids = []
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        for i, prompt in enumerate(prompts):
            task = GenerationTask(
                task_id=f"{batch_id}_{i:04d}",
                prompt=prompt,
                asset_type=asset_type,
                priority=priority,
                metadata={'batch_id': batch_id, 'batch_index': i}
            )
            task_ids.append(self.add_task(task))
        
        logger.info(f"Added batch {batch_id} with {len(prompts)} tasks")
        return task_ids
    
    async def process_queue(
        self,
        generator_func: Callable,
        progress_callback: Optional[Callable] = None,
        safety_check_func: Optional[Callable] = None
    ):
        """
        Process the queue with batching and rate limiting
        
        Args:
            generator_func: Async function to generate images
            progress_callback: Optional callback for progress updates
            safety_check_func: Optional function to validate prompts
        """
        self.is_processing = True
        
        try:
            while not self.priority_queue.empty() or self.active_tasks:
                # Collect batch of tasks
                batch = []
                batch_cost = 0.0
                
                while len(batch) < self.batch_config.batch_size and not self.priority_queue.empty():
                    task = self.priority_queue.get()
                    
                    # Safety check if enabled
                    if self.batch_config.safety_check and safety_check_func:
                        is_safe, reason = await safety_check_func(task.prompt)
                        if not is_safe:
                            task.status = GenerationStatus.FAILED
                            task.error = f"Safety check failed: {reason}"
                            self.failed_tasks[task.task_id] = task
                            logger.warning(f"Task {task.task_id} failed safety check: {reason}")
                            continue
                    
                    # Cost check
                    estimated_cost = self._estimate_cost(task)
                    if batch_cost + estimated_cost > self.batch_config.cost_limit:
                        # Put task back if it exceeds cost limit
                        self.priority_queue.put(task)
                        break
                    
                    batch.append(task)
                    batch_cost += estimated_cost
                    self.active_tasks[task.task_id] = task
                
                if batch:
                    # Process batch
                    logger.info(f"Processing batch of {len(batch)} tasks (estimated cost: ${batch_cost:.2f})")
                    
                    # Rate limiting
                    if self.rate_limiter:
                        await self.rate_limiter.acquire()
                    
                    # Process tasks concurrently within batch
                    batch_results = await self._process_batch(
                        batch,
                        generator_func,
                        progress_callback
                    )
                    
                    # Update statistics
                    self.stats['batches_processed'] += 1
                    self.stats['total_cost'] += batch_cost
                    
                    # Delay between batches
                    await asyncio.sleep(self.batch_config.batch_delay)
                
                # Check for stalled active tasks
                await self._check_stalled_tasks()
                
                # Small delay if queue is empty but active tasks remain
                if self.priority_queue.empty() and self.active_tasks:
                    await asyncio.sleep(0.5)
        
        finally:
            self.is_processing = False
            logger.info("Queue processing completed")
    
    async def _process_batch(
        self,
        batch: List[GenerationTask],
        generator_func: Callable,
        progress_callback: Optional[Callable]
    ) -> List[GenerationTask]:
        """Process a batch of tasks concurrently"""
        async def process_single_task(task: GenerationTask):
            async with self.semaphore:
                task.status = GenerationStatus.PROCESSING
                task.started_at = time.time()
                
                try:
                    # Call generator function
                    result = await generator_func(
                        prompt=task.prompt,
                        asset_type=task.asset_type,
                        metadata=task.metadata
                    )
                    
                    task.result = result
                    task.status = GenerationStatus.COMPLETED
                    task.completed_at = time.time()
                    
                    # Move to completed
                    self.completed_tasks[task.task_id] = task
                    del self.active_tasks[task.task_id]
                    
                    self.stats['total_completed'] += 1
                    
                    if progress_callback:
                        progress_callback(task.task_id, 'completed', result)
                    
                    logger.info(f"Task {task.task_id} completed successfully")
                    
                except Exception as e:
                    task.error = str(e)
                    task.retry_count += 1
                    
                    if task.retry_count < task.max_retries:
                        # Retry with lower priority
                        task.status = GenerationStatus.QUEUED
                        task.priority = GenerationPriority(min(task.priority.value + 1, GenerationPriority.BACKGROUND.value))
                        self.priority_queue.put(task)
                        del self.active_tasks[task.task_id]
                        logger.warning(f"Task {task.task_id} failed, retrying ({task.retry_count}/{task.max_retries})")
                    else:
                        # Move to failed
                        task.status = GenerationStatus.FAILED
                        task.completed_at = time.time()
                        self.failed_tasks[task.task_id] = task
                        del self.active_tasks[task.task_id]
                        self.stats['total_failed'] += 1
                        
                        if progress_callback:
                            progress_callback(task.task_id, 'failed', str(e))
                        
                        logger.error(f"Task {task.task_id} failed after {task.retry_count} attempts: {e}")
                
                self.stats['total_processed'] += 1
                return task
        
        # Process all tasks in batch concurrently
        results = await asyncio.gather(
            *[process_single_task(task) for task in batch],
            return_exceptions=True
        )
        
        return [r for r in results if not isinstance(r, Exception)]
    
    async def _check_stalled_tasks(self):
        """Check for and handle stalled tasks"""
        current_time = time.time()
        stalled_timeout = 300  # 5 minutes
        
        for task_id, task in list(self.active_tasks.items()):
            if task.started_at and (current_time - task.started_at) > stalled_timeout:
                logger.warning(f"Task {task_id} appears stalled, requeueing")
                task.status = GenerationStatus.QUEUED
                task.retry_count += 1
                self.priority_queue.put(task)
                del self.active_tasks[task_id]
    
    def _estimate_cost(self, task: GenerationTask) -> float:
        """Estimate cost for a generation task"""
        # Base costs per asset type (example values)
        cost_map = {
            'icons': 0.02,
            'covers': 0.04,
            'textures': 0.03,
            'avatars': 0.05
        }
        return cost_map.get(task.asset_type, 0.03)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a queued task
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if cancelled, False if not found or already processing
        """
        # Check if task is in priority queue
        temp_queue = []
        cancelled = False
        
        while not self.priority_queue.empty():
            task = self.priority_queue.get()
            if task.task_id == task_id:
                task.status = GenerationStatus.CANCELLED
                self.stats['total_cancelled'] += 1
                cancelled = True
                logger.info(f"Cancelled task {task_id}")
            else:
                temp_queue.append(task)
        
        # Restore queue
        for task in temp_queue:
            self.priority_queue.put(task)
        
        return cancelled
    
    def get_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            'is_processing': self.is_processing,
            'queued_count': self.priority_queue.qsize(),
            'active_count': len(self.active_tasks),
            'completed_count': len(self.completed_tasks),
            'failed_count': len(self.failed_tasks),
            'statistics': self.stats,
            'config': {
                'batch_size': self.batch_config.batch_size,
                'rate_limit': self.batch_config.rate_limit,
                'concurrent_limit': self.batch_config.concurrent_limit,
                'cost_limit': self.batch_config.cost_limit
            }
        }
    
    def get_task_status(self, task_id: str) -> Optional[GenerationTask]:
        """Get status of a specific task"""
        # Check all task collections
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        if task_id in self.failed_tasks:
            return self.failed_tasks[task_id]
        return None
    
    def export_results(self, output_path: Path) -> Dict[str, Any]:
        """Export queue results to file"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'completed': {
                task_id: {
                    'prompt': task.prompt,
                    'asset_type': task.asset_type,
                    'duration': task.completed_at - task.started_at if task.started_at else 0,
                    'result': task.result
                }
                for task_id, task in self.completed_tasks.items()
            },
            'failed': {
                task_id: {
                    'prompt': task.prompt,
                    'asset_type': task.asset_type,
                    'error': task.error,
                    'retry_count': task.retry_count
                }
                for task_id, task in self.failed_tasks.items()
            }
        }
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Exported results to {output_path}")
        return results

# Example usage
async def example_usage():
    """Example of using the mass generation queue"""
    
    # Configure batch processing
    config = BatchConfig(
        batch_size=3,
        batch_delay=2.0,
        rate_limit=10,
        concurrent_limit=2,
        cost_limit=5.0,
        safety_check=True
    )
    
    # Create queue
    queue = MassGenerationQueue(batch_config=config)
    
    # Add tasks
    prompts = [
        "A professional icon for estate planning",
        "A warm family heritage illustration",
        "A secure document protection symbol",
        "A peaceful transition imagery",
        "A modern technology bridge concept"
    ]
    
    task_ids = queue.add_batch(prompts, "icons", GenerationPriority.NORMAL)
    print(f"Added {len(task_ids)} tasks to queue")
    
    # Mock generator function
    async def mock_generator(prompt: str, asset_type: str, metadata: Dict):
        await asyncio.sleep(1)  # Simulate API call
        return f"generated_{asset_type}_{metadata.get('batch_index', 0)}.png"
    
    # Mock safety check
    async def mock_safety_check(prompt: str) -> Tuple[bool, str]:
        # Simple example - reject prompts with certain keywords
        forbidden_words = ['inappropriate', 'offensive']
        for word in forbidden_words:
            if word in prompt.lower():
                return False, f"Contains forbidden word: {word}"
        return True, "OK"
    
    # Progress callback
    def progress_callback(task_id: str, status: str, result: Any):
        print(f"Task {task_id}: {status} - {result}")
    
    # Process queue
    await queue.process_queue(
        generator_func=mock_generator,
        progress_callback=progress_callback,
        safety_check_func=mock_safety_check
    )
    
    # Get status
    status = queue.get_status()
    print(f"\nQueue Status:")
    print(f"Completed: {status['completed_count']}")
    print(f"Failed: {status['failed_count']}")
    print(f"Total cost: ${status['statistics']['total_cost']:.2f}")
    
    # Export results
    queue.export_results(Path("generation_results.json"))

if __name__ == "__main__":
    asyncio.run(example_usage())