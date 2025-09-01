#!/usr/bin/env python3
"""
Test script to verify dynamic discovery of ALL assets from YAML files.
This script ONLY tests parsing - no API calls are made.
"""

import os
import yaml
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

class YAMLAssetDiscovery:
    def __init__(self, yaml_dir: str = "split_yaml"):
        self.yaml_dir = Path(yaml_dir)
        self.pages = defaultdict(list)
        self.errors = []
        
    def discover_all_assets(self) -> Dict[str, Set[str]]:
        """Discover all unique pages from all YAML files."""
        assets = {
            'core_pages': set(),
            'letters': set(),
            'acceptance_pages': set(),
            'database_pages': set(),
            'admin_pages': set(),
            'all_unique': set()
        }
        
        yaml_files = sorted(self.yaml_dir.glob("*.yaml"))
        print(f"\n🔍 Scanning {len(yaml_files)} YAML files...\n")
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Try to parse as YAML
                try:
                    data = yaml.safe_load(content)
                    if data:
                        self._extract_pages_from_data(data, yaml_file.name, assets)
                except yaml.YAMLError:
                    # If YAML parsing fails, try line-by-line extraction
                    self._extract_pages_from_lines(content, yaml_file.name, assets)
                    
            except Exception as e:
                self.errors.append(f"{yaml_file.name}: {str(e)}")
                
        # Combine all unique pages
        for category in ['core_pages', 'letters', 'acceptance_pages', 'database_pages', 'admin_pages']:
            assets['all_unique'].update(assets[category])
            
        return assets
    
    def _extract_pages_from_data(self, data: dict, filename: str, assets: dict):
        """Extract pages from parsed YAML data."""
        if not isinstance(data, dict):
            return
            
        # Core pages structure
        if 'pages' in data and isinstance(data['pages'], list):
            for page in data['pages']:
                if isinstance(page, dict) and 'title' in page:
                    assets['core_pages'].add(page['title'])
                    
        # Letters structure
        if 'letters' in data and isinstance(data['letters'], list):
            for letter in data['letters']:
                if isinstance(letter, dict):
                    if 'Title' in letter:  # Capital T
                        assets['letters'].add(letter['Title'])
                    elif 'title' in letter:  # lowercase t
                        assets['letters'].add(letter['title'])
                        
        # Acceptance rows structure  
        if 'acceptance' in data and isinstance(data['acceptance'], dict):
            if 'rows' in data['acceptance'] and isinstance(data['acceptance']['rows'], list):
                for row in data['acceptance']['rows']:
                    if isinstance(row, dict) and 'Page' in row:
                        assets['acceptance_pages'].add(row['Page'])
                        
        # Admin page structure
        if 'admin_page' in data and isinstance(data['admin_page'], dict):
            if 'title' in data['admin_page']:
                assets['admin_pages'].add(data['admin_page']['title'])
                
        # Database analytics pages
        if 'databases' in data and isinstance(data['databases'], list):
            for db in data['databases']:
                if isinstance(db, dict) and 'title' in db:
                    assets['database_pages'].add(db['title'])
                    
    def _extract_pages_from_lines(self, content: str, filename: str, assets: dict):
        """Extract pages by parsing lines when YAML parsing fails."""
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Core pages: "- title: Page Name"
            if line.strip().startswith('- title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                if title:
                    assets['core_pages'].add(title)
                    
            # Letters: "- Title: Letter Name"
            elif line.strip().startswith('- Title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                if title:
                    assets['letters'].add(title)
                    
            # Acceptance: "Page: Page Name"
            elif 'Page:' in line and not line.strip().startswith('#'):
                parts = line.split('Page:', 1)
                if len(parts) > 1:
                    title = parts[1].strip().strip('"').strip("'")
                    if title and title != 'Page':  # Avoid false positives
                        assets['acceptance_pages'].add(title)
                        
            # Database pages with indentation: "  title: DB Page"
            elif line.startswith('  title:') or line.startswith('    title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                if title and title != '{}':  # Avoid empty placeholders
                    assets['database_pages'].add(title)
                    
    def print_report(self, assets: Dict[str, Set[str]]):
        """Print a detailed report of discovered assets."""
        print("=" * 80)
        print("📊 ASSET DISCOVERY REPORT - v4.0 NOTION TEMPLATE")
        print("=" * 80)
        
        # Category breakdown
        print("\n📁 PAGES BY CATEGORY:")
        print(f"  • Core Pages:        {len(assets['core_pages']):3d} pages")
        print(f"  • Letters:           {len(assets['letters']):3d} pages")
        print(f"  • Acceptance Pages:  {len(assets['acceptance_pages']):3d} pages")
        print(f"  • Database Pages:    {len(assets['database_pages']):3d} pages")
        print(f"  • Admin Pages:       {len(assets['admin_pages']):3d} pages")
        print(f"  {'─' * 30}")
        print(f"  TOTAL UNIQUE PAGES:  {len(assets['all_unique']):3d} pages")
        
        # Asset calculation
        total_pages = len(assets['all_unique'])
        print("\n🎨 ASSET REQUIREMENTS:")
        print(f"  • Icons needed:      {total_pages:3d} × $0.04 = ${total_pages * 0.04:.2f}")
        print(f"  • Covers needed:     {total_pages:3d} × $0.04 = ${total_pages * 0.04:.2f}")
        print(f"  • Letter headers:     18 × $0.04 = $0.72")
        print(f"  • Database icons:     10 × $0.04 = $0.40")
        print(f"  • Textures:          10 × $0.003 = $0.03")
        print(f"  {'─' * 30}")
        total_assets = (total_pages * 2) + 18 + 10 + 10
        total_cost = (total_pages * 2 * 0.04) + (18 * 0.04) + (10 * 0.04) + (10 * 0.003)
        print(f"  TOTAL ASSETS:       {total_assets:3d} assets")
        print(f"  ESTIMATED COST:     ${total_cost:.2f}")
        
        # Budget check
        print("\n💰 BUDGET STATUS:")
        if total_cost <= 25.00:
            print(f"  ✅ Within budget ($25.00 limit)")
        else:
            print(f"  ⚠️  Exceeds budget by ${total_cost - 25.00:.2f}")
            
        # Sample of discovered pages
        print("\n📝 SAMPLE PAGES DISCOVERED:")
        for category, key, pages in [
            ("Core Pages", 'core_pages', list(assets['core_pages'])[:5]),
            ("Letters", 'letters', list(assets['letters'])[:5]),
            ("Acceptance", 'acceptance_pages', list(assets['acceptance_pages'])[:5])
        ]:
            if pages:
                print(f"\n  {category}:")
                for page in pages:
                    print(f"    • {page}")
                if len(assets[key]) > 5:
                    print(f"    ... and {len(assets[key]) - 5} more")
                    
        # Errors
        if self.errors:
            print("\n⚠️  PARSING ERRORS:")
            for error in self.errors[:5]:
                print(f"  • {error}")
            if len(self.errors) > 5:
                print(f"  ... and {len(self.errors) - 5} more errors")
                
        print("\n" + "=" * 80)
        print("✅ Discovery complete! Ready for asset generation.")
        print("⚠️  REMEMBER: Only generate SAMPLES (5-10 max) for testing!")
        print("    Full generation must be run by the user.")
        print("=" * 80)

def main():
    """Run the asset discovery test."""
    print("\n🚀 Starting Full Asset Discovery Test...")
    print("   This tests YAML parsing only - no API calls are made.\n")
    
    discovery = YAMLAssetDiscovery()
    assets = discovery.discover_all_assets()
    discovery.print_report(assets)
    
    # Save results to JSON for reference
    results = {
        'total_pages': len(assets['all_unique']),
        'total_assets': (len(assets['all_unique']) * 2) + 38,
        'categories': {
            'core_pages': len(assets['core_pages']),
            'letters': len(assets['letters']),
            'acceptance_pages': len(assets['acceptance_pages']),
            'database_pages': len(assets['database_pages']),
            'admin_pages': len(assets['admin_pages'])
        },
        'pages': {
            category: sorted(list(pages))
            for category, pages in assets.items()
            if category != 'all_unique'
        }
    }
    
    with open('asset_discovery_results.json', 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"\n💾 Results saved to asset_discovery_results.json")
    
    return results

if __name__ == "__main__":
    main()