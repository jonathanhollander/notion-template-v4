#!/usr/bin/env python3
"""
Test script for ordered deployment with proper parent-child handling
Tests only 3 pages to verify block creation is working correctly
"""

import os
import sys
import json
import yaml
import logging
import requests
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "your_notion_token_here")
NOTION_PARENT_PAGEID = os.getenv("NOTION_PARENT_PAGEID", "251a6c4e-badd-8040-9b97-e14848a10788")
NOTION_VERSION = "2025-09-03"

def req(method, url, data=None):
    """Make request to Notion API"""
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

    response = requests.request(method, url, headers=headers, data=data)
    return response

def build_block(block_def):
    """Build a Notion block from YAML definition"""
    block_type = block_def.get('type', 'paragraph')
    content = block_def.get('content', '')

    if block_type == 'heading_1':
        return {
            "heading_1": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    elif block_type == 'heading_2':
        return {
            "heading_2": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    elif block_type == 'heading_3':
        return {
            "heading_3": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    elif block_type == 'paragraph':
        return {
            "paragraph": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    elif block_type == 'bulleted_list_item':
        return {
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    elif block_type == 'numbered_list_item':
        return {
            "numbered_list_item": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
    elif block_type == 'callout':
        return {
            "callout": {
                "rich_text": [{"text": {"content": content}}],
                "icon": {"emoji": block_def.get('icon', 'emoji:💡').replace('emoji:', '')},
                "color": block_def.get('color', 'default')
            }
        }
    elif block_type == 'to_do':
        return {
            "to_do": {
                "rich_text": [{"text": {"content": content}}],
                "checked": block_def.get('checked', False)
            }
        }
    elif block_type == 'toggle':
        return {
            "toggle": {
                "rich_text": [{"text": {"content": content}}],
                "children": []
            }
        }
    elif block_type == 'divider':
        return {
            "divider": {}
        }
    elif block_type == 'code':
        return {
            "code": {
                "rich_text": [{"text": {"content": content}}],
                "language": block_def.get('language', 'plain text')
            }
        }
    else:
        # Default to paragraph for unknown types
        return {
            "paragraph": {
                "rich_text": [{"text": {"content": f"[{block_type}] {content}"}}]
            }
        }

def create_page_with_parent_check(page_data, parent_pages, created_pages):
    """Create a page with proper parent checking"""
    title = page_data.get('title', 'Untitled')
    parent_name = page_data.get('parent')

    print(f"\n=== CREATING PAGE: {title} ===")
    print(f"Has parent: {parent_name}")
    print(f"Has blocks: {'blocks' in page_data}")
    print(f"Block count: {len(page_data.get('blocks', []))}")

    # Determine parent ID
    if parent_name and parent_name in created_pages:
        parent_id = created_pages[parent_name]
        print(f"Using existing parent '{parent_name}': {parent_id}")
    elif parent_name and parent_name not in created_pages:
        # Create parent first if it exists in our data
        if parent_name in parent_pages:
            print(f"Creating missing parent '{parent_name}' first...")
            parent_id = create_page_with_parent_check(parent_pages[parent_name], parent_pages, created_pages)
            if not parent_id:
                print(f"Failed to create parent '{parent_name}', using root parent")
                parent_id = NOTION_PARENT_PAGEID
        else:
            print(f"Parent '{parent_name}' not found in data, using root parent")
            parent_id = NOTION_PARENT_PAGEID
    else:
        print("No parent specified, using root parent")
        parent_id = NOTION_PARENT_PAGEID

    # Build properties
    properties = {
        "title": {
            "title": [
                {"text": {"content": title}}
            ]
        }
    }

    # Build content blocks
    children = []
    if 'blocks' in page_data:
        print(f"Building {len(page_data['blocks'])} blocks...")
        for i, block in enumerate(page_data['blocks']):
            built_block = build_block(block)
            children.append(built_block)
            print(f"  Block {i+1}: {block.get('type', 'paragraph')} - '{block.get('content', '')[:50]}...'")
    else:
        print("No blocks to build")

    # Create page payload
    payload = {
        "parent": {"page_id": parent_id},
        "properties": properties
    }

    if children:
        payload["children"] = children

    print(f"Creating page with {len(children)} blocks...")

    # Make API call
    try:
        response = req("POST", "https://api.notion.com/v1/pages", data=json.dumps(payload))

        print(f"API Response Status: {response.status_code}")
        if response.status_code != 200:
            print(f"API Error Response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            page_id = result.get('id')
            created_pages[title] = page_id
            print(f"✅ SUCCESS: Created '{title}' with {len(children)} blocks")
            return page_id
        else:
            print(f"❌ FAILED: {response.status_code} {response.text}")
            return None

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return None

def load_yaml_data():
    """Load and merge all YAML files"""
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

def main():
    print("=== ORDERED DEPLOYMENT TEST (3 pages max) ===")

    # Load all page data
    print("Loading YAML data...")
    merged_data = load_yaml_data()
    print(f"Total pages loaded: {len(merged_data['pages'])}")

    # Create lookup tables
    all_pages = {page.get('title'): page for page in merged_data['pages']}
    parent_pages = {}
    child_pages = []

    # Separate parent and child pages
    for page in merged_data['pages']:
        if page.get('parent'):
            child_pages.append(page)
        else:
            parent_pages[page.get('title')] = page

    print(f"Parent pages: {len(parent_pages)}")
    print(f"Child pages: {len(child_pages)}")

    # Find first 3 child pages with blocks for testing
    test_pages = []
    for page in child_pages:
        if 'blocks' in page and len(page.get('blocks', [])) > 0:
            test_pages.append(page)
            if len(test_pages) >= 3:
                break

    print(f"\nSelected {len(test_pages)} pages for testing:")
    for page in test_pages:
        title = page.get('title')
        parent = page.get('parent', 'No parent')
        num_blocks = len(page.get('blocks', []))
        print(f"  - {title}: {num_blocks} blocks (parent: {parent})")

    # Test deployment with proper ordering
    print("\n=== STARTING ORDERED DEPLOYMENT ===")
    created_pages = {}

    for i, page in enumerate(test_pages, 1):
        print(f"\n--- Testing page {i}/3 ---")
        page_id = create_page_with_parent_check(page, all_pages, created_pages)

        if page_id:
            print(f"✅ Page {i} SUCCESS: {page.get('title')}")
        else:
            print(f"❌ Page {i} FAILED: {page.get('title')}")

        print(f"Currently created pages: {len(created_pages)}")

    print("\n=== TEST COMPLETED ===")
    print(f"Total pages created: {len(created_pages)}")
    for title, page_id in created_pages.items():
        print(f"  ✅ {title}: {page_id}")

if __name__ == "__main__":
    main()