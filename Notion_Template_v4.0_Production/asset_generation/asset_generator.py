#!/usr/bin/env python3
"""
Estate Planning Concierge v4.0 - Asset Generator
Comprehensive asset generation with real-time logging and status updates
"""

import os
import sys
import json
import time
import logging
import logging.handlers
import asyncio
import replicate
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from colorama import init, Fore, Back, Style
from tqdm import tqdm
from tqdm.asyncio import tqdm as atqdm
from git_operations import GitOperations
from sync_yaml_comprehensive import sync_with_yaml as comprehensive_sync

# Initialize colorama for cross-platform colored output
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for different log levels"""
    
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "🔍 %(asctime)s [DEBUG] %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "✅ %(asctime)s [INFO] %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "⚠️  %(asctime)s [WARN] %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "❌ %(asctime)s [ERROR] %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Back.WHITE + "🚨 %(asctime)s [CRITICAL] %(message)s" + Style.RESET_ALL
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(asctime)s [%(levelname)s] %(message)s")
        formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)

class AssetGenerator:
    """Main asset generator with comprehensive logging and status tracking"""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the generator with configuration"""
        self.start_time = time.time()
        self.total_cost = 0.0
        self.errors = []
        self.generated_assets = []
        self.generation_stats = {
            'icons_generated': 0,
            'covers_generated': 0,
            'textures_generated': 0,
            'regenerated_count': 0,
            'total_cost': 0.0,
            'generation_mode': 'sample'
        }
        
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize Replicate client
        self.setup_replicate()
        
        # Log initialization
        self.logger.info("=" * 80)
        self.logger.info("ESTATE PLANNING CONCIERGE v4.0 - ASSET GENERATOR")
        self.logger.info("=" * 80)
        self.logger.info(f"Configuration loaded from: {config_path}")
        self.logger.info(f"Sample budget: ${self.config['budget']['sample_generation']['max_cost']:.2f}")
        self.logger.info(f"Production budget: ${self.config['budget']['mass_generation']['max_cost']:.2f}")
        self.logger.info(f"Review server port: {self.config['review']['port']}")
        self.logger.info("=" * 80)
    
    def load_config(self, config_path: str) -> Dict:
        """Load configuration from JSON file"""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Expand environment variables
        api_key = config['replicate']['api_key']
        if api_key.startswith('${') and api_key.endswith('}'):
            env_var = api_key[2:-1]
            config['replicate']['api_key'] = os.getenv(env_var, '')
        
        return config
    
    def setup_logging(self):
        """Setup comprehensive logging with colors and file output"""
        # Create logger
        self.logger = logging.getLogger('AssetGenerator')
        self.logger.setLevel(getattr(logging, self.config['logging']['level']))
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler
        log_file = Path(self.config['logging']['log_file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config['logging']['max_log_size'],
            backupCount=self.config['logging']['backup_count']
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def setup_replicate(self):
        """Initialize Replicate client"""
        api_key = self.config['replicate']['api_key']
        if not api_key:
            raise ValueError("REPLICATE_API_KEY not found in environment or config")
        
        os.environ['REPLICATE_API_TOKEN'] = api_key
        self.logger.info("✓ Replicate API client initialized")
    
    def sync_with_yaml(self) -> Dict[str, List[Dict]]:
        """Use comprehensive YAML sync with fallback parsing for malformed files"""
        self.logger.info("Using comprehensive YAML sync with fallback parsing...")
        
        try:
            # Use the comprehensive sync function that handles all parsing
            pages_by_type = comprehensive_sync()
        except ValueError as e:
            # YAML parsing failed - STOP THE SCRIPT
            self.logger.error("="*80)
            self.logger.error("CRITICAL ERROR: YAML PARSING FAILED")
            self.logger.error("="*80)
            self.logger.error(str(e))
            self.logger.error("="*80)
            self.logger.error("Script cannot continue without all YAML files.")
            self.logger.error("Please fix the YAML errors and try again.")
            self.logger.error("="*80)
            sys.exit(1)  # Exit with error code
        except Exception as e:
            self.logger.error(f"Unexpected error during YAML sync: {e}")
            sys.exit(1)
        
        # Log the results
        self.logger.info("="*80)
        self.logger.info("COMPREHENSIVE YAML SYNC COMPLETE")
        self.logger.info("="*80)
        self.logger.info("Assets discovered:")
        for asset_type, items in pages_by_type.items():
            self.logger.info(f"  - {asset_type}: {len(items)}")
        self.logger.info(f"  - TOTAL ASSETS: {sum(len(v) for v in pages_by_type.values())}")
        self.logger.info("="*80)
        
        return pages_by_type
    
    def print_status(self, stage: str, message: str, level: str = "info"):
        """Print formatted status message with timestamp and cost"""
        elapsed = time.time() - self.start_time
        elapsed_str = f"{elapsed:.1f}s"
        cost_str = f"${self.total_cost:.3f}"
        
        status_line = f"[{elapsed_str}] [{cost_str}] {stage}: {message}"
        
        if level == "error":
            self.logger.error(status_line)
        elif level == "warning":
            self.logger.warning(status_line)
        else:
            self.logger.info(status_line)
    
    async def generate_asset(self, asset_type: str, prompt: str, index: int, total: int) -> Optional[Dict]:
        """Generate a single asset with progress tracking"""
        model_config = self.config['replicate']['models'][asset_type]
        model_id = model_config['model_id']
        cost = model_config['cost_per_image']
        
        # Check budget
        if self.total_cost + cost > self.config['budget']['sample_generation']['max_cost']:
            self.print_status(
                "BUDGET",
                f"Would exceed sample budget (${self.total_cost + cost:.3f} > ${self.config['budget']['sample_generation']['max_cost']:.2f})",
                "warning"
            )
            return None
        
        self.print_status(
            f"{asset_type.upper()}",
            f"Generating {index}/{total}: {prompt[:50]}..."
        )
        
        try:
            # Rate limiting
            await asyncio.sleep(1 / self.config['replicate']['rate_limit'])
            
            # Generate image
            output = await asyncio.to_thread(
                replicate.run,
                model_id,
                input={"prompt": prompt}
            )
            
            # Update cost and statistics
            self.total_cost += cost
            self.update_statistics(asset_type, count=1, cost=cost)
            
            # Save asset
            filename = f"{asset_type}_{index:03d}.png"
            filepath = Path(self.config['output']['sample_directory']) / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Download and save (simplified for example)
            # In reality, you'd download the image from the URL returned
            
            self.print_status(
                f"{asset_type.upper()}",
                f"✓ Generated {filename} (Cost: ${cost:.3f}, Total: ${self.total_cost:.3f})"
            )
            
            return {
                'type': asset_type,
                'filename': filename,
                'prompt': prompt,
                'prompt_editable': True,  # Flag to indicate this prompt can be edited
                'cost': cost,
                'timestamp': datetime.now().isoformat(),
                'model_id': model_id,  # Store which model was used
                'index': index,  # Store the index for regeneration
            }
            
        except Exception as e:
            self.print_status(
                f"{asset_type.upper()}",
                f"✗ Failed to generate {index}/{total}: {str(e)}",
                "error"
            )
            self.errors.append({
                'type': asset_type,
                'index': index,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return None
    
    async def generate_samples(self):
        """Generate sample assets for review across ALL asset categories"""
        self.logger.info("\n" + "="*80)
        self.logger.info("STAGE 1: COMPREHENSIVE SAMPLE GENERATION")
        self.logger.info("="*80)
        
        # Sync with YAML to get dynamic page list
        pages_by_type = self.sync_with_yaml()
        
        samples = []
        
        # Generate samples from ALL asset categories
        sample_configs = []
        
        # Sample from each category for comprehensive review
        # Icons - sample 5 for variety
        if pages_by_type['icons']:
            icon_samples = pages_by_type['icons'][:5]
            if icon_samples:
                sample_configs.append(('icons', icon_samples))
        
        # Covers - sample 5 for variety
        if pages_by_type['covers']:
            cover_samples = pages_by_type['covers'][:5]
            if cover_samples:
                sample_configs.append(('covers', cover_samples))
        
        # Letter Headers - sample 3
        if pages_by_type['letter_headers']:
            letter_samples = pages_by_type['letter_headers'][:3]
            if letter_samples:
                sample_configs.append(('letter_headers', letter_samples))
        
        # Database Icons - sample 5
        if pages_by_type['database_icons']:
            db_samples = pages_by_type['database_icons'][:5]
            if db_samples:
                sample_configs.append(('database_icons', db_samples))
        
        # Textures - sample 4 from the expanded set
        if pages_by_type['textures']:
            texture_samples = pages_by_type['textures'][:4]
            if texture_samples:
                sample_configs.append(('textures', texture_samples))
        
        asset_configs = sample_configs
        
        # Calculate total samples to generate
        total_samples = sum(len(items) for _, items in asset_configs)
        
        # Progress bar for overall sample generation
        with tqdm(total=total_samples, desc="Generating Samples", unit="asset") as pbar:
            for asset_type, page_items in asset_configs:
                count = len(page_items)
                self.print_status("SAMPLES", f"Starting {asset_type} generation ({count} items)")
                
                tasks = []
                for i, page_data in enumerate(page_items, 1):
                    prompt = page_data['prompt']
                    # Pass page data for metadata
                    task = self.generate_asset_with_metadata(asset_type, prompt, i, count, page_data)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks)
                
                for result in results:
                    if result:
                        samples.append(result)
                        self.generated_assets.append(result)
                    pbar.update(1)
        
        # Save sample manifest with enhanced metadata
        manifest_path = Path(self.config['output']['sample_directory']) / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump({
                'samples': samples,
                'total_cost': self.total_cost,
                'errors': self.errors,
                'timestamp': datetime.now().isoformat(),
                'editable_prompts': True,  # Flag for review server
                'prompt_file': 'prompts.json'  # Reference to prompt storage
            }, f, indent=2)
        
        # Also update prompts.json with generated prompts
        prompts_path = Path('prompts.json')
        if prompts_path.exists():
            with open(prompts_path, 'r') as f:
                prompts_data = json.load(f)
            
            # Update prompts data
            for sample in samples:
                asset_type = sample['type']
                page_title = sample.get('metadata', {}).get('page_title', 'Unknown')
                
                if asset_type in prompts_data['prompts']:
                    prompts_data['prompts'][asset_type][page_title] = {
                        'original': sample['prompt'],
                        'current': sample['prompt'],
                        'generated_at': sample['timestamp'],
                        'filename': sample['filename'],
                        'metadata': sample.get('metadata', {})
                    }
            
            # Update statistics
            prompts_data['statistics']['total_prompts_generated'] = len(samples)
            prompts_data['statistics']['last_updated'] = datetime.now().isoformat()
            
            # Save updated prompts data
            with open(prompts_path, 'w') as f:
                json.dump(prompts_data, f, indent=2)
        
        self.logger.info("\n" + "="*80)
        self.logger.info(f"SAMPLE GENERATION COMPLETE")
        self.logger.info(f"Generated: {len(samples)} samples")
        self.logger.info(f"Errors: {len(self.errors)}")
        self.logger.info(f"Total Cost: ${self.total_cost:.3f}")
        self.logger.info(f"Time Elapsed: {time.time() - self.start_time:.1f}s")
        self.logger.info("="*80)
        
        return samples
    
    async def generate_asset_with_metadata(self, asset_type: str, prompt: str, index: int, total: int, page_data: Dict) -> Optional[Dict]:
        """Generate a single asset with enhanced metadata for editing"""
        # Call the original generate_asset function
        result = await self.generate_asset(asset_type, prompt, index, total)
        
        if result:
            # Add page metadata for context during review
            result['metadata'] = {
                'page_title': page_data.get('title', 'Unknown'),
                'page_description': page_data.get('description', ''),
                'page_slug': page_data.get('slug', ''),
                'page_role': page_data.get('role', ''),
                'original_prompt': prompt,  # Store original for comparison
                'editable': True,
                'regeneration_count': 0,
                'prompt_history': [prompt],  # Track prompt evolution
            }
            
            # Add regeneration info
            result['regeneration'] = {
                'can_regenerate': True,
                'asset_type': asset_type,
                'model_config': self.config['replicate']['models'][asset_type],
                'page_index': index - 1,  # Zero-based for array access
            }
        
        return result
    
    async def run_sample_generation(self):
        """Run sample generation with review gate"""
        try:
            # Generate samples
            samples = await self.generate_samples()
            
            if not samples:
                self.logger.error("No samples generated. Exiting.")
                return False
            
            # Launch review server
            self.logger.info("\n" + "="*80)
            self.logger.info("LAUNCHING REVIEW SERVER")
            self.logger.info("="*80)
            
            from review_server import ReviewServer
            server = ReviewServer(
                port=self.config['review']['port'],
                directory=self.config['output']['sample_directory'],
                auto_open=self.config['review']['auto_open']
            )
            
            self.logger.info(f"Starting review server on port {self.config['review']['port']}...")
            self.logger.info(f"Review URL: http://localhost:{self.config['review']['port']}")
            
            if self.config['review']['auto_open']:
                self.logger.info("Browser will open automatically...")
            
            # Wait for approval
            approval_file = Path(self.config['review']['approval_file'])
            self.logger.info(f"\nWaiting for approval file: {approval_file}")
            self.logger.info("To approve samples, create APPROVED.txt in the current directory")
            
            approved = await server.wait_for_approval(approval_file)
            
            if approved:
                self.logger.info(Fore.GREEN + "\n✅ SAMPLES APPROVED - Proceeding to mass generation" + Style.RESET_ALL)
                return True
            else:
                self.logger.warning(Fore.YELLOW + "\n⚠️ SAMPLES REJECTED - Exiting" + Style.RESET_ALL)
                return False
                
        except Exception as e:
            self.logger.error(f"Sample generation failed: {str(e)}")
            return False
    
    async def regenerate_specific_asset(self, asset_data: Dict) -> Optional[Dict]:
        """Regenerate a specific asset with new prompt"""
        asset_type = asset_data['type']
        prompt = asset_data['prompt']
        filename = asset_data['filename']
        page_title = asset_data.get('page_title', 'Unknown')
        
        self.logger.info(f"Regenerating {filename} with new prompt...")
        
        # Generate with new prompt
        model_config = self.config['replicate']['models'][asset_type]
        model_id = model_config['model_id']
        cost = model_config['cost_per_image']
        
        try:
            # Rate limiting
            await asyncio.sleep(1 / self.config['replicate']['rate_limit'])
            
            # Generate image with new prompt
            output = await asyncio.to_thread(
                replicate.run,
                model_id,
                input={"prompt": prompt}
            )
            
            # Update cost tracking and statistics
            self.total_cost += cost
            self.update_statistics(asset_type, count=1, cost=cost)
            self.generation_stats['regenerated_count'] += 1
            
            # Save regenerated asset
            filepath = Path(self.config['output']['sample_directory']) / filename
            # In reality, you'd download and save the actual image here
            
            self.logger.info(f"✅ Regenerated {filename} successfully")
            
            # Update prompts.json with regeneration stats
            prompts_path = Path('prompts.json')
            if prompts_path.exists():
                with open(prompts_path, 'r') as f:
                    prompts_data = json.load(f)
                
                prompts_data['statistics']['total_regenerations'] += 1
                prompts_data['statistics']['last_updated'] = datetime.now().isoformat()
                
                with open(prompts_path, 'w') as f:
                    json.dump(prompts_data, f, indent=2)
            
            return {
                'filename': filename,
                'type': asset_type,
                'prompt': prompt,
                'cost': cost,
                'regenerated_at': datetime.now().isoformat(),
                'status': 'success'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to regenerate {filename}: {str(e)}")
            return {
                'filename': filename,
                'error': str(e),
                'status': 'failed'
            }
    
    async def process_regeneration_queue(self):
        """Process queued regeneration requests from prompts.json"""
        prompts_path = Path('prompts.json')
        if not prompts_path.exists():
            self.logger.warning("No prompts.json found")
            return
        
        with open(prompts_path, 'r') as f:
            prompts_data = json.load(f)
        
        queue = prompts_data.get('regeneration_queue', [])
        if not queue:
            self.logger.info("No assets queued for regeneration")
            return
        
        self.logger.info(f"Processing {len(queue)} regeneration requests...")
        
        results = []
        for item in queue:
            result = await self.regenerate_specific_asset(item)
            results.append(result)
        
        # Clear the queue after processing
        prompts_data['regeneration_queue'] = []
        with open(prompts_path, 'w') as f:
            json.dump(prompts_data, f, indent=2)
        
        # Summary
        successful = sum(1 for r in results if r.get('status') == 'success')
        failed = sum(1 for r in results if r.get('status') == 'failed')
        
        self.logger.info(f"Regeneration complete: {successful} successful, {failed} failed")
        return results
    
    def print_final_summary(self):
        """Print comprehensive final summary"""
        elapsed = time.time() - self.start_time
        
        print("\n" + "="*80)
        print(Fore.CYAN + "FINAL SUMMARY" + Style.RESET_ALL)
        print("="*80)
        
        print(f"\n📊 STATISTICS:")
        print(f"  • Total Assets Generated: {len(self.generated_assets)}")
        print(f"  • Total Cost: ${self.total_cost:.3f}")
        print(f"  • Total Time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        print(f"  • Average Cost per Asset: ${self.total_cost/max(len(self.generated_assets), 1):.3f}")
        print(f"  • Errors Encountered: {len(self.errors)}")
        
        if self.errors:
            print(f"\n⚠️ ERRORS:")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  • {error['type']} #{error['index']}: {error['error'][:50]}...")
        
        print(f"\n📁 OUTPUT LOCATIONS:")
        print(f"  • Samples: {self.config['output']['sample_directory']}")
        print(f"  • Logs: {self.config['logging']['log_file']}")
        
        print("\n" + "="*80)
    
    def update_statistics(self, asset_type: str, count: int = 1, cost: float = 0.0):
        """Update generation statistics
        
        Args:
            asset_type: Type of asset generated
            count: Number of assets generated
            cost: Cost of generation
        """
        if asset_type == 'icons':
            self.generation_stats['icons_generated'] += count
        elif asset_type == 'covers':
            self.generation_stats['covers_generated'] += count
        elif asset_type == 'textures':
            self.generation_stats['textures_generated'] += count
        
        self.generation_stats['total_cost'] += cost
        self.total_cost += cost
    
    async def commit_assets_to_git(self, mode: str = "sample", dry_run: bool = False):
        """Commit generated assets to Git repository
        
        Args:
            mode: Generation mode (sample/production)
            dry_run: If True, only preview operations
            
        Returns:
            True if successful
        """
        try:
            self.logger.info("Preparing to commit assets to Git...")
            
            # Initialize Git operations
            git_ops = GitOperations(repo_path=Path.cwd().parent)  # Go up to project root
            
            # Update stats with final mode
            self.generation_stats['generation_mode'] = mode
            self.generation_stats['total_cost'] = self.total_cost
            
            # Perform auto-commit
            success = git_ops.auto_commit_assets(
                stats=self.generation_stats,
                mode=mode,
                dry_run=dry_run
            )
            
            if success:
                self.logger.info("✅ Assets successfully committed to Git")
            else:
                self.logger.warning("⚠️ Git commit failed - assets saved locally but not committed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error during Git commit: {str(e)}")
            return False

async def main():
    """Main entry point with CLI arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Estate Planning Asset Generator")
    parser.add_argument('--regenerate', action='store_true', 
                       help='Process regeneration queue from prompts.json')
    parser.add_argument('--skip-review', action='store_true',
                       help='Skip review server and approval process')
    parser.add_argument('--mass-production', action='store_true',
                       help='Run mass production immediately (requires prior approval)')
    parser.add_argument('--edit-prompts', action='store_true',
                       help='Launch prompt editor interface only')
    parser.add_argument('--no-commit', action='store_true',
                       help='Skip automatic Git commit after generation')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview Git operations without executing them')
    
    args = parser.parse_args()
    
    generator = AssetGenerator()
    
    try:
        if args.regenerate:
            # Process regeneration queue
            generator.logger.info("Processing regeneration queue...")
            await generator.process_regeneration_queue()
            
        elif args.edit_prompts:
            # Launch review server for prompt editing only
            generator.logger.info("Launching prompt editor interface...")
            from review_server import ReviewServer
            server = ReviewServer()
            server.start()
            
            print("\n📝 Prompt editor running. Press Enter to stop...")
            input()
            server.stop()
            
        elif args.mass_production:
            # Check for approval file
            if not Path("APPROVED.txt").exists():
                generator.logger.error("Mass production requires approval. Run sample generation first.")
                return
            
            generator.logger.info("Starting mass production...")
            # TODO: Implement mass generation
            generator.logger.info("Mass generation would start here...")
            
            # Commit assets to Git after mass production
            if not args.no_commit:
                await generator.commit_assets_to_git(mode="production", dry_run=args.dry_run)
            
        else:
            # Normal flow: sample generation with approval gate
            approved = await generator.run_sample_generation()
            
            if approved and not args.skip_review:
                # Process any regeneration requests
                await generator.process_regeneration_queue()
                
                # TODO: Implement mass generation after approval
                generator.logger.info("Mass generation would start here...")
                
                # Commit assets to Git after successful generation
                if not args.no_commit:
                    await generator.commit_assets_to_git(mode="production", dry_run=args.dry_run)
            
            elif args.skip_review:
                # If review was skipped, still commit sample assets
                if not args.no_commit:
                    await generator.commit_assets_to_git(mode="sample", dry_run=args.dry_run)
        
    except KeyboardInterrupt:
        generator.logger.warning("\n⚠️ Generation interrupted by user")
    except Exception as e:
        generator.logger.error(f"Fatal error: {str(e)}")
    finally:
        generator.print_final_summary()

if __name__ == "__main__":
    asyncio.run(main())