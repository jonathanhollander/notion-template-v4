#!/usr/bin/env python3
"""
Test script to check merged YAML data
"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path

# Load the load_yaml_data function from deploy.py
sys.path.append('.')

def load_yaml_data(yaml_dir: Path = None) -> dict:
    """Load and merge all YAML files"""
    if yaml_dir is None:
        yaml_dir = Path(__file__).parent / "split_yaml"
    else:
        yaml_dir = Path(yaml_dir)

    if not yaml_dir.exists():
        logging.error(f"YAML directory not found: {yaml_dir}")
        return {}

    merged = {
        "pages": [],
        "db": {
            "schemas": {},
            "seed_rows": {}
        }
    }

    # Process YAML files in sorted order
    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    print(f"Found {len(yaml_files)} YAML files to process")

    for yaml_file in yaml_files:
        print(f"Loading {yaml_file.name}")
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            # Merge pages
            if 'pages' in data:
                merged['pages'].extend(data['pages'])

        except Exception as e:
            print(f"Failed to load {yaml_file.name}: {e}")

    print(f"Merged {len(merged['pages'])} pages")
    return merged

# Load merged data
merged_data = load_yaml_data()

# Find pages with blocks
pages_with_blocks = []
pages_without_blocks = []

for page in merged_data['pages']:
    title = page.get('title', 'No title')
    has_blocks = 'blocks' in page
    num_blocks = len(page.get('blocks', []))

    if has_blocks and num_blocks > 0:
        pages_with_blocks.append((title, num_blocks))
    else:
        pages_without_blocks.append(title)

print(f"\n=== SUMMARY ===")
print(f"Total pages: {len(merged_data['pages'])}")
print(f"Pages with blocks: {len(pages_with_blocks)}")
print(f"Pages without blocks: {len(pages_without_blocks)}")

print(f"\n=== PAGES WITH BLOCKS ===")
for title, num_blocks in pages_with_blocks[:10]:  # Show first 10
    print(f"  {title}: {num_blocks} blocks")

print(f"\n=== FIRST FEW PAGES WITHOUT BLOCKS ===")
for title in pages_without_blocks[:10]:  # Show first 10
    print(f"  {title}")

# Test specific page we know has blocks
target_page = "Google Inactive Account Manager"
for page in merged_data['pages']:
    if page.get('title') == target_page:
        print(f"\n=== FOUND TARGET PAGE: {target_page} ===")
        print(f"Has blocks: {'blocks' in page}")
        print(f"Number of blocks: {len(page.get('blocks', []))}")
        if 'blocks' in page:
            print("First block:")
            print(json.dumps(page['blocks'][0], indent=2))
        break
else:
    print(f"\n=== TARGET PAGE NOT FOUND: {target_page} ===")