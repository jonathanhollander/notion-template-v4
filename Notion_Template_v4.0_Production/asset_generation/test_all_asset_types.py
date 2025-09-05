#!/usr/bin/env python3
"""
Test script to generate 3 samples of EVERY asset type
Uses existing generation methods without modifying core code
"""

import asyncio
import sys
from pathlib import Path
from asset_generator import AssetGenerator

async def test_all_asset_types():
    """Generate 3 samples of each asset type discovered from YAML"""
    
    generator = AssetGenerator()
    generator.logger.info("=" * 80)
    generator.logger.info("TESTING ALL ASSET TYPES - 3 SAMPLES EACH")
    generator.logger.info("=" * 80)
    
    # Discover all assets from YAML
    pages_by_type = generator.sync_with_yaml()
    
    # Track totals
    total_generated = 0
    total_cost = 0.0
    
    # Asset types to test (all that were discovered)
    asset_types_to_test = [
        ('icons', 3),
        ('covers', 3),
        ('letter_headers', 3),
        ('textures', 3),
        ('database_icons', 3)
    ]
    
    for asset_type, sample_count in asset_types_to_test:
        if asset_type in pages_by_type and pages_by_type[asset_type]:
            generator.logger.info(f"\n{'='*60}")
            generator.logger.info(f"Testing {asset_type.upper()} - {sample_count} samples")
            generator.logger.info(f"{'='*60}")
            
            # Get sample pages
            sample_pages = pages_by_type[asset_type][:sample_count]
            
            if not sample_pages:
                generator.logger.warning(f"No {asset_type} found to test")
                continue
                
            # Generate each sample
            for idx, page in enumerate(sample_pages, 1):
                try:
                    generator.logger.info(f"[{idx}/{sample_count}] Generating {asset_type} for: {page.get('title', 'Unknown')}")
                    
                    # Get prompt for this page/asset - it's already in the page_data
                    prompt = page.get('prompt', f"Generate a {asset_type} for {page.get('title', 'Unknown')}")
                    
                    # Generate the asset
                    result = await generator.generate_asset(
                        asset_type=asset_type,
                        prompt=prompt,
                        index=idx,
                        total=sample_count
                    )
                    
                    if result:
                        total_generated += 1
                        # Extract cost from result if available
                        if 'cost' in result:
                            total_cost += result['cost']
                        else:
                            # Use default cost from config
                            model_config = generator.config['replicate']['models'].get(asset_type, {})
                            total_cost += model_config.get('cost_per_image', 0.04)
                        
                        generator.logger.info(f"✅ Generated {asset_type} {idx}/{sample_count}")
                    else:
                        generator.logger.warning(f"Failed to generate {asset_type} {idx}")
                        
                except Exception as e:
                    generator.logger.error(f"Error generating {asset_type}: {e}")
                    
                # Rate limiting delay
                await asyncio.sleep(1)
        else:
            generator.logger.info(f"\nNo {asset_type} discovered from YAML - skipping")
    
    # Final summary
    generator.logger.info("\n" + "="*80)
    generator.logger.info("TEST COMPLETE - ALL ASSET TYPES")
    generator.logger.info("="*80)
    generator.logger.info(f"Total assets generated: {total_generated}")
    generator.logger.info(f"Total cost: ${total_cost:.3f}")
    generator.logger.info(f"Check output/samples/ directory for all generated assets")
    generator.logger.info("="*80)

if __name__ == "__main__":
    try:
        asyncio.run(test_all_asset_types())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nTest failed: {e}")
        sys.exit(1)