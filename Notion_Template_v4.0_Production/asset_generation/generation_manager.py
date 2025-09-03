#!/usr/bin/env python3
"""
Generation Manager for Estate Planning Concierge v4.0
Handles background asset generation with real-time status tracking
"""

import os
import json
import time
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Import existing asset generation modules
from asset_generator import AssetGenerator
from sample_generator import SampleGenerator


class GenerationStatus(Enum):
    """Generation job status enumeration"""
    PENDING = "pending"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class GenerationJob:
    """Data class for tracking generation jobs"""
    job_id: str
    job_type: str  # "sample" or "full"
    status: GenerationStatus
    total_images: int
    completed_images: int
    progress_percent: float
    estimated_cost: float
    actual_cost: float
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_directory: Optional[str] = None
    generation_config: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class GenerationManager:
    """Manages background asset generation jobs with real-time monitoring"""
    
    def __init__(self, db_path: str = "estate_planning_assets.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Job tracking
        self.active_jobs: Dict[str, GenerationJob] = {}
        self.job_history: List[GenerationJob] = []
        self.current_job_id: Optional[str] = None
        
        # Generation instances
        self.asset_generator: Optional[AssetGenerator] = None
        self.sample_generator: Optional[SampleGenerator] = None
        
        # Callbacks for real-time updates
        self.progress_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.status_callbacks: List[Callable[[str, GenerationStatus], None]] = []
        
        # Thread management
        self.generation_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
    def register_progress_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Register a callback for progress updates"""
        self.progress_callbacks.append(callback)
    
    def register_status_callback(self, callback: Callable[[str, GenerationStatus], None]):
        """Register a callback for status changes"""
        self.status_callbacks.append(callback)
    
    def _notify_progress(self, job_id: str, progress_data: Dict[str, Any]):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(job_id, progress_data)
            except Exception as e:
                self.logger.error(f"Progress callback error: {e}")
    
    def _notify_status_change(self, job_id: str, status: GenerationStatus):
        """Notify all status callbacks"""
        for callback in self.status_callbacks:
            try:
                callback(job_id, status)
            except Exception as e:
                self.logger.error(f"Status callback error: {e}")
    
    def create_sample_job(self, max_images: int = 10, output_dir: Optional[str] = None) -> str:
        """Create a new sample generation job"""
        job_id = f"sample_{int(time.time())}"
        
        if output_dir is None:
            output_dir = f"output/samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        job = GenerationJob(
            job_id=job_id,
            job_type="sample",
            status=GenerationStatus.PENDING,
            total_images=max_images,
            completed_images=0,
            progress_percent=0.0,
            estimated_cost=max_images * 0.04,  # Approximate cost per image
            actual_cost=0.0,
            output_directory=output_dir,
            generation_config={
                "max_images": max_images,
                "output_directory": output_dir,
                "mode": "sample"
            }
        )
        
        self.active_jobs[job_id] = job
        self.logger.info(f"Created sample job {job_id} for {max_images} images")
        return job_id
    
    def create_full_job(self, output_dir: Optional[str] = None) -> str:
        """Create a new full generation job"""
        job_id = f"full_{int(time.time())}"
        
        if output_dir is None:
            output_dir = f"output/full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Estimate based on known asset count (approximately 490 assets)
        estimated_images = 490
        estimated_cost = estimated_images * 0.04  # Approximate cost per image
        
        job = GenerationJob(
            job_id=job_id,
            job_type="full",
            status=GenerationStatus.PENDING,
            total_images=estimated_images,
            completed_images=0,
            progress_percent=0.0,
            estimated_cost=estimated_cost,
            actual_cost=0.0,
            output_directory=output_dir,
            generation_config={
                "output_directory": output_dir,
                "mode": "full"
            }
        )
        
        self.active_jobs[job_id] = job
        self.logger.info(f"Created full job {job_id} for ~{estimated_images} images (est. ${estimated_cost:.2f})")
        return job_id
    
    def start_job(self, job_id: str) -> bool:
        """Start a generation job in background thread"""
        if job_id not in self.active_jobs:
            self.logger.error(f"Job {job_id} not found")
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status != GenerationStatus.PENDING:
            self.logger.error(f"Job {job_id} is not in pending state: {job.status}")
            return False
        
        # Check if another job is running
        if self.current_job_id and self.current_job_id in self.active_jobs:
            current_job = self.active_jobs[self.current_job_id]
            if current_job.status == GenerationStatus.RUNNING:
                self.logger.error(f"Job {self.current_job_id} is already running")
                return False
        
        # Start the job
        self.current_job_id = job_id
        job.status = GenerationStatus.INITIALIZING
        job.started_at = datetime.now()
        
        # Create and start background thread
        self.stop_event.clear()
        self.generation_thread = threading.Thread(
            target=self._run_generation,
            args=(job_id,),
            daemon=True
        )
        self.generation_thread.start()
        
        self.logger.info(f"Started job {job_id}")
        self._notify_status_change(job_id, GenerationStatus.INITIALIZING)
        return True
    
    def _run_generation(self, job_id: str):
        """Run generation in background thread"""
        job = self.active_jobs[job_id]
        
        try:
            job.status = GenerationStatus.RUNNING
            self._notify_status_change(job_id, GenerationStatus.RUNNING)
            
            if job.job_type == "sample":
                self._run_sample_generation(job)
            else:
                self._run_full_generation(job)
            
            if not self.stop_event.is_set():
                job.status = GenerationStatus.COMPLETED
                job.completed_at = datetime.now()
                self.logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            job.status = GenerationStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self.logger.error(f"Job {job_id} failed: {e}")
        
        finally:
            # Move to history
            self.job_history.append(job)
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
            
            if self.current_job_id == job_id:
                self.current_job_id = None
            
            self._notify_status_change(job_id, job.status)
    
    def _run_sample_generation(self, job: GenerationJob):
        """Run sample generation with progress tracking"""
        config = job.generation_config
        max_images = config.get("max_images", 10)
        output_dir = config.get("output_directory")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize sample generator
        if not self.sample_generator:
            self.sample_generator = SampleGenerator()
        
        # Run actual sample generation
        try:
            # Generate samples using the SampleGenerator
            results = self.sample_generator.generate_samples(
                max_images=max_images,
                output_dir=output_dir,
                progress_callback=lambda completed, total: self._update_job_progress(
                    job, completed, total
                )
            )
            
            job.completed_images = len(results) if results else 0
            job.progress_percent = 100 if job.completed_images > 0 else 0
            job.actual_cost = sum(r.get('cost', 0.04) for r in results) if results else 0
            
            progress_data = {
                "completed": job.completed_images,
                "total": job.total_images,
                "progress": job.progress_percent,
                "cost": job.actual_cost,
                "estimated_cost": job.estimated_cost
            }
            
            self._notify_progress(job.job_id, progress_data)
            self.logger.info(f"Job {job.job_id}: {job.completed_images}/{job.total_images} images")
            
        except Exception as e:
            self.logger.error(f"Sample generation failed: {e}")
            job.error_message = str(e)
            job.status = GenerationStatus.FAILED
    
    def _run_full_generation(self, job: GenerationJob):
        """Run full generation with progress tracking"""
        output_dir = job.generation_config.get("output_directory")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize asset generator
        if not self.asset_generator:
            self.asset_generator = AssetGenerator()
        
        # Run actual full generation
        try:
            # Run mass production using the AssetGenerator
            results = self.asset_generator.mass_generate_assets(
                progress_callback=lambda completed, total: self._update_job_progress(
                    job, completed, total
                )
            )
            
            job.completed_images = len(results) if results else 0
            job.progress_percent = 100 if job.completed_images > 0 else 0
            job.actual_cost = self.asset_generator.total_cost if self.asset_generator else 0
            
            progress_data = {
                "completed": job.completed_images,
                "total": job.total_images,
                "progress": job.progress_percent,
                "cost": job.actual_cost,
                "estimated_cost": job.estimated_cost
            }
            
            self._notify_progress(job.job_id, progress_data)
            
            # Log every 10 images to avoid spam
            if job.completed_images % 10 == 0:
                self.logger.info(f"Job {job.job_id}: {job.completed_images}/{job.total_images} images")
                
        except Exception as e:
            self.logger.error(f"Full generation failed: {e}")
            job.error_message = str(e)
            job.status = GenerationStatus.FAILED
    
    def _update_job_progress(self, job: GenerationJob, completed: int, total: int):
        """Helper to update job progress from callbacks"""
        job.completed_images = completed
        job.total_images = total
        job.progress_percent = (completed / total * 100) if total > 0 else 0
        
        progress_data = {
            "completed": completed,
            "total": total,
            "progress": job.progress_percent,
            "cost": job.actual_cost,
            "estimated_cost": job.estimated_cost
        }
        
        self._notify_progress(job.job_id, progress_data)
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status not in [GenerationStatus.RUNNING, GenerationStatus.INITIALIZING]:
            return False
        
        # Signal the generation thread to stop
        self.stop_event.set()
        
        job.status = GenerationStatus.CANCELLED
        job.completed_at = datetime.now()
        
        self.logger.info(f"Job {job_id} cancelled")
        self._notify_status_change(job_id, GenerationStatus.CANCELLED)
        
        return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id].to_dict()
        
        # Check history
        for job in self.job_history:
            if job.job_id == job_id:
                return job.to_dict()
        
        return None
    
    def get_active_jobs(self) -> List[Dict[str, Any]]:
        """Get all active jobs"""
        return [job.to_dict() for job in self.active_jobs.values()]
    
    def get_job_history(self) -> List[Dict[str, Any]]:
        """Get job history"""
        return [job.to_dict() for job in self.job_history]
    
    def get_current_job(self) -> Optional[Dict[str, Any]]:
        """Get currently running job"""
        if self.current_job_id and self.current_job_id in self.active_jobs:
            return self.active_jobs[self.current_job_id].to_dict()
        return None