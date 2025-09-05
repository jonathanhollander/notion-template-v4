#!/usr/bin/env python3
"""
Estate Planning Executive Theme Generator
Generates a complete set of 337 high-end visual assets within budget constraints
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import replicate
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ThemeAsset:
    """Represents a single theme asset to generate"""
    asset_type: str  # icon, cover, header, texture
    category: str
    name: str
    prompt: str
    filename: str
    status: str = "pending"
    cost: float = 0.0
    generation_time: float = 0.0
    url: Optional[str] = None
    error: Optional[str] = None

@dataclass
class GenerationBatch:
    """Represents a batch of assets to generate together"""
    batch_id: int
    asset_type: str
    assets: List[ThemeAsset]
    total_cost: float = 0.0
    status: str = "pending"

class BudgetTracker:
    """Tracks generation costs to stay within budget"""
    
    def __init__(self, total_budget: float = 13.11):
        self.total_budget = total_budget
        self.spent = 0.0
        self.reserved = 0.0
        self.cost_per_type = {
            'icon': 0.04,
            'cover': 0.04,
            'header': 0.05,
            'texture': 0.05
        }
        self.generation_log = []
    
    def can_afford(self, asset_type: str, count: int = 1) -> bool:
        """Check if we can afford to generate assets"""
        cost = self.cost_per_type.get(asset_type, 0.05) * count
        return (self.spent + self.reserved + cost) <= self.total_budget
    
    def reserve(self, asset_type: str, count: int = 1) -> float:
        """Reserve budget for upcoming generation"""
        cost = self.cost_per_type.get(asset_type, 0.05) * count
        if self.can_afford(asset_type, count):
            self.reserved += cost
            return cost
        raise ValueError(f"Budget exceeded: Cannot reserve ${cost:.2f}")
    
    def commit(self, asset_type: str, count: int = 1) -> float:
        """Commit reserved budget as spent"""
        cost = self.cost_per_type.get(asset_type, 0.05) * count
        self.reserved -= cost
        self.spent += cost
        self.generation_log.append({
            'timestamp': datetime.now().isoformat(),
            'asset_type': asset_type,
            'count': count,
            'cost': cost,
            'total_spent': self.spent
        })
        return cost
    
    def release(self, amount: float):
        """Release reserved budget if generation fails"""
        self.reserved = max(0, self.reserved - amount)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        return {
            'total_budget': self.total_budget,
            'spent': round(self.spent, 2),
            'reserved': round(self.reserved, 2),
            'available': round(self.total_budget - self.spent - self.reserved, 2),
            'percentage_used': round((self.spent / self.total_budget) * 100, 1)
        }

class EstateExecutiveThemeGenerator:
    """Generates the complete Estate Planning Executive theme asset set"""
    
    def __init__(self, config_path: str = None):
        """Initialize the theme generator
        
        Args:
            config_path: Path to theme configuration JSON
        """
        # Load configuration
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        else:
            # Use default path
            default_path = Path(__file__).parent / "themes/estate_planning_executive/theme_config.json"
            if default_path.exists():
                with open(default_path, 'r') as f:
                    self.config = json.load(f)
            else:
                raise FileNotFoundError(f"Theme configuration not found at {config_path or default_path}")
        
        # Initialize components
        self.budget_tracker = BudgetTracker(self.config['generation_settings']['budget']['total_limit'])
        self.assets_to_generate: List[ThemeAsset] = []
        self.generated_assets: List[ThemeAsset] = []
        self.failed_assets: List[ThemeAsset] = []
        
        # Setup output directory
        self.base_path = Path(self.config['directory_structure']['base_path'].lstrip('/'))
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in self.config['directory_structure']['subdirectories'].values():
            (self.base_path / subdir).mkdir(parents=True, exist_ok=True)
        
        # Initialize Replicate client if available
        self.replicate_client = None
        api_token = os.environ.get('REPLICATE_API_TOKEN')
        if api_token:
            self.replicate_client = replicate.Client(api_token=api_token)
            logger.info("✅ Replicate client initialized")
        else:
            logger.warning("⚠️ REPLICATE_API_TOKEN not found - running in planning mode only")
    
    def prepare_asset_list(self) -> List[ThemeAsset]:
        """Prepare the complete list of assets to generate"""
        assets = []
        
        # Prepare icons (162 total)
        icon_spec = self.config['asset_specifications']['icons']
        icons_per_category = 162 // len(icon_spec['categories'])
        
        for category in icon_spec['categories']:
            for i in range(icons_per_category):
                name = f"{category}_{i+1:03d}"
                prompt = icon_spec['base_prompt'].replace(
                    '{subject}', 
                    f"{category.replace('_', ' ')} concept #{i+1}"
                )
                filename = f"icon_{category}_{i+1:03d}.png"
                
                assets.append(ThemeAsset(
                    asset_type='icon',
                    category=category,
                    name=name,
                    prompt=prompt,
                    filename=filename
                ))
        
        # Add extra icons to reach exactly 162
        remaining_icons = 162 - len([a for a in assets if a.asset_type == 'icon'])
        for i in range(remaining_icons):
            category = icon_spec['categories'][i % len(icon_spec['categories'])]
            name = f"{category}_extra_{i+1:02d}"
            prompt = icon_spec['base_prompt'].replace(
                '{subject}',
                f"premium {category.replace('_', ' ')} element"
            )
            filename = f"icon_{category}_extra_{i+1:02d}.png"
            
            assets.append(ThemeAsset(
                asset_type='icon',
                category=category,
                name=name,
                prompt=prompt,
                filename=filename
            ))
        
        # Prepare covers (162 total)
        cover_spec = self.config['asset_specifications']['covers']
        covers_per_category = 162 // len(cover_spec['categories'])
        
        for category in cover_spec['categories']:
            for i in range(covers_per_category):
                name = f"{category}_{i+1:03d}"
                prompt = cover_spec['base_prompt'].replace(
                    '{subject}',
                    f"{category.replace('_', ' ')} design #{i+1}"
                )
                filename = f"cover_{category}_{i+1:03d}.jpg"
                
                assets.append(ThemeAsset(
                    asset_type='cover',
                    category=category,
                    name=name,
                    prompt=prompt,
                    filename=filename
                ))
        
        # Add extra covers to reach exactly 162
        remaining_covers = 162 - len([a for a in assets if a.asset_type == 'cover'])
        for i in range(remaining_covers):
            category = cover_spec['categories'][i % len(cover_spec['categories'])]
            name = f"{category}_extra_{i+1:02d}"
            prompt = cover_spec['base_prompt'].replace(
                '{subject}',
                f"elegant {category.replace('_', ' ')} theme"
            )
            filename = f"cover_{category}_extra_{i+1:02d}.jpg"
            
            assets.append(ThemeAsset(
                asset_type='cover',
                category=category,
                name=name,
                prompt=prompt,
                filename=filename
            ))
        
        # Prepare letter headers (3 total)
        header_spec = self.config['asset_specifications']['letter_headers']
        for i, header_type in enumerate(header_spec['types']):
            name = f"{header_type}"
            prompt = f"{header_spec['base_prompt']}, {header_type.replace('_', ' ')} style"
            filename = f"header_{header_type}_{i+1}.png"
            
            assets.append(ThemeAsset(
                asset_type='header',
                category='headers',
                name=name,
                prompt=prompt,
                filename=filename
            ))
        
        # Prepare textures (10 total)
        texture_spec = self.config['asset_specifications']['textures']
        for i, material in enumerate(texture_spec['materials']):
            name = f"{material}"
            prompt = texture_spec['base_prompt'].replace('{material}', material.replace('_', ' '))
            filename = f"texture_{material}_{i+1:02d}.jpg"
            
            assets.append(ThemeAsset(
                asset_type='texture',
                category='textures',
                name=name,
                prompt=prompt,
                filename=filename
            ))
        
        self.assets_to_generate = assets
        logger.info(f"📋 Prepared {len(assets)} assets for generation:")
        logger.info(f"   • Icons: {len([a for a in assets if a.asset_type == 'icon'])}")
        logger.info(f"   • Covers: {len([a for a in assets if a.asset_type == 'cover'])}")
        logger.info(f"   • Headers: {len([a for a in assets if a.asset_type == 'header'])}")
        logger.info(f"   • Textures: {len([a for a in assets if a.asset_type == 'texture'])}")
        
        return assets
    
    def create_batches(self) -> List[GenerationBatch]:
        """Create generation batches based on configuration"""
        batches = []
        batch_settings = self.config['generation_settings']['batch_settings']
        
        # Group assets by type
        assets_by_type = {
            'icon': [a for a in self.assets_to_generate if a.asset_type == 'icon'],
            'cover': [a for a in self.assets_to_generate if a.asset_type == 'cover'],
            'header': [a for a in self.assets_to_generate if a.asset_type == 'header'],
            'texture': [a for a in self.assets_to_generate if a.asset_type == 'texture']
        }
        
        batch_id = 0
        
        # Create batches for each type
        for asset_type, assets in assets_by_type.items():
            if asset_type == 'icon':
                batch_size = batch_settings['icons_per_batch']
            elif asset_type == 'cover':
                batch_size = batch_settings['covers_per_batch']
            elif asset_type == 'header':
                batch_size = batch_settings['headers_per_batch']
            else:  # texture
                batch_size = batch_settings['textures_per_batch']
            
            # Split into batches
            for i in range(0, len(assets), batch_size):
                batch_assets = assets[i:i + batch_size]
                batch_cost = self.budget_tracker.cost_per_type[asset_type] * len(batch_assets)
                
                batches.append(GenerationBatch(
                    batch_id=batch_id,
                    asset_type=asset_type,
                    assets=batch_assets,
                    total_cost=batch_cost
                ))
                batch_id += 1
        
        logger.info(f"📦 Created {len(batches)} generation batches")
        return batches
    
    async def generate_asset(self, asset: ThemeAsset) -> bool:
        """Generate a single asset
        
        Args:
            asset: ThemeAsset to generate
            
        Returns:
            True if successful, False otherwise
        """
        if not self.replicate_client:
            logger.warning(f"Skipping {asset.filename} - no Replicate client")
            asset.status = "skipped"
            return False
        
        try:
            # Reserve budget
            cost = self.budget_tracker.reserve(asset.asset_type)
            
            # Generate image
            logger.debug(f"Generating {asset.filename}...")
            output = await self.replicate_client.predictions.create(
                model="black-forest-labs/flux-schnell",
                input={
                    "prompt": asset.prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "1:1" if asset.asset_type == 'icon' else "16:9",
                    "output_format": "png" if asset.asset_type in ['icon', 'header'] else "jpg",
                    "output_quality": 95
                }
            )
            
            # Wait for completion
            while output.status not in ['succeeded', 'failed', 'canceled']:
                await asyncio.sleep(1)
                output = await self.replicate_client.predictions.get(output.id)
            
            if output.status == 'succeeded' and output.output:
                asset.url = output.output[0] if isinstance(output.output, list) else output.output
                asset.status = "generated"
                asset.cost = cost
                
                # Commit budget
                self.budget_tracker.commit(asset.asset_type)
                self.generated_assets.append(asset)
                
                logger.info(f"✅ Generated {asset.filename}")
                return True
            else:
                raise Exception(f"Generation failed: {output.status}")
                
        except Exception as e:
            logger.error(f"❌ Failed to generate {asset.filename}: {e}")
            asset.status = "failed"
            asset.error = str(e)
            
            # Release budget
            self.budget_tracker.release(self.budget_tracker.cost_per_type[asset.asset_type])
            self.failed_assets.append(asset)
            return False
    
    async def process_batch(self, batch: GenerationBatch) -> Dict[str, Any]:
        """Process a single generation batch
        
        Args:
            batch: GenerationBatch to process
            
        Returns:
            Batch results
        """
        logger.info(f"🎨 Processing batch {batch.batch_id} ({batch.asset_type}): {len(batch.assets)} assets")
        
        # Check budget
        if not self.budget_tracker.can_afford(batch.asset_type, len(batch.assets)):
            logger.error(f"❌ Insufficient budget for batch {batch.batch_id}")
            batch.status = "budget_exceeded"
            return {
                'batch_id': batch.batch_id,
                'status': 'budget_exceeded',
                'generated': 0,
                'failed': len(batch.assets)
            }
        
        # Generate assets in batch
        tasks = [self.generate_asset(asset) for asset in batch.assets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count results
        successful = sum(1 for r in results if r is True)
        failed = len(results) - successful
        
        batch.status = "completed"
        batch.total_cost = sum(a.cost for a in batch.assets if a.status == "generated")
        
        return {
            'batch_id': batch.batch_id,
            'status': 'completed',
            'generated': successful,
            'failed': failed,
            'cost': batch.total_cost
        }
    
    async def generate_theme(self, test_mode: bool = False) -> Dict[str, Any]:
        """Generate the complete theme asset set
        
        Args:
            test_mode: If True, only generate a small test batch
            
        Returns:
            Generation results
        """
        start_time = datetime.now()
        
        # Prepare assets
        self.prepare_asset_list()
        
        if test_mode:
            # In test mode, only generate 5 of each type
            test_assets = []
            for asset_type in ['icon', 'cover', 'header', 'texture']:
                type_assets = [a for a in self.assets_to_generate if a.asset_type == asset_type]
                test_assets.extend(type_assets[:5 if asset_type != 'header' else 1])
            self.assets_to_generate = test_assets
            logger.info(f"🧪 TEST MODE: Generating {len(test_assets)} sample assets")
        
        # Create batches
        batches = self.create_batches()
        
        # Process batches
        logger.info("="*80)
        logger.info("🚀 STARTING ESTATE PLANNING EXECUTIVE THEME GENERATION")
        logger.info(f"📊 Total assets: {len(self.assets_to_generate)}")
        logger.info(f"💰 Budget: ${self.budget_tracker.total_budget}")
        logger.info("="*80)
        
        batch_results = []
        for batch in tqdm(batches, desc="Processing batches"):
            # Check budget before processing
            budget_status = self.budget_tracker.get_status()
            logger.info(f"💰 Budget status: ${budget_status['spent']:.2f} spent, ${budget_status['available']:.2f} available")
            
            if budget_status['available'] < 0.01:
                logger.warning("⚠️ Budget nearly exhausted, stopping generation")
                break
            
            # Process batch
            result = await self.process_batch(batch)
            batch_results.append(result)
            
            # Delay between batches
            if batch != batches[-1]:  # Not the last batch
                delay = self.config['generation_settings']['batch_settings']['delay_between_batches']
                await asyncio.sleep(delay)
        
        # Calculate final statistics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        final_stats = {
            'theme': self.config['theme']['name'],
            'generation_time': duration,
            'total_assets_planned': len(self.assets_to_generate),
            'total_generated': len(self.generated_assets),
            'total_failed': len(self.failed_assets),
            'budget': self.budget_tracker.get_status(),
            'batches_processed': len(batch_results),
            'success_rate': (len(self.generated_assets) / len(self.assets_to_generate) * 100) if self.assets_to_generate else 0
        }
        
        # Save generation report
        report_path = self.base_path / "generation_report.json"
        with open(report_path, 'w') as f:
            json.dump({
                'metadata': final_stats,
                'generated_assets': [
                    {
                        'filename': a.filename,
                        'type': a.asset_type,
                        'category': a.category,
                        'url': a.url,
                        'cost': a.cost
                    }
                    for a in self.generated_assets
                ],
                'failed_assets': [
                    {
                        'filename': a.filename,
                        'type': a.asset_type,
                        'error': a.error
                    }
                    for a in self.failed_assets
                ]
            }, indent=2)
        
        # Print summary
        logger.info("="*80)
        logger.info("✨ THEME GENERATION COMPLETE")
        logger.info(f"⏱️  Duration: {duration:.1f} seconds")
        logger.info(f"📊 Generated: {final_stats['total_generated']}/{final_stats['total_assets_planned']} assets")
        logger.info(f"💰 Total cost: ${final_stats['budget']['spent']:.2f}")
        logger.info(f"📈 Success rate: {final_stats['success_rate']:.1f}%")
        logger.info(f"📁 Report saved to: {report_path}")
        logger.info("="*80)
        
        return final_stats

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Estate Planning Executive Theme Generator")
    parser.add_argument('--config', type=str, help='Path to theme configuration JSON')
    parser.add_argument('--test', action='store_true', help='Test mode: Generate sample assets only')
    parser.add_argument('--budget', type=float, default=13.11, help='Maximum budget in USD')
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = EstateExecutiveThemeGenerator(config_path=args.config)
    
    if args.budget != 13.11:
        generator.budget_tracker.total_budget = args.budget
        logger.info(f"💰 Budget override: ${args.budget:.2f}")
    
    # Generate theme
    results = await generator.generate_theme(test_mode=args.test)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())