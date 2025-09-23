#!/usr/bin/env python3
"""
Analyze page structure and parent relationships
"""

import yaml
from pathlib import Path

def load_yaml_data():
    yaml_dir = Path("split_yaml")
    merged = {"pages": []}
    yaml_files = sorted(yaml_dir.glob("*.yaml"))

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data and 'pages' in data:
                merged['pages'].extend(data['pages'])
        except Exception as e:
            print(f"Failed to load {yaml_file.name}: {e}")

    return merged

# Load data
merged_data = load_yaml_data()

# Analyze structure
pages_with_blocks = []
pages_without_blocks = []
parent_relationships = {}

for page in merged_data['pages']:
    title = page.get('title', 'No title')
    has_blocks = 'blocks' in page
    num_blocks = len(page.get('blocks', []))
    parent = page.get('parent')

    if has_blocks and num_blocks > 0:
        pages_with_blocks.append((title, num_blocks, parent))
    else:
        pages_without_blocks.append((title, parent))

    if parent:
        if parent not in parent_relationships:
            parent_relationships[parent] = []
        parent_relationships[parent].append(title)

print("=== PAGES WITH BLOCKS ===")
root_pages = []
child_pages = []

for title, num_blocks, parent in pages_with_blocks:
    if parent:
        child_pages.append((title, num_blocks, parent))
    else:
        root_pages.append((title, num_blocks))

print(f"\nROOT PAGES (no parent): {len(root_pages)}")
for title, num_blocks in root_pages:
    print(f"  - {title}: {num_blocks} blocks")

print(f"\nCHILD PAGES (have parent): {len(child_pages)}")
for title, num_blocks, parent in child_pages:
    print(f"  - {title}: {num_blocks} blocks (parent: {parent})")

print(f"\n=== PARENT-CHILD RELATIONSHIPS ===")
for parent, children in parent_relationships.items():
    print(f"{parent} has {len(children)} children:")
    for child in children:
        print(f"  - {child}")

# Find pages that should be created first (root pages with blocks)
print(f"\n=== RECOMMENDED CREATION ORDER ===")
print("1. First create root pages with blocks:")
for title, num_blocks in root_pages:
    print(f"   ✅ {title}")

print("\n2. Then create child pages with blocks (after parents exist):")
for title, num_blocks, parent in child_pages:
    print(f"   🔗 {title} (needs: {parent})")