#!/usr/bin/env python3
"""
Comprehensive test to verify YAML discovery and summarize what will be generated
"""

import sys
import json
from pathlib import Path
from sync_yaml_comprehensive import sync_with_yaml

def main():
    """Test and summarize YAML discovery"""
    print("="*80)
    print("COMPREHENSIVE YAML DISCOVERY TEST")
    print("="*80)
    
    try:
        # Test the comprehensive sync
        print("\n1. Running comprehensive YAML sync...")
        pages_by_type = sync_with_yaml()
        
        # Detailed breakdown
        print("\n2. Detailed Asset Breakdown:")
        print("-" * 60)
        
        # Icons
        if pages_by_type.get('icons'):
            print(f"\n📦 ICONS ({len(pages_by_type['icons'])} total):")
            categories = {}
            for item in pages_by_type['icons']:
                cat = item.get('category', 'general')
                categories[cat] = categories.get(cat, 0) + 1
            for cat, count in sorted(categories.items()):
                print(f"  • {cat:20s}: {count:3d} icons")
        
        # Covers
        if pages_by_type.get('covers'):
            print(f"\n🖼️  COVERS ({len(pages_by_type['covers'])} total):")
            categories = {}
            for item in pages_by_type['covers']:
                cat = item.get('category', 'general')
                categories[cat] = categories.get(cat, 0) + 1
            for cat, count in sorted(categories.items()):
                print(f"  • {cat:20s}: {count:3d} covers")
        
        # Letter Headers
        if pages_by_type.get('letter_headers'):
            print(f"\n✉️  LETTER HEADERS ({len(pages_by_type['letter_headers'])} total):")
            for i, item in enumerate(pages_by_type['letter_headers'][:5], 1):
                print(f"  {i}. {item.get('title', 'Unknown')}")
            if len(pages_by_type['letter_headers']) > 5:
                print(f"  ... and {len(pages_by_type['letter_headers']) - 5} more")
        
        # Database Icons
        if pages_by_type.get('database_icons'):
            print(f"\n🗄️  DATABASE ICONS ({len(pages_by_type['database_icons'])} total):")
            for item in pages_by_type['database_icons']:
                print(f"  • {item.get('title', 'Unknown')}")
        
        # Textures
        if pages_by_type.get('textures'):
            print(f"\n🎨 TEXTURES ({len(pages_by_type['textures'])} total):")
            for item in pages_by_type['textures']:
                print(f"  • {item.get('title', 'Unknown')}")
        
        # Cost Analysis
        print("\n3. Cost Analysis:")
        print("-" * 60)
        total_assets = sum(len(v) for v in pages_by_type.values())
        
        # Calculate costs based on config
        icon_cost = len(pages_by_type.get('icons', [])) * 0.04
        cover_cost = len(pages_by_type.get('covers', [])) * 0.04
        letter_cost = len(pages_by_type.get('letter_headers', [])) * 0.04
        db_icon_cost = len(pages_by_type.get('database_icons', [])) * 0.04
        texture_cost = len(pages_by_type.get('textures', [])) * 0.003
        
        total_cost = icon_cost + cover_cost + letter_cost + db_icon_cost + texture_cost
        
        print(f"  Icons:          {len(pages_by_type.get('icons', [])):3d} × $0.040 = ${icon_cost:6.2f}")
        print(f"  Covers:         {len(pages_by_type.get('covers', [])):3d} × $0.040 = ${cover_cost:6.2f}")
        print(f"  Letter Headers: {len(pages_by_type.get('letter_headers', [])):3d} × $0.040 = ${letter_cost:6.2f}")
        print(f"  Database Icons: {len(pages_by_type.get('database_icons', [])):3d} × $0.040 = ${db_icon_cost:6.2f}")
        print(f"  Textures:       {len(pages_by_type.get('textures', [])):3d} × $0.003 = ${texture_cost:6.2f}")
        print("-" * 60)
        print(f"  TOTAL:          {total_assets:3d} assets     = ${total_cost:6.2f}")
        
        # Budget Check
        print("\n4. Budget Validation:")
        print("-" * 60)
        config_path = Path(__file__).parent / 'config.json'
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
            budget = config.get('budget', {}).get('mass_generation', {}).get('max_cost', 0)
            print(f"  Budget Limit:    ${budget:.2f}")
            print(f"  Estimated Cost:  ${total_cost:.2f}")
            if total_cost <= budget:
                print(f"  ✅ Within budget (${budget - total_cost:.2f} remaining)")
            else:
                print(f"  ❌ Over budget by ${total_cost - budget:.2f}")
        
        # YAML Source Files
        print("\n5. YAML Source Files:")
        print("-" * 60)
        yaml_dir = Path(__file__).parent.parent / 'split_yaml'
        yaml_files = sorted(yaml_dir.glob('*.yaml'))
        print(f"  Found {len(yaml_files)} YAML files in {yaml_dir.name}/")
        
        # Sample prompts
        print("\n6. Sample Prompts (first 3 of each type):")
        print("-" * 60)
        
        if pages_by_type.get('icons'):
            print("\n  ICON PROMPTS:")
            for item in pages_by_type['icons'][:3]:
                print(f"  • {item.get('title', 'Unknown')[:30]:30s}")
                print(f"    → {item.get('prompt', 'No prompt')[:70]}...")
        
        if pages_by_type.get('covers'):
            print("\n  COVER PROMPTS:")
            for item in pages_by_type['covers'][:3]:
                print(f"  • {item.get('title', 'Unknown')[:30]:30s}")
                print(f"    → {item.get('prompt', 'No prompt')[:70]}...")
        
        # Summary
        print("\n" + "="*80)
        print("✅ YAML DISCOVERY COMPLETE")
        print("="*80)
        print(f"\n📊 SUMMARY:")
        print(f"  • Total Assets:  {total_assets}")
        print(f"  • Estimated Cost: ${total_cost:.2f}")
        print(f"  • Budget Status:  {'✅ OK' if total_cost <= 25.00 else '❌ OVER'}")
        print(f"\n💡 NEXT STEPS:")
        print(f"  1. Set REPLICATE_API_KEY environment variable")
        print(f"  2. Run: python3 asset_generator.py --dry-run")
        print(f"  3. For samples: Run standard mode (generates 10 samples)")
        print(f"  4. For all {total_assets} assets: python3 asset_generator.py --mass-production")
        
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