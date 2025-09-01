#!/usr/bin/env python3
"""
Test script to verify comprehensive YAML sync without needing API keys
"""

import sys
import json
import yaml
from pathlib import Path
from typing import Dict, List

def sync_with_yaml() -> Dict[str, List[Dict]]:
    """Comprehensively read ALL pages from ALL YAML configuration files"""
    print("Syncing with ALL YAML configuration files for comprehensive asset generation...")
    
    pages_by_type = {
        'icons': [],
        'covers': [],
        'textures': [],
        'letter_headers': [],  # New category for letter templates
        'database_icons': []   # New category for database categories
    }
    
    # Path to split_yaml directory (relative to project root)
    yaml_dir = Path(__file__).parent.parent / 'split_yaml'
    
    if not yaml_dir.exists():
        print(f"YAML directory not found: {yaml_dir}")
        return pages_by_type
    
    # Read all YAML files
    yaml_files = sorted(yaml_dir.glob('*.yaml'))
    total_pages = 0
    stats = {
        'core_pages': 0,
        'extended_pages': 0,
        'letters': 0,
        'databases': 0,
        'admin_pages': 0,
        'missing_assets': 0
    }
    
    for yaml_file in yaml_files:
        print(f"Reading {yaml_file.name}...")
        try:
            with open(yaml_file, 'r') as f:
                content = f.read()
            
            # Handle malformed YAML structure with complexity mixed in pages
            lines = content.split('\n')
            fixed_lines = []
            in_pages = False
            
            for line in lines:
                if line.strip() == 'pages:':
                    in_pages = True
                    fixed_lines.append(line)
                elif in_pages and line.strip().startswith('complexity:'):
                    continue  # Skip complexity lines mixed in pages
                else:
                    fixed_lines.append(line)
            
            # Parse fixed YAML
            fixed_content = '\n'.join(fixed_lines)
            data = yaml.safe_load(fixed_content)
            
            # Process different YAML structures
            
            # 1. Regular pages (from 01_pages_core.yaml, etc.)
            if 'pages' in data and isinstance(data['pages'], list):
                for page in data['pages']:
                    if not isinstance(page, dict):
                        continue
                    
                    title = page.get('title', 'Untitled')
                    description = page.get('description', '')
                    slug = page.get('slug', title.lower().replace(' ', '-'))
                    role = page.get('role', 'owner')
                    
                    # Track if assets are missing
                    has_icon = bool(page.get('icon_file'))
                    has_cover = bool(page.get('cover_file'))
                    
                    # Always add page even if it currently lacks asset fields
                    # (we'll generate them anyway for comprehensive coverage)
                    if not has_icon:
                        stats['missing_assets'] += 1
                        pages_by_type['icons'].append({
                            'title': title,
                            'slug': slug,
                            'role': role,
                            'prompt': f"Technical drawing icon for '{title}': {description[:100]}, mechanical poetry style, readable at 24px"
                        })
                    elif has_icon:  # Still add if it has icon_file for regeneration
                        pages_by_type['icons'].append({
                            'title': title,
                            'slug': slug,
                            'role': role,
                            'prompt': f"Technical drawing icon for '{title}': {description[:100]}, mechanical poetry style, readable at 24px"
                        })
                    
                    if not has_cover:
                        stats['missing_assets'] += 1
                        pages_by_type['covers'].append({
                            'title': title,
                            'slug': slug,
                            'role': role,
                            'prompt': f"Blueprint cover for '{title}': {description[:100]}, architectural drawing style, golden ratio grid"
                        })
                    elif has_cover:  # Still add if it has cover_file for regeneration
                        pages_by_type['covers'].append({
                            'title': title,
                            'slug': slug,
                            'role': role,
                            'prompt': f"Blueprint cover for '{title}': {description[:100]}, architectural drawing style, golden ratio grid"
                        })
                    
                    stats['core_pages'] += 1
                    total_pages += 1
            
            # 2. Extended pages (from 02_pages_extended.yaml)
            if 'extended_pages' in data and isinstance(data['extended_pages'], list):
                for page in data['extended_pages']:
                    if not isinstance(page, dict):
                        continue
                    
                    title = page.get('title', 'Untitled')
                    description = page.get('description', '')
                    category = page.get('category', 'general')
                    
                    # Extended pages typically don't have assets defined
                    pages_by_type['icons'].append({
                        'title': title,
                        'slug': title.lower().replace(' ', '-'),
                        'category': category,
                        'prompt': f"Professional icon for '{title}': {description[:100]}, minimalist style, clear at small sizes"
                    })
                    
                    pages_by_type['covers'].append({
                        'title': title,
                        'slug': title.lower().replace(' ', '-'),
                        'category': category,
                        'prompt': f"Professional header for '{title}': {description[:100]}, clean modern design, estate planning theme"
                    })
                    
                    stats['extended_pages'] += 1
                    stats['missing_assets'] += 2  # Both icon and cover missing
                    total_pages += 1
            
            # 3. Admin section (from YAML files with admin: key)
            if 'admin' in data and isinstance(data['admin'], dict):
                admin_pages = data['admin'].get('pages', [])
                for page in admin_pages:
                    if not isinstance(page, dict):
                        continue
                    
                    title = page.get('title', 'Untitled')
                    description = page.get('description', '')
                    
                    pages_by_type['icons'].append({
                        'title': f"Admin: {title}",
                        'slug': f"admin-{title.lower().replace(' ', '-')}",
                        'category': 'admin',
                        'prompt': f"Administrative icon for '{title}': {description[:100]}, professional dashboard style"
                    })
                    
                    stats['admin_pages'] += 1
                    stats['missing_assets'] += 1
                    total_pages += 1
            
            # 4. Letters (from 03_letters.yaml)
            if 'letters' in data and isinstance(data['letters'], list):
                for letter in data['letters']:
                    if not isinstance(letter, dict):
                        continue
                    
                    title = letter.get('title', 'Untitled Letter')
                    purpose = letter.get('purpose', '')
                    
                    # Letters need special header graphics
                    pages_by_type['letter_headers'].append({
                        'title': title,
                        'slug': title.lower().replace(' ', '-'),
                        'prompt': f"Professional letterhead design for '{title}': {purpose[:100]}, formal business style, subtle estate planning motif"
                    })
                    
                    stats['letters'] += 1
                    total_pages += 1
            
            # 5. Databases (from 04_databases.yaml)
            if 'db' in data and isinstance(data['db'], list):
                for database in data['db']:
                    if not isinstance(database, dict):
                        continue
                    
                    db_name = database.get('name', 'Untitled DB')
                    categories = database.get('categories', [])
                    
                    # Each database category needs an icon
                    for category in categories:
                        if isinstance(category, dict):
                            cat_name = category.get('name', 'Category')
                            cat_desc = category.get('description', '')
                            
                            pages_by_type['database_icons'].append({
                                'title': cat_name,
                                'database': db_name,
                                'slug': f"{db_name.lower()}-{cat_name.lower()}".replace(' ', '-'),
                                'prompt': f"Database category icon for '{cat_name}' in {db_name}: {cat_desc[:80]}, clean data visualization style"
                            })
                    
                    stats['databases'] += len(categories)
                    
        except Exception as e:
            print(f"Error reading {yaml_file.name}: {str(e)}")
    
    # Add comprehensive texture patterns (expanded from 4 to 10)
    pages_by_type['textures'] = [
        {'title': 'topographical', 'slug': 'texture-topo', 'prompt': 'Subtle topographical map pattern, seamless tile, 5% opacity'},
        {'title': 'blueprint-grid', 'slug': 'texture-grid', 'prompt': 'Blueprint grid with golden ratio proportions, slight distortion'},
        {'title': 'mechanical', 'slug': 'texture-mech', 'prompt': 'Mechanical drawing texture, gears and mechanisms, 10% opacity'},
        {'title': 'parchment', 'slug': 'texture-parchment', 'prompt': 'Aged parchment texture with subtle fibers, warm tone'},
        {'title': 'legal-watermark', 'slug': 'texture-legal', 'prompt': 'Legal document watermark pattern, official seal elements, very subtle'},
        {'title': 'family-tree', 'slug': 'texture-family', 'prompt': 'Delicate family tree branches pattern, organic connections, 8% opacity'},
        {'title': 'compass-rose', 'slug': 'texture-compass', 'prompt': 'Navigation compass rose pattern, directional guidance theme, elegant'},
        {'title': 'ledger-lines', 'slug': 'texture-ledger', 'prompt': 'Financial ledger lines pattern, accounting grid, professional'},
        {'title': 'estate-crest', 'slug': 'texture-crest', 'prompt': 'Subtle heraldic crest elements, family legacy theme, dignified'},
        {'title': 'time-spiral', 'slug': 'texture-time', 'prompt': 'Temporal spiral pattern, legacy through time concept, philosophical'}
    ]
    
    # Comprehensive logging
    print("="*80)
    print("COMPREHENSIVE YAML SYNC COMPLETE")
    print("="*80)
    print(f"✓ Processed {len(yaml_files)} YAML files")
    print(f"✓ Found {total_pages} total pages/items")
    print("")
    print("Page Statistics:")
    print(f"  - Core Pages: {stats['core_pages']}")
    print(f"  - Extended Pages: {stats['extended_pages']}")
    print(f"  - Letter Templates: {stats['letters']}")
    print(f"  - Database Categories: {stats['databases']}")
    print(f"  - Admin Pages: {stats['admin_pages']}")
    print(f"  - Assets Missing: {stats['missing_assets']}")
    print("")
    print("Assets to Generate:")
    print(f"  - Icons: {len(pages_by_type['icons'])}")
    print(f"  - Covers: {len(pages_by_type['covers'])}")
    print(f"  - Letter Headers: {len(pages_by_type['letter_headers'])}")
    print(f"  - Database Icons: {len(pages_by_type['database_icons'])}")
    print(f"  - Textures: {len(pages_by_type['textures'])}")
    print(f"  - TOTAL ASSETS: {sum(len(v) for v in pages_by_type.values())}")
    print("="*80)
    
    # Calculate cost estimate
    icon_cost = len(pages_by_type['icons']) * 0.04
    cover_cost = len(pages_by_type['covers']) * 0.04
    letter_cost = len(pages_by_type['letter_headers']) * 0.04
    db_cost = len(pages_by_type['database_icons']) * 0.04
    texture_cost = len(pages_by_type['textures']) * 0.003
    total_cost = icon_cost + cover_cost + letter_cost + db_cost + texture_cost
    
    print("")
    print("Cost Estimate:")
    print(f"  - Icons: ${icon_cost:.2f}")
    print(f"  - Covers: ${cover_cost:.2f}")
    print(f"  - Letter Headers: ${letter_cost:.2f}")
    print(f"  - Database Icons: ${db_cost:.2f}")
    print(f"  - Textures: ${texture_cost:.2f}")
    print(f"  - TOTAL COST: ${total_cost:.2f}")
    print("="*80)
    
    return pages_by_type

if __name__ == "__main__":
    result = sync_with_yaml()
    
    # Save to JSON for inspection
    output = {
        'assets': {k: len(v) for k, v in result.items()},
        'total': sum(len(v) for v in result.values()),
        'sample_icons': result['icons'][:3] if result['icons'] else [],
        'sample_covers': result['covers'][:3] if result['covers'] else [],
        'sample_letters': result['letter_headers'][:3] if result['letter_headers'] else [],
        'sample_database': result['database_icons'][:3] if result['database_icons'] else []
    }
    
    with open('test_yaml_sync_output.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\nTest output saved to test_yaml_sync_output.json")