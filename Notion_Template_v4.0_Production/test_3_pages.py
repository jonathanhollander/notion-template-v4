#!/usr/bin/env python3
"""
Test script to deploy only 3 pages with blocks
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
    else:
        # Default to paragraph for unknown types
        return {
            "paragraph": {
                "rich_text": [{"text": {"content": f"[{block_type}] {content}"}}]
            }
        }

def create_test_page(page_data):
    """Create a single test page"""
    title = page_data.get('title', 'Untitled')

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
        logging.info(f"Found {len(page_data['blocks'])} blocks for '{title}'")
        for block in page_data['blocks']:
            built_block = build_block(block)
            children.append(built_block)
            logging.debug(f"Built block: {json.dumps(built_block, indent=2)}")
    else:
        logging.warning(f"No blocks found for '{title}'")

    # Create page payload
    payload = {
        "parent": {"page_id": NOTION_PARENT_PAGEID},
        "properties": properties
    }

    if children:
        payload["children"] = children

    # Log the full payload
    logging.info(f"Creating page '{title}' with {len(children)} blocks")
    logging.debug(f"Full payload: {json.dumps(payload, indent=2)}")

    # Make API call
    try:
        response = req("POST", "https://api.notion.com/v1/pages", data=json.dumps(payload))

        logging.info(f"API Response Status: {response.status_code}")
        logging.debug(f"API Response: {response.text}")

        if response.status_code == 200:
            result = response.json()
            page_id = result.get('id')
            logging.info(f"✅ Created page '{title}': {page_id}")
            return page_id
        else:
            logging.error(f"❌ Failed to create page '{title}': {response.status_code} {response.text}")
            return None

    except Exception as e:
        logging.error(f"❌ Exception creating page '{title}': {e}")
        return None

# Load merged YAML data (copy from test_merged_data.py)
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

# Main test
if __name__ == "__main__":
    print("Loading YAML data...")
    merged_data = load_yaml_data()

    print(f"Total pages available: {len(merged_data['pages'])}")

    # Find first 3 pages with blocks
    test_pages = []
    for page in merged_data['pages']:
        if 'blocks' in page and len(page.get('blocks', [])) > 0:
            test_pages.append(page)
            if len(test_pages) >= 3:
                break

    print(f"Selected {len(test_pages)} pages for testing:")
    for page in test_pages:
        title = page.get('title')
        num_blocks = len(page.get('blocks', []))
        print(f"  - {title}: {num_blocks} blocks")

    print("\nStarting page creation...")
    for i, page in enumerate(test_pages, 1):
        print(f"\n=== Creating page {i}/3: {page.get('title')} ===")
        page_id = create_test_page(page)
        if page_id:
            print(f"✅ Success! Page ID: {page_id}")
        else:
            print(f"❌ Failed to create page")

    print("\n=== Test completed ===")