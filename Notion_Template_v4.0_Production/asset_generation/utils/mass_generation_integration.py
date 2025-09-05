"""
Estate Planning v4.0 - Mass Generation Integration Module
Integrates async downloader and generation queue with safety checks
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from .generation_queue import (
    MassGenerationQueue,
    BatchConfig,
    GenerationTask,
    GenerationPriority,
    GenerationStatus
)
from .async_downloader import AsyncImageDownloader, DownloadTask

logger = logging.getLogger(__name__)

@dataclass
class MassGenerationConfig:
    """Configuration for mass generation operations"""
    # Directory structure
    base_output_dir: Path = Path("output/mass_generation")
    organize_by_user: bool = True
    organize_by_batch: bool = True
    organize_by_timestamp: bool = True
    
    # Safety limits
    max_batch_size: int = 50
    max_total_items: int = 500
    max_total_cost: float = 20.0  # Maximum $20 budget
    require_confirmation: bool = True
    confirmation_threshold: int = 10  # Require confirmation for more than 10 items
    
    # Performance settings
    concurrent_downloads: int = 5
    concurrent_generations: int = 3
    batch_delay_seconds: float = 2.0
    
    # Logging and audit
    enable_audit_log: bool = True
    audit_log_path: Path = Path("logs/mass_generation_audit.json")
    
    # User permissions (placeholder for RBAC)
    allowed_users: List[str] = None
    admin_users: List[str] = None

class MassGenerationCoordinator:
    """Coordinates mass generation with safety checks and user confirmations"""
    
    def __init__(self, config: Optional[MassGenerationConfig] = None):
        """
        Initialize the mass generation coordinator
        
        Args:
            config: Configuration for mass generation
        """
        self.config = config or MassGenerationConfig()
        self.setup_directories()
        
        # Initialize components
        batch_config = BatchConfig(
            batch_size=self.config.max_batch_size,
            batch_delay=self.config.batch_delay_seconds,
            concurrent_limit=self.config.concurrent_generations,
            cost_limit=self.config.max_total_cost / 10  # Per-batch cost limit
        )
        
        self.generation_queue = MassGenerationQueue(batch_config=batch_config)
        self.downloader = AsyncImageDownloader(
            max_concurrent=self.config.concurrent_downloads,
            timeout=60,
            retry_delay=2.0,
            max_retries=3
        )
        
        # Session tracking
        self.current_session = None
        self.audit_log = []
        
    def setup_directories(self):
        """Create directory structure for organized storage"""
        # Create base directories
        self.config.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.config.base_output_dir / "users").mkdir(exist_ok=True)
        (self.config.base_output_dir / "batches").mkdir(exist_ok=True)
        (self.config.base_output_dir / "temp").mkdir(exist_ok=True)
        (self.config.base_output_dir / "failed").mkdir(exist_ok=True)
        
        # Create logs directory
        self.config.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Directory structure established at {self.config.base_output_dir}")
    
    def get_output_path(
        self,
        filename: str,
        user_id: Optional[str] = None,
        batch_id: Optional[str] = None
    ) -> Path:
        """
        Generate organized output path based on configuration
        
        Args:
            filename: Name of the file
            user_id: Optional user identifier
            batch_id: Optional batch identifier
            
        Returns:
            Organized path for the file
        """
        path_parts = [str(self.config.base_output_dir)]
        
        # Add user organization
        if self.config.organize_by_user and user_id:
            path_parts.append(f"users/{user_id}")
        
        # Add batch organization
        if self.config.organize_by_batch and batch_id:
            path_parts.append(f"batches/{batch_id}")
        
        # Add timestamp organization
        if self.config.organize_by_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d")
            path_parts.append(timestamp)
        
        # Create full path
        output_dir = Path("/".join(path_parts))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        return output_dir / filename
    
    async def request_user_confirmation(
        self,
        prompt_count: int,
        estimated_cost: float,
        estimated_time: float
    ) -> bool:
        """
        Request user confirmation for mass generation
        
        Args:
            prompt_count: Number of items to generate
            estimated_cost: Estimated total cost
            estimated_time: Estimated time in minutes
            
        Returns:
            True if user confirms, False otherwise
        """
        if not self.config.require_confirmation:
            return True
        
        if prompt_count <= self.config.confirmation_threshold:
            return True
        
        # In a real implementation, this would show a modal or prompt
        # For now, we'll log the request and return based on safety limits
        confirmation_message = f"""
        ╔════════════════════════════════════════════╗
        ║     MASS GENERATION CONFIRMATION REQUIRED   ║
        ╚════════════════════════════════════════════╝
        
        You are about to generate {prompt_count} images.
        
        Estimated Cost: ${estimated_cost:.2f}
        Estimated Time: {estimated_time:.1f} minutes
        
        Safety Limits:
        - Maximum items: {self.config.max_total_items}
        - Maximum cost: ${self.config.max_total_cost:.2f}
        
        This action will:
        1. Generate {prompt_count} unique images
        2. Download them to organized directories
        3. Create an audit log of all operations
        
        ⚠️  This operation cannot be undone once started.
        """
        
        logger.warning(confirmation_message)
        
        # Check against safety limits
        if prompt_count > self.config.max_total_items:
            logger.error(f"Rejected: {prompt_count} exceeds maximum of {self.config.max_total_items}")
            return False
        
        if estimated_cost > self.config.max_total_cost:
            logger.error(f"Rejected: ${estimated_cost:.2f} exceeds maximum of ${self.config.max_total_cost:.2f}")
            return False
        
        # For integration, we'll need to implement actual user confirmation
        # This could be via web interface, CLI prompt, or API callback
        return True  # Placeholder - would need actual user input
    
    async def validate_prompts(self, prompts: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate prompts for safety and appropriateness
        
        Args:
            prompts: List of prompts to validate
            
        Returns:
            Tuple of (valid_prompts, rejected_prompts)
        """
        valid_prompts = []
        rejected_prompts = []
        
        # Basic safety checks
        forbidden_terms = [
            "inappropriate", "offensive", "violent", "explicit",
            "harmful", "illegal", "dangerous", "weapon"
        ]
        
        for prompt in prompts:
            prompt_lower = prompt.lower()
            
            # Check for forbidden terms
            is_safe = True
            for term in forbidden_terms:
                if term in prompt_lower:
                    rejected_prompts.append(f"{prompt} (contains '{term}')")
                    is_safe = False
                    break
            
            if is_safe:
                # Check prompt length
                if len(prompt) < 10:
                    rejected_prompts.append(f"{prompt} (too short)")
                elif len(prompt) > 1000:
                    rejected_prompts.append(f"{prompt} (too long)")
                else:
                    valid_prompts.append(prompt)
        
        if rejected_prompts:
            logger.warning(f"Rejected {len(rejected_prompts)} prompts during validation")
            for rejected in rejected_prompts[:5]:  # Log first 5
                logger.debug(f"  Rejected: {rejected}")
        
        return valid_prompts, rejected_prompts
    
    async def prepare_mass_generation(
        self,
        prompts: List[str],
        asset_type: str,
        user_id: Optional[str] = None,
        priority: GenerationPriority = GenerationPriority.NORMAL
    ) -> Optional[str]:
        """
        Prepare and validate mass generation request
        
        Args:
            prompts: List of prompts to generate
            asset_type: Type of assets (icons/covers/textures)
            user_id: Optional user identifier
            priority: Generation priority
            
        Returns:
            Batch ID if approved, None if rejected
        """
        # Validate prompts
        valid_prompts, rejected_prompts = await self.validate_prompts(prompts)
        
        if not valid_prompts:
            logger.error("No valid prompts after validation")
            return None
        
        # Estimate cost and time
        cost_per_item = {
            'icons': 0.02,
            'covers': 0.04,
            'textures': 0.03,
            'avatars': 0.05
        }.get(asset_type, 0.03)
        
        estimated_cost = len(valid_prompts) * cost_per_item
        estimated_time = (len(valid_prompts) * 10) / 60  # 10 seconds per item estimate
        
        # Request user confirmation
        confirmed = await self.request_user_confirmation(
            len(valid_prompts),
            estimated_cost,
            estimated_time
        )
        
        if not confirmed:
            logger.info("User cancelled mass generation")
            return None
        
        # Add tasks to queue
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id or 'anonymous'}"
        task_ids = self.generation_queue.add_batch(
            valid_prompts,
            asset_type,
            priority
        )
        
        # Log audit entry
        audit_entry = {
            'batch_id': batch_id,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'asset_type': asset_type,
            'prompt_count': len(valid_prompts),
            'rejected_count': len(rejected_prompts),
            'estimated_cost': estimated_cost,
            'task_ids': task_ids,
            'status': 'prepared'
        }
        
        self.audit_log.append(audit_entry)
        self.save_audit_log()
        
        logger.info(f"Prepared batch {batch_id} with {len(valid_prompts)} tasks")
        return batch_id
    
    async def execute_mass_generation(
        self,
        batch_id: str,
        generator_func: Any,
        progress_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute mass generation with the prepared batch
        
        Args:
            batch_id: Batch ID from preparation
            generator_func: Async function to generate images
            progress_callback: Optional callback for progress updates
            
        Returns:
            Generation results summary
        """
        start_time = datetime.now()
        
        try:
            # Create session
            self.current_session = {
                'batch_id': batch_id,
                'start_time': start_time,
                'status': 'running'
            }
            
            # Process queue
            await self.generation_queue.process_queue(
                generator_func=generator_func,
                progress_callback=progress_callback,
                safety_check_func=self._safety_check
            )
            
            # Get results
            status = self.generation_queue.get_status()
            
            # Download generated images
            download_results = await self._download_generated_images(batch_id)
            
            # Update session
            self.current_session['end_time'] = datetime.now()
            self.current_session['status'] = 'completed'
            self.current_session['results'] = {
                'completed': status['completed_count'],
                'failed': status['failed_count'],
                'downloaded': download_results['successful'],
                'download_failed': download_results['failed'],
                'total_cost': status['statistics']['total_cost']
            }
            
            # Update audit log
            for entry in self.audit_log:
                if entry['batch_id'] == batch_id:
                    entry['status'] = 'completed'
                    entry['results'] = self.current_session['results']
                    entry['duration'] = str(datetime.now() - start_time)
            
            self.save_audit_log()
            
            return self.current_session['results']
            
        except Exception as e:
            logger.error(f"Mass generation failed: {e}")
            if self.current_session:
                self.current_session['status'] = 'failed'
                self.current_session['error'] = str(e)
            raise
        
        finally:
            # Export results
            results_path = self.config.base_output_dir / f"{batch_id}_results.json"
            self.generation_queue.export_results(results_path)
    
    async def _safety_check(self, prompt: str) -> Tuple[bool, str]:
        """Internal safety check for queue processing"""
        valid, rejected = await self.validate_prompts([prompt])
        if valid:
            return True, "OK"
        return False, rejected[0] if rejected else "Failed validation"
    
    async def _download_generated_images(self, batch_id: str) -> Dict[str, Any]:
        """Download all generated images for a batch"""
        # Get completed tasks
        completed_tasks = self.generation_queue.completed_tasks
        
        # Prepare download tasks
        download_tasks = []
        for task_id, gen_task in completed_tasks.items():
            if gen_task.result:
                # Assume result contains image URL
                image_url = gen_task.result
                filename = f"{task_id}.png"
                filepath = self.get_output_path(
                    filename,
                    batch_id=batch_id
                )
                
                dl_task = DownloadTask(
                    url=image_url,
                    filepath=filepath,
                    task_id=task_id
                )
                download_tasks.append(dl_task)
        
        # Execute downloads
        if download_tasks:
            results = await self.downloader.download_batch(download_tasks)
            
            successful = sum(1 for t in results if t.status.value == "completed")
            failed = sum(1 for t in results if t.status.value == "failed")
            
            return {
                'successful': successful,
                'failed': failed,
                'total': len(results)
            }
        
        return {'successful': 0, 'failed': 0, 'total': 0}
    
    def save_audit_log(self):
        """Save audit log to file"""
        if self.config.enable_audit_log:
            try:
                with open(self.config.audit_log_path, 'w') as f:
                    json.dump(self.audit_log, f, indent=2, default=str)
                logger.debug(f"Audit log saved to {self.config.audit_log_path}")
            except Exception as e:
                logger.error(f"Failed to save audit log: {e}")
    
    def get_user_permissions(self, user_id: str) -> Dict[str, bool]:
        """
        Check user permissions for mass generation
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary of permissions
        """
        # Placeholder for RBAC implementation
        is_admin = self.config.admin_users and user_id in self.config.admin_users
        is_allowed = (
            not self.config.allowed_users or
            user_id in self.config.allowed_users or
            is_admin
        )
        
        return {
            'can_generate': is_allowed,
            'can_mass_generate': is_allowed,
            'can_override_limits': is_admin,
            'max_items': self.config.max_total_items if not is_admin else 1000,
            'max_cost': self.config.max_total_cost if not is_admin else 100.0
        }
    
    async def cleanup(self):
        """Clean up resources"""
        await self.downloader.cleanup()
        logger.info("Mass generation coordinator cleaned up")

# Example usage
async def example_usage():
    """Example of using the mass generation coordinator"""
    
    # Configure mass generation
    config = MassGenerationConfig(
        base_output_dir=Path("output/mass_generation"),
        max_total_items=100,
        max_total_cost=5.0,
        require_confirmation=True,
        confirmation_threshold=5
    )
    
    # Create coordinator
    coordinator = MassGenerationCoordinator(config)
    
    # Example prompts
    prompts = [
        "Professional estate planning icon with trust symbolism",
        "Warm family heritage illustration",
        "Secure document protection symbol",
        "Peaceful transition imagery",
        "Modern technology bridge concept"
    ]
    
    # Prepare mass generation
    batch_id = await coordinator.prepare_mass_generation(
        prompts=prompts,
        asset_type="icons",
        user_id="test_user",
        priority=GenerationPriority.NORMAL
    )
    
    if batch_id:
        print(f"Batch {batch_id} prepared for generation")
        
        # Mock generator function
        async def mock_generator(prompt: str, asset_type: str, metadata: Dict):
            await asyncio.sleep(1)  # Simulate API call
            return f"https://example.com/generated_{metadata.get('batch_index', 0)}.png"
        
        # Execute generation
        results = await coordinator.execute_mass_generation(
            batch_id=batch_id,
            generator_func=mock_generator
        )
        
        print(f"Generation complete: {results}")
    
    # Cleanup
    await coordinator.cleanup()

if __name__ == "__main__":
    asyncio.run(example_usage())