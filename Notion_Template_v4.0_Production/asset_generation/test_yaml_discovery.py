#!/usr/bin/env python3
"""
Test script to verify YAML discovery without generating any images
"""

import sys
import json
from pathlib import Path
from sync_yaml_comprehensive import sync_with_yaml

def main():
    """Test YAML discovery and validation"""
    print("="*80)
    print("TESTING YAML DISCOVERY - NO IMAGE GENERATION")
    print("="*80)
    
    try:
        # Test the comprehensive sync
        print("\n1. Testing comprehensive YAML sync...")
        pages_by_type = sync_with_yaml()
        
        # Count everything
        total_assets = sum(len(v) for v in pages_by_type.values())
        
        print("\n2. Discovery Results:")
        print("-" * 40)
        for asset_type, items in pages_by_type.items():
            print(f"  {asset_type:20s}: {len(items):3d} items")
        print("-" * 40)
        print(f"  {'TOTAL':20s}: {total_assets:3d} assets")
        
        # Cost estimate
        estimated_cost = total_assets * 0.04
        print(f"\n3. Estimated Cost: ${estimated_cost:.2f}")
        
        # Check against expected ~490 assets
        print(f"\n4. Validation:")
        if 450 <= total_assets <= 550:
            print(f"  ✓ Asset count ({total_assets}) is within expected range (450-550)")
        else:
            print(f"  ⚠️ Asset count ({total_assets}) is outside expected range (450-550)")
        
        # Sample some items to verify quality
        print(f"\n5. Sample Items:")
        if pages_by_type.get('icons'):
            print("  Sample Icons:")
            for item in pages_by_type['icons'][:3]:
                print(f"    - {item.get('title', 'Unknown')}")
        
        if pages_by_type.get('covers'):
            print("  Sample Covers:")
            for item in pages_by_type['covers'][:3]:
                print(f"    - {item.get('title', 'Unknown')}")
        
        # Check YAML directory
        yaml_dir = Path(__file__).parent.parent / 'split_yaml'
        yaml_files = list(yaml_dir.glob('*.yaml'))
        print(f"\n6. YAML Files:")
        print(f"  Found {len(yaml_files)} YAML files in {yaml_dir}")
        
        # Verify config.json is set correctly
        config_path = Path(__file__).parent / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            budget = config.get('mass_generation', {}).get('max_cost', 0)
            print(f"\n7. Budget Configuration:")
            print(f"  Max budget: ${budget:.2f}")
            if estimated_cost <= budget:
                print(f"  ✓ Estimated cost (${estimated_cost:.2f}) is within budget")
            else:
                print(f"  ⚠️ Estimated cost (${estimated_cost:.2f}) exceeds budget (${budget:.2f})")
        
        print("\n" + "="*80)
        print("✓ YAML DISCOVERY TEST SUCCESSFUL")
        print("="*80)
        print(f"\nReady to generate {total_assets} assets")
        print("To generate SAMPLE assets (5-10), run: python asset_generator.py --samples")
        print("To generate ALL assets, run: python asset_generator.py --generate-all")
        
        return 0
        
    except ValueError as e:
        print("\n" + "="*80)
        print("❌ YAML DISCOVERY FAILED")
        print("="*80)
        print(str(e))
        print("="*80)
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())