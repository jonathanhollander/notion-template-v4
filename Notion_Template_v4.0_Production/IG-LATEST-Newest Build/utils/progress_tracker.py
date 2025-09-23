"""Progress tracking and resume capability for asset generation.

Tracks generation progress in real-time and enables resuming interrupted
runs from the last successful checkpoint.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles

from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class CheckpointStatus(Enum):
    """Status of a checkpoint."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESUMED = "resumed"


@dataclass
class Checkpoint:
    """Represents a checkpoint in the generation process."""
    run_id: str
    asset_type: str
    index: int
    total: int
    status: CheckpointStatus
    timestamp: datetime
    cost_so_far: float
    prompt: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary."""
        data = asdict(self)
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create checkpoint from dictionary."""
        data['status'] = CheckpointStatus(data['status'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


class ProgressTracker:
    """Tracks and manages generation progress with resume capability.
    
    Features:
        - Real-time progress tracking
        - Automatic checkpointing
        - Resume from interruption
        - Progress statistics
        - Cost tracking
        - ETA calculation
    """
    
    def __init__(
        self,
        db_manager: DatabaseManager,
        checkpoint_dir: Path = Path(".progress"),
        checkpoint_interval: int = 5
    ):
        """Initialize progress tracker.
        
        Args:
            db_manager: Database manager instance
            checkpoint_dir: Directory for checkpoint files
            checkpoint_interval: Save checkpoint every N assets
        """
        self.db = db_manager
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_interval = checkpoint_interval
        
        # Current state
        self.current_run_id: Optional[str] = None
        self.checkpoints: List[Checkpoint] = []
        self.start_time: Optional[datetime] = None
        self.last_checkpoint_time: Optional[datetime] = None
        
        # Statistics
        self.completed_count = 0
        self.failed_count = 0
        self.total_cost = 0.0
        self.average_time_per_asset = 0.0
        
        # Ensure checkpoint directory exists
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    async def start_run(
        self,
        run_id: str,
        total_assets: int,
        mode: str = "production",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new generation run.
        
        Args:
            run_id: Unique run identifier
            total_assets: Total number of assets to generate
            mode: Generation mode (sample/production)
            metadata: Additional run metadata
            
        Returns:
            Run ID for tracking
        """
        self.current_run_id = run_id
        self.start_time = datetime.now()
        self.completed_count = 0
        self.failed_count = 0
        self.total_cost = 0.0
        
        # Save initial checkpoint
        checkpoint_file = self.checkpoint_dir / f"{run_id}.json"
        initial_state = {
            'run_id': run_id,
            'total_assets': total_assets,
            'mode': mode,
            'start_time': self.start_time.isoformat(),
            'status': 'started',
            'completed': 0,
            'failed': 0,
            'total_cost': 0.0,
            'metadata': metadata or {}
        }
        
        async with aiofiles.open(checkpoint_file, 'w') as f:
            await f.write(json.dumps(initial_state, indent=2))
        
        logger.info(f"Started run {run_id} for {total_assets} assets")
        return run_id
    
    async def can_resume(self, run_id: Optional[str] = None) -> bool:
        """Check if a run can be resumed.
        
        Args:
            run_id: Specific run ID to check, or check for any resumable run
            
        Returns:
            True if resumable run exists
        """
        if run_id:
            checkpoint_file = self.checkpoint_dir / f"{run_id}.json"
            if checkpoint_file.exists():
                async with aiofiles.open(checkpoint_file, 'r') as f:
                    state = json.loads(await f.read())
                return state.get('status') not in ['completed', 'cancelled']
            return False
        else:
            # Check for any resumable run
            for checkpoint_file in self.checkpoint_dir.glob("*.json"):
                async with aiofiles.open(checkpoint_file, 'r') as f:
                    state = json.loads(await f.read())
                if state.get('status') not in ['completed', 'cancelled']:
                    return True
            return False
    
    async def resume_run(self, run_id: str) -> Tuple[int, Dict[str, Any]]:
        """Resume an interrupted run.
        
        Args:
            run_id: Run ID to resume
            
        Returns:
            Tuple of (last_completed_index, run_state)
        """
        checkpoint_file = self.checkpoint_dir / f"{run_id}.json"
        if not checkpoint_file.exists():
            raise FileNotFoundError(f"No checkpoint found for run {run_id}")
        
        # Load checkpoint
        async with aiofiles.open(checkpoint_file, 'r') as f:
            state = json.loads(await f.read())
        
        # Get resume point from database
        last_index, db_state = await self.db.get_resume_point(run_id)
        
        # Update internal state
        self.current_run_id = run_id
        self.start_time = datetime.fromisoformat(state['start_time'])
        self.completed_count = state.get('completed', 0)
        self.failed_count = state.get('failed', 0)
        self.total_cost = state.get('total_cost', 0.0)
        
        # Mark as resumed
        state['status'] = 'resumed'
        state['resumed_at'] = datetime.now().isoformat()
        state['resume_index'] = last_index
        
        async with aiofiles.open(checkpoint_file, 'w') as f:
            await f.write(json.dumps(state, indent=2))
        
        logger.info(f"Resumed run {run_id} from index {last_index}")
        logger.info(f"Progress: {self.completed_count} completed, {self.failed_count} failed, ${self.total_cost:.2f} spent")
        
        return last_index, state
    
    async def checkpoint(
        self,
        asset_type: str,
        index: int,
        total: int,
        status: CheckpointStatus,
        cost: float = 0.0,
        prompt: Optional[str] = None,
        output_path: Optional[str] = None,
        error: Optional[str] = None
    ) -> None:
        """Save a checkpoint after asset generation.
        
        Args:
            asset_type: Type of asset generated
            index: Current index
            total: Total assets
            status: Checkpoint status
            cost: Cost of this generation
            prompt: Generation prompt
            output_path: Output file path
            error: Error message if failed
        """
        if not self.current_run_id:
            logger.warning("No active run to checkpoint")
            return
        
        # Create checkpoint
        checkpoint = Checkpoint(
            run_id=self.current_run_id,
            asset_type=asset_type,
            index=index,
            total=total,
            status=status,
            timestamp=datetime.now(),
            cost_so_far=self.total_cost + cost,
            prompt=prompt,
            output_path=output_path,
            error=error
        )
        
        self.checkpoints.append(checkpoint)
        
        # Update statistics
        if status == CheckpointStatus.COMPLETED:
            self.completed_count += 1
            self.total_cost += cost
        elif status == CheckpointStatus.FAILED:
            self.failed_count += 1
        
        # Calculate average time
        if self.completed_count > 0 and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.average_time_per_asset = elapsed / self.completed_count
        
        # Save checkpoint periodically or on important events
        should_save = (
            index % self.checkpoint_interval == 0 or
            status == CheckpointStatus.FAILED or
            index == total
        )
        
        if should_save:
            await self._save_checkpoint(checkpoint)
    
    async def _save_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Save checkpoint to file.
        
        Args:
            checkpoint: Checkpoint to save
        """
        if not self.current_run_id:
            return
        
        checkpoint_file = self.checkpoint_dir / f"{self.current_run_id}.json"
        
        # Load existing state
        if checkpoint_file.exists():
            async with aiofiles.open(checkpoint_file, 'r') as f:
                state = json.loads(await f.read())
        else:
            state = {
                'run_id': self.current_run_id,
                'start_time': self.start_time.isoformat() if self.start_time else None
            }
        
        # Update state
        state.update({
            'last_checkpoint': checkpoint.to_dict(),
            'completed': self.completed_count,
            'failed': self.failed_count,
            'total_cost': self.total_cost,
            'last_update': datetime.now().isoformat(),
            'status': 'in_progress' if checkpoint.index < checkpoint.total else 'completed',
            'progress_percentage': round((checkpoint.index / checkpoint.total) * 100, 2)
        })
        
        # Add ETA if possible
        if self.average_time_per_asset > 0:
            remaining = checkpoint.total - checkpoint.index
            eta_seconds = remaining * self.average_time_per_asset
            state['eta_seconds'] = round(eta_seconds)
            state['eta_formatted'] = str(timedelta(seconds=int(eta_seconds)))
        
        # Save to file
        async with aiofiles.open(checkpoint_file, 'w') as f:
            await f.write(json.dumps(state, indent=2))
        
        self.last_checkpoint_time = datetime.now()
        
        # Log progress
        if checkpoint.index % 10 == 0 or checkpoint.status == CheckpointStatus.FAILED:
            logger.info(
                f"Progress: {checkpoint.index}/{checkpoint.total} "
                f"({state.get('progress_percentage', 0):.1f}%) "
                f"- Cost: ${self.total_cost:.2f}"
            )
            if 'eta_formatted' in state:
                logger.info(f"ETA: {state['eta_formatted']}")
    
    async def get_progress(self) -> Dict[str, Any]:
        """Get current progress statistics.
        
        Returns:
            Dictionary with progress information
        """
        if not self.current_run_id:
            return {'status': 'no_active_run'}
        
        elapsed_time = None
        if self.start_time:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        # Get latest checkpoint
        latest_checkpoint = self.checkpoints[-1] if self.checkpoints else None
        
        progress = {
            'run_id': self.current_run_id,
            'completed': self.completed_count,
            'failed': self.failed_count,
            'total_cost': round(self.total_cost, 2),
            'elapsed_seconds': round(elapsed_time) if elapsed_time else 0,
            'average_time_per_asset': round(self.average_time_per_asset, 2),
            'checkpoints_saved': len(self.checkpoints)
        }
        
        if latest_checkpoint:
            progress['current_index'] = latest_checkpoint.index
            progress['total_assets'] = latest_checkpoint.total
            progress['progress_percentage'] = round(
                (latest_checkpoint.index / latest_checkpoint.total) * 100, 2
            )
            
            # Calculate ETA
            if self.average_time_per_asset > 0:
                remaining = latest_checkpoint.total - latest_checkpoint.index
                eta_seconds = remaining * self.average_time_per_asset
                progress['eta_seconds'] = round(eta_seconds)
                progress['eta_formatted'] = str(timedelta(seconds=int(eta_seconds)))
        
        return progress
    
    async def complete_run(self) -> Dict[str, Any]:
        """Mark run as completed and return final statistics.
        
        Returns:
            Final run statistics
        """
        if not self.current_run_id:
            return {'status': 'no_active_run'}
        
        checkpoint_file = self.checkpoint_dir / f"{self.current_run_id}.json"
        
        # Calculate final statistics
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds() if self.start_time else 0
        
        final_stats = {
            'run_id': self.current_run_id,
            'status': 'completed',
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': end_time.isoformat(),
            'total_time_seconds': round(total_time),
            'total_time_formatted': str(timedelta(seconds=int(total_time))),
            'completed': self.completed_count,
            'failed': self.failed_count,
            'success_rate': round((self.completed_count / max(self.completed_count + self.failed_count, 1)) * 100, 2),
            'total_cost': round(self.total_cost, 2),
            'average_cost_per_asset': round(self.total_cost / max(self.completed_count, 1), 4),
            'average_time_per_asset': round(self.average_time_per_asset, 2)
        }
        
        # Save final state
        if checkpoint_file.exists():
            async with aiofiles.open(checkpoint_file, 'r') as f:
                state = json.loads(await f.read())
            state.update(final_stats)
            async with aiofiles.open(checkpoint_file, 'w') as f:
                await f.write(json.dumps(state, indent=2))
        
        logger.info(f"Run {self.current_run_id} completed:")
        logger.info(f"  Total time: {final_stats['total_time_formatted']}")
        logger.info(f"  Success rate: {final_stats['success_rate']}%")
        logger.info(f"  Total cost: ${final_stats['total_cost']}")
        
        # Reset state
        self.current_run_id = None
        self.checkpoints.clear()
        
        return final_stats
    
    async def list_resumable_runs(self) -> List[Dict[str, Any]]:
        """List all resumable runs.
        
        Returns:
            List of resumable run information
        """
        resumable = []
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                async with aiofiles.open(checkpoint_file, 'r') as f:
                    state = json.loads(await f.read())
                
                if state.get('status') not in ['completed', 'cancelled']:
                    run_info = {
                        'run_id': state.get('run_id'),
                        'status': state.get('status'),
                        'completed': state.get('completed', 0),
                        'failed': state.get('failed', 0),
                        'total_cost': state.get('total_cost', 0.0),
                        'last_update': state.get('last_update'),
                        'progress_percentage': state.get('progress_percentage', 0)
                    }
                    
                    # Add age of checkpoint
                    if run_info['last_update']:
                        last_update = datetime.fromisoformat(run_info['last_update'])
                        age = datetime.now() - last_update
                        run_info['age_hours'] = round(age.total_seconds() / 3600, 1)
                    
                    resumable.append(run_info)
                    
            except Exception as e:
                logger.error(f"Error reading checkpoint {checkpoint_file}: {e}")
        
        # Sort by last update (most recent first)
        resumable.sort(key=lambda x: x.get('last_update', ''), reverse=True)
        
        return resumable
    
    async def cleanup_old_checkpoints(self, days: int = 7) -> int:
        """Clean up old checkpoint files.
        
        Args:
            days: Remove checkpoints older than this many days
            
        Returns:
            Number of checkpoints removed
        """
        removed = 0
        cutoff = datetime.now() - timedelta(days=days)
        
        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                async with aiofiles.open(checkpoint_file, 'r') as f:
                    state = json.loads(await f.read())
                
                # Check if completed and old
                if state.get('status') == 'completed':
                    last_update = state.get('last_update')
                    if last_update:
                        update_time = datetime.fromisoformat(last_update)
                        if update_time < cutoff:
                            checkpoint_file.unlink()
                            removed += 1
                            logger.debug(f"Removed old checkpoint: {checkpoint_file.name}")
                            
            except Exception as e:
                logger.error(f"Error cleaning checkpoint {checkpoint_file}: {e}")
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} old checkpoints")
        
        return removed