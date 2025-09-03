#!/usr/bin/env python3
"""
Estate Planning Concierge v4.0 - Enhanced Asset Generator
Integrates SQLite database, caching, smart retry, and progress tracking.
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Import our new components
from utils.database_manager import DatabaseManager, AssetDatabase
from utils.cache_manager import AssetCache, CachingStrategy
from utils.progress_tracker import ProgressTracker
from utils.smart_retry import SmartRetryManager, CircuitBreaker
from utils.structured_logger import setup_logging, logger, log_execution_time
from services.asset_service import AssetGenerationService, AssetRequest
from services.batch_service import BatchProcessingService, BatchConfig
from utils.transaction_safety import TransactionManager
from models.config_models import ApplicationConfig, BudgetConfig

# Import original components
from prompts import ESTATE_PROMPT_BUILDER


class EnhancedAssetGenerator:
    """Enhanced asset generator with all new features integrated.
    
    Features:
        - SQLite database for tracking
        - Intelligent caching
        - Smart retry with fallbacks
        - Resume capability
        - Structured logging
        - Service layer architecture
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize enhanced generator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Setup structured logging
        self.logger = setup_logging(
            log_level=self.config.get('logging', {}).get('log_level', 'INFO'),
            log_file=self.config.get('logging', {}).get('log_file'),
            json_logs=self.config.get('logging', {}).get('json_logs', False)
        )
        
        # Initialize API client
        self.api_client = self._initialize_api_client()
        
        # Initialize services
        self.asset_service = AssetGenerationService(
            api_client=self.api_client,
            db_path=self.config.get('database', {}).get('path', 'asset_generation.db'),
            cache_dir=self.config.get('cache', {}).get('directory', 'cache/assets'),
            checkpoint_dir=self.config.get('checkpoint', {}).get('directory', '.progress'),
            budget_config=BudgetConfig(**self.config.get('budget', {}))
        )
        
        # Initialize batch service
        batch_config = BatchConfig(
            max_concurrent=self.config.get('batch', {}).get('max_concurrent', 3),
            requests_per_second=self.config.get('batch', {}).get('requests_per_second', 2.0),
            group_by_model=self.config.get('batch', {}).get('group_by_model', True),
            prioritize_uncached=self.config.get('batch', {}).get('prioritize_uncached', True)
        )
        self.batch_service = BatchProcessingService(self.asset_service, batch_config)
        
        # Statistics
        self.stats = {
            'start_time': datetime.now(),
            'total_requested': 0,
            'total_generated': 0,
            'cache_hits': 0,
            'retries': 0,
            'failures': 0
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            # Create default configuration
            default_config = {
                'budget': {
                    'sample_limit': 0.30,
                    'production_limit': 20.00,
                    'daily_limit': 10.00
                },
                'replicate': {
                    'api_key': os.getenv('REPLICATE_API_TOKEN'),
                    'models': {
                        'flux-schnell': {
                            'cost_per_image': 0.003,
                            'timeout': 60
                        },
                        'flux-dev': {
                            'cost_per_image': 0.03,
                            'timeout': 120
                        }
                    }
                },
                'batch': {
                    'max_concurrent': 3,
                    'requests_per_second': 2.0,
                    'group_by_model': True,
                    'prioritize_uncached': True
                },
                'cache': {
                    'directory': 'cache/assets',
                    'max_age_days': 30
                },
                'database': {
                    'path': 'asset_generation.db'
                },
                'checkpoint': {
                    'directory': '.progress',
                    'interval': 10
                },
                'logging': {
                    'log_level': 'INFO',
                    'log_file': 'logs/asset_generation.log',
                    'json_logs': False
                }
            }
            
            # Save default config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _initialize_api_client(self):
        """Initialize Replicate API client."""
        try:
            import replicate
            api_key = self.config.get('replicate', {}).get('api_key') or os.getenv('REPLICATE_API_TOKEN')
            if not api_key:
                raise ValueError("REPLICATE_API_TOKEN not found in config or environment")
            
            # Create a wrapper that matches our service expectations
            class ReplicateClient:
                def __init__(self, api_key):
                    self.client = replicate.Client(api_token=api_key)
                
                async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
                    """Generate asset using Replicate API."""
                    model = request.get('model', 'flux-schnell')
                    prompt = request.get('prompt', '')
                    
                    # Map model names to Replicate model versions
                    model_map = {
                        'flux-schnell': "black-forest-labs/flux-schnell",
                        'flux-dev': "black-forest-labs/flux-dev",
                        'stable-diffusion-xl-base-1.0': "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
                    }
                    
                    model_id = model_map.get(model, model)
                    
                    # Run prediction
                    output = await asyncio.to_thread(
                        self.client.run,
                        model_id,
                        input={
                            "prompt": prompt,
                            "num_inference_steps": request.get('num_inference_steps', 4),
                            "guidance_scale": request.get('guidance_scale', 0),
                            "width": request.get('width', 1024),
                            "height": request.get('height', 1024),
                            "num_outputs": request.get('num_outputs', 1)
                        }
                    )
                    
                    # Format response
                    if isinstance(output, list):
                        output_url = output[0] if output else None
                    else:
                        output_url = output
                    
                    return {
                        'output': [output_url] if output_url else None,
                        'status': 'succeeded' if output_url else 'failed'
                    }
            
            return ReplicateClient(api_key)
            
        except ImportError:
            self.logger.error("Replicate library not installed. Please run: pip install replicate")
            raise
    
    async def initialize(self):
        """Initialize all services."""
        await self.asset_service.initialize()
        self.logger.info("Enhanced Asset Generator initialized")
    
    async def generate_sample_assets(self) -> Dict[str, Any]:
        """Generate sample assets (5-10 for testing)."""
        self.logger.info("Starting SAMPLE generation (5-10 assets)")
        
        # Create sample requests
        requests = []
        
        # 3 sample icons
        for i in range(3):
            prompt = ESTATE_PROMPT_BUILDER.get_icon_prompt(i, 3)
            requests.append(AssetRequest(
                prompt=prompt,
                asset_type='icons',
                index=i + 1,
                total=3,
                model='flux-schnell'
            ))
        
        # 2 sample covers
        for i in range(2):
            prompt = ESTATE_PROMPT_BUILDER.get_cover_prompt(i, 2)
            requests.append(AssetRequest(
                prompt=prompt,
                asset_type='covers',
                index=i + 1,
                total=2,
                model='flux-schnell'
            ))
        
        # Generate with batch service
        run_id = f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.logger.context(run_id=run_id, mode='sample'):
            responses, stats = await self.batch_service.generate_batch(
                requests,
                run_id=run_id
            )
        
        # Log results
        self.logger.info(f"Sample generation complete: {stats['successful']}/{len(requests)} successful")
        self.logger.info(f"Total cost: ${stats['total_cost']:.2f}")
        self.logger.info(f"Cache hits: {stats['cached']}")
        
        return stats
    
    async def generate_production_assets(
        self,
        asset_counts: Optional[Dict[str, int]] = None,
        resume_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate production assets.
        
        Args:
            asset_counts: Optional custom asset counts
            resume_run_id: Optional run ID to resume
            
        Returns:
            Generation statistics
        """
        if asset_counts is None:
            # Default production counts
            asset_counts = {
                'icons': 150,
                'covers': 100,
                'textures': 50,
                'letter_headers': 150,
                'database_icons': 40
            }
        
        total_assets = sum(asset_counts.values())
        self.logger.info(f"Starting PRODUCTION generation ({total_assets} assets)")
        
        # Check if we can resume
        if not resume_run_id:
            resumable_runs = await self.asset_service.progress.list_resumable_runs()
            if resumable_runs:
                self.logger.info(f"Found {len(resumable_runs)} resumable runs:")
                for run in resumable_runs[:3]:  # Show top 3
                    self.logger.info(
                        f"  - {run['run_id']}: {run['completed']}/{run.get('total', '?')} "
                        f"({run.get('progress_percentage', 0):.1f}%) - "
                        f"Age: {run.get('age_hours', 0):.1f}h"
                    )
                
                # Use most recent by default
                resume_run_id = resumable_runs[0]['run_id']
                self.logger.info(f"Resuming run: {resume_run_id}")
        
        # Create requests
        requests = []
        
        for asset_type, count in asset_counts.items():
            for i in range(count):
                # Get appropriate prompt
                if asset_type == 'icons':
                    prompt = ESTATE_PROMPT_BUILDER.get_icon_prompt(i, count)
                elif asset_type == 'covers':
                    prompt = ESTATE_PROMPT_BUILDER.get_cover_prompt(i, count)
                elif asset_type == 'textures':
                    prompt = ESTATE_PROMPT_BUILDER.get_texture_prompt(i, count)
                elif asset_type == 'letter_headers':
                    prompt = ESTATE_PROMPT_BUILDER.get_letter_header_prompt(i, count)
                elif asset_type == 'database_icons':
                    prompt = ESTATE_PROMPT_BUILDER.get_database_icon_prompt(i, count)
                else:
                    prompt = f"Estate planning {asset_type} design {i+1}"
                
                requests.append(AssetRequest(
                    prompt=prompt,
                    asset_type=asset_type,
                    index=i + 1,
                    total=count,
                    model='flux-schnell'  # Using fast model for production
                ))
        
        # Generate with batch service
        run_id = resume_run_id or f"production_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.logger.context(run_id=run_id, mode='production', total=total_assets):
            responses, stats = await self.batch_service.generate_batch(
                requests,
                run_id=run_id,
                resume=bool(resume_run_id)
            )
        
        # Generate summary
        self.logger.info("=" * 60)
        self.logger.info("PRODUCTION GENERATION COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Total requested: {stats['total_requests']}")
        self.logger.info(f"Successfully generated: {stats['successful']}")
        self.logger.info(f"Failed: {stats['failed']}")
        self.logger.info(f"Cache hits: {stats['cached']}")
        self.logger.info(f"Retried: {stats['retried']}")
        self.logger.info(f"Success rate: {stats['success_rate']:.1f}%")
        self.logger.info(f"Total cost: ${stats['total_cost']:.2f}")
        self.logger.info(f"Total time: {stats['elapsed_time']:.1f}s")
        self.logger.info(f"Rate: {stats['requests_per_second']:.2f} req/s")
        
        # Print metrics table
        self.logger.print_metrics_table()
        
        return stats
    
    async def generate_approved_assets(
        self,
        db_path: str = "estate_planning_assets.db",
        resume_run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate assets using human-approved prompts from database.
        
        Args:
            db_path: Path to the approval workflow database
            resume_run_id: Optional run ID to resume
            
        Returns:
            Generation statistics
        """
        # Initialize approval database
        approval_db = AssetDatabase(db_path)
        await approval_db.init_database()
        
        self.logger.info("Starting APPROVED PROMPTS generation")
        
        # Get all approved prompts from database
        approved_prompts = await approval_db.get_approved_prompts()
        
        if not approved_prompts:
            self.logger.warning("No approved prompts found in database")
            return {'error': 'No approved prompts available'}
        
        self.logger.info(f"Found {len(approved_prompts)} approved prompts")
        
        # Check if we can resume
        if not resume_run_id:
            resumable_runs = await self.asset_service.progress.list_resumable_runs()
            if resumable_runs:
                # Look for approved prompts runs
                approved_runs = [r for r in resumable_runs if 'approved' in r['run_id']]
                if approved_runs:
                    resume_run_id = approved_runs[0]['run_id']
                    self.logger.info(f"Resuming approved prompts run: {resume_run_id}")
        
        # Create requests from approved prompts
        requests = []
        
        for prompt_data in approved_prompts:
            # Extract relevant information
            selected_prompt = prompt_data['selected_prompt_text']
            asset_type = prompt_data['asset_type']
            index = prompt_data['index_in_category']
            
            # Apply any custom modifications from human review
            if prompt_data.get('custom_modifications'):
                selected_prompt = f"{selected_prompt}, {prompt_data['custom_modifications']}"
            
            requests.append(AssetRequest(
                prompt=selected_prompt,
                asset_type=asset_type,
                index=index,
                total=len([p for p in approved_prompts if p['asset_type'] == asset_type]),
                model='flux-schnell',  # Using fast model
                metadata={
                    'competition_id': prompt_data['competition_id'],
                    'selected_model': prompt_data['selected_model'],
                    'decision_reasoning': prompt_data.get('decision_reasoning', ''),
                    'reviewer_name': prompt_data.get('reviewer_name', 'Unknown')
                }
            ))
        
        total_assets = len(requests)
        
        # Generate with batch service
        run_id = resume_run_id or f"approved_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.logger.context(run_id=run_id, mode='approved', total=total_assets):
            responses, stats = await self.batch_service.generate_batch(
                requests,
                run_id=run_id,
                resume=bool(resume_run_id)
            )
        
        # Update database with generation results
        for i, response in enumerate(responses):
            if response.get('success') and i < len(approved_prompts):
                prompt_data = approved_prompts[i]
                
                # Mark competition as completed in database
                await approval_db.mark_competition_completed(prompt_data['competition_id'])
        
        # Generate summary
        self.logger.info("=" * 60)
        self.logger.info("APPROVED PROMPTS GENERATION COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Total requested: {stats['total_requests']}")
        self.logger.info(f"Successfully generated: {stats['successful']}")
        self.logger.info(f"Failed: {stats['failed']}")
        self.logger.info(f"Cache hits: {stats['cached']}")
        self.logger.info(f"Retried: {stats['retried']}")
        self.logger.info(f"Success rate: {stats['success_rate']:.1f}%")
        self.logger.info(f"Total cost: ${stats['total_cost']:.2f}")
        self.logger.info(f"Total time: {stats['elapsed_time']:.1f}s")
        self.logger.info(f"Rate: {stats['requests_per_second']:.2f} req/s")
        
        # Print metrics table
        self.logger.print_metrics_table()
        
        await approval_db.close()
        return stats
    
    async def check_cache_status(self) -> Dict[str, Any]:
        """Check cache status and statistics."""
        cache_stats = await self.asset_service.cache.get_cache_stats()
        
        self.logger.info("=" * 60)
        self.logger.info("CACHE STATUS")
        self.logger.info("=" * 60)
        self.logger.info(f"Memory cache size: {cache_stats['memory_cache_size']}")
        self.logger.info(f"Total cached files: {cache_stats['total_cached_files']}")
        self.logger.info(f"Cache size: {cache_stats['cache_size_mb']:.2f} MB")
        
        if cache_stats.get('cached_files_by_type'):
            self.logger.info("Cached by type:")
            for asset_type, count in cache_stats['cached_files_by_type'].items():
                self.logger.info(f"  - {asset_type}: {count}")
        
        return cache_stats
    
    async def cleanup(self):
        """Clean up resources."""
        # Clear old cache
        expired = await self.asset_service.cache.clear_expired()
        if expired > 0:
            self.logger.info(f"Cleared {expired} expired cache entries")
        
        # Clean old checkpoints
        removed = await self.asset_service.progress.cleanup_old_checkpoints(days=7)
        if removed > 0:
            self.logger.info(f"Removed {removed} old checkpoints")
        
        # Get final statistics
        final_stats = await self.asset_service.get_statistics()
        
        # Close services
        await self.asset_service.cleanup()
        
        self.logger.info("Cleanup complete")
        return final_stats


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Enhanced Asset Generator')
    parser.add_argument('--mode', choices=['sample', 'production', 'approved', 'cache-status', 'resume'],
                       default='sample', help='Generation mode')
    parser.add_argument('--config', default='config.json', help='Configuration file')
    parser.add_argument('--resume', help='Resume run ID')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup after generation')
    parser.add_argument('--approval-db', default='estate_planning_assets.db', 
                       help='Path to approval workflow database')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = EnhancedAssetGenerator(args.config)
    await generator.initialize()
    
    try:
        if args.mode == 'sample':
            stats = await generator.generate_sample_assets()
        elif args.mode == 'production':
            stats = await generator.generate_production_assets(resume_run_id=args.resume)
        elif args.mode == 'approved':
            stats = await generator.generate_approved_assets(
                db_path=args.approval_db, 
                resume_run_id=args.resume
            )
        elif args.mode == 'cache-status':
            stats = await generator.check_cache_status()
        elif args.mode == 'resume':
            # List resumable runs
            resumable = await generator.asset_service.progress.list_resumable_runs()
            if resumable:
                print("\nResumable runs:")
                for run in resumable:
                    print(f"  {run['run_id']}: {run['completed']}/{run.get('total', '?')} "
                          f"({run.get('progress_percentage', 0):.1f}%) - "
                          f"Age: {run.get('age_hours', 0):.1f}h")
                
                # Resume most recent
                if input("\nResume most recent? (y/n): ").lower() == 'y':
                    stats = await generator.generate_production_assets(
                        resume_run_id=resumable[0]['run_id']
                    )
            else:
                print("No resumable runs found")
                stats = {}
        
        # Optionally run cleanup
        if args.cleanup:
            await generator.cleanup()
        
        return stats
        
    except KeyboardInterrupt:
        generator.logger.warning("Generation interrupted by user")
        # Save progress
        progress = await generator.asset_service.progress.get_progress()
        generator.logger.info(f"Progress saved: {progress.get('progress_percentage', 0):.1f}% complete")
        generator.logger.info(f"Resume with run ID: {progress.get('run_id')}")
    except Exception as e:
        generator.logger.error(f"Generation failed: {e}", exception=e)
        raise
    finally:
        # Always cleanup on exit
        await generator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())