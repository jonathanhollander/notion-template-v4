#!/usr/bin/env python3
"""
Test script to debug single page creation with blocks
"""

import os
import sys
import json
import yaml
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load YAML file with blocks
yaml_file = "split_yaml/25_digital_legacy.yaml"

with open(yaml_file, 'r') as f:
    data = yaml.safe_load(f)

print(f"Loaded YAML file: {yaml_file}")
print(f"Found {len(data.get('pages', []))} pages")

# Find first page with blocks
for page in data.get('pages', []):
    title = page.get('title', 'No title')
    has_blocks = 'blocks' in page
    num_blocks = len(page.get('blocks', []))

    print(f"\nPage: {title}")
    print(f"Has blocks field: {has_blocks}")
    print(f"Number of blocks: {num_blocks}")

    if has_blocks and num_blocks > 0:
        print(f"First few blocks:")
        for i, block in enumerate(page['blocks'][:3]):  # Show first 3 blocks
            print(f"  Block {i+1}: {block.get('type', 'no type')} - '{block.get('content', 'no content')[:50]}...'")

        # Test build_block function
        print(f"\nTesting build_block function:")

        # Simple version of build_block for testing
        def build_block(block_def):
            block_type = block_def.get('type', 'paragraph')
            if block_type == 'heading_1':
                return {
                    "heading_1": {
                        "rich_text": [{"text": {"content": block_def.get('content', '')}}]
                    }
                }
            elif block_type == 'paragraph':
                return {
                    "paragraph": {
                        "rich_text": [{"text": {"content": block_def.get('content', '')}}]
                    }
                }
            elif block_type == 'heading_2':
                return {
                    "heading_2": {
                        "rich_text": [{"text": {"content": block_def.get('content', '')}}]
                    }
                }
            else:
                return {
                    "paragraph": {
                        "rich_text": [{"text": {"content": f"[{block_type}] {block_def.get('content', '')}"}}]
                    }
                }

        # Test first block
        first_block = page['blocks'][0]
        built_block = build_block(first_block)
        print(f"Built block: {json.dumps(built_block, indent=2)}")

        break
else:
    print("No pages with blocks found!")