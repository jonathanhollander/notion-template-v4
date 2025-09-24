"""
Enhanced logging utilities for deploy.py
Provides detailed logging for asset deployment and page creation
"""

import logging
import json
from typing import Dict, List, Any, Optional
from modules.logging_config import AssetLogger, APIRequestLogger

# Global loggers
asset_logger = None
deployment_logger = None


def init_enhanced_logging():
    """Initialize enhanced logging for deployment"""
    global asset_logger, deployment_logger

    asset_logger = AssetLogger()
    deployment_logger = logging.getLogger('estate_planning.deployment')

    deployment_logger.info("Enhanced deployment logging initialized")
    return asset_logger, deployment_logger


def log_page_creation_start(page_data: Dict, parent_info: str = ""):
    """Log the start of page creation with full context"""
    if not asset_logger:
        return

    title = page_data.get('title', 'Untitled')

    # Count blocks if present
    total_blocks = 0
    if 'children' in page_data:
        total_blocks = len(page_data['children'])
    elif 'blocks' in page_data:
        total_blocks = len(page_data['blocks'])

    asset_logger.log_page_processing(title, total_blocks)

    # Log additional page details
    deployment_logger.info(f"Creating page: '{title}'")
    if parent_info:
        deployment_logger.info(f"  Parent: {parent_info}")

    # Log page properties being set
    if 'properties' in page_data:
        props = page_data['properties']
        prop_names = list(props.keys()) if isinstance(props, dict) else []
        deployment_logger.debug(f"  Properties: {prop_names}")

        # Log specific important properties
        for prop_name, prop_value in (props.items() if isinstance(props, dict) else []):
            if prop_name in ['icon_file', 'cover_file', 'role', 'complexity']:
                deployment_logger.debug(f"  {prop_name}: {prop_value}")

    # Log if page has assets
    has_icon = 'icon_file' in page_data or ('properties' in page_data and 'icon_file' in page_data['properties'])
    has_cover = 'cover_file' in page_data or ('properties' in page_data and 'cover_file' in page_data['properties'])

    if has_icon or has_cover:
        asset_types = []
        if has_icon:
            asset_types.append('icon')
        if has_cover:
            asset_types.append('cover')
        deployment_logger.info(f"  Assets required: {', '.join(asset_types)}")


def log_block_creation(block_type: str, block_data: Dict, success: bool = True):
    """Log individual block creation with content details"""
    if not asset_logger:
        return

    # Extract content preview based on block type
    content_preview = ""

    if block_type == "paragraph" and "paragraph" in block_data:
        rich_text = block_data["paragraph"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "heading_1" and "heading_1" in block_data:
        rich_text = block_data["heading_1"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "heading_2" and "heading_2" in block_data:
        rich_text = block_data["heading_2"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "heading_3" and "heading_3" in block_data:
        rich_text = block_data["heading_3"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "bulleted_list_item" and "bulleted_list_item" in block_data:
        rich_text = block_data["bulleted_list_item"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "numbered_list_item" and "numbered_list_item" in block_data:
        rich_text = block_data["numbered_list_item"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "toggle" and "toggle" in block_data:
        rich_text = block_data["toggle"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "quote" and "quote" in block_data:
        rich_text = block_data["quote"].get("rich_text", [])
        if rich_text and len(rich_text) > 0:
            content_preview = rich_text[0].get("text", {}).get("content", "")

    elif block_type == "divider":
        content_preview = "--- (divider) ---"

    elif block_type == "image" and "image" in block_data:
        if "external" in block_data["image"]:
            content_preview = f"External: {block_data['image']['external'].get('url', 'unknown')}"
        elif "file" in block_data["image"]:
            content_preview = f"File: {block_data['image']['file'].get('url', 'unknown')}"
        else:
            content_preview = "Image block"

    else:
        content_preview = f"{block_type} block"

    asset_logger.log_block_creation(block_type, content_preview, success)


def log_yaml_section_processing(section_name: str, yaml_data: Dict):
    """Log YAML section processing with item counts"""
    if not asset_logger:
        return

    items_found = 0
    section_info = ""

    if section_name == "pages" and "pages" in yaml_data:
        items_found = len(yaml_data["pages"])
        section_info = f"{items_found} pages found"

    elif section_name == "databases" and "databases" in yaml_data:
        items_found = len(yaml_data["databases"])
        section_info = f"{items_found} databases found"

    elif section_name in yaml_data:
        if isinstance(yaml_data[section_name], list):
            items_found = len(yaml_data[section_name])
        elif isinstance(yaml_data[section_name], dict):
            items_found = len(yaml_data[section_name].keys())
        else:
            items_found = 1

        section_info = f"{items_found} items found"

    asset_logger.log_yaml_processing(section_name, items_found)
    deployment_logger.debug(f"YAML section '{section_name}': {section_info}")


def log_asset_processing(asset_type: str, asset_info: Dict, success: bool = True):
    """Log asset processing (icons, covers, files)"""
    if not asset_logger:
        return

    asset_path = ""

    if isinstance(asset_info, dict):
        # Extract path from various possible structures
        if 'file_path' in asset_info:
            asset_path = asset_info['file_path']
        elif 'url' in asset_info:
            asset_path = asset_info['url']
        elif 'external' in asset_info and 'url' in asset_info['external']:
            asset_path = asset_info['external']['url']
        elif 'file' in asset_info and 'url' in asset_info['file']:
            asset_path = asset_info['file']['url']
        else:
            asset_path = str(asset_info)
    elif isinstance(asset_info, str):
        asset_path = asset_info
    else:
        asset_path = f"<{type(asset_info).__name__}>"

    asset_logger.log_asset_processing(asset_type, asset_path, success)


def log_page_creation_complete(page_title: str, page_id: str, success: bool = True):
    """Log completion of page creation"""
    if not deployment_logger:
        return

    if success:
        deployment_logger.info(f"✓ Page created successfully: '{page_title}' (ID: {page_id})")
    else:
        deployment_logger.error(f"✗ Failed to create page: '{page_title}'")


def log_payload_details(operation: str, payload: Dict):
    """Log detailed payload information for debugging"""
    if not deployment_logger:
        return

    deployment_logger.debug(f"{operation} payload structure:")

    if isinstance(payload, dict):
        # Log top-level keys
        top_keys = list(payload.keys())
        deployment_logger.debug(f"  Top-level keys: {top_keys}")

        # Log parent information
        if 'parent' in payload:
            parent = payload['parent']
            if 'page_id' in parent:
                deployment_logger.debug(f"  Parent page ID: {parent['page_id']}")
            elif 'database_id' in parent:
                deployment_logger.debug(f"  Parent database ID: {parent['database_id']}")

        # Log properties count
        if 'properties' in payload:
            props = payload['properties']
            if isinstance(props, dict):
                deployment_logger.debug(f"  Properties count: {len(props)}")
                deployment_logger.debug(f"  Property names: {list(props.keys())}")

        # Log children/blocks count
        if 'children' in payload:
            children = payload['children']
            if isinstance(children, list):
                deployment_logger.debug(f"  Children blocks: {len(children)}")

                # Log block types
                block_types = []
                for child in children[:10]:  # Limit to first 10
                    if isinstance(child, dict) and 'type' in child:
                        block_types.append(child['type'])

                if block_types:
                    deployment_logger.debug(f"  Block types: {block_types}")

                if len(children) > 10:
                    deployment_logger.debug(f"  ... and {len(children) - 10} more blocks")


def log_content_transformation(from_format: str, to_format: str, data: Any):
    """Log content format transformations"""
    if not asset_logger:
        return

    item_count = 0

    if isinstance(data, list):
        item_count = len(data)
    elif isinstance(data, dict):
        item_count = len(data.keys())
    elif isinstance(data, str):
        item_count = 1

    asset_logger.log_content_transformation(from_format, to_format, item_count)


def log_deployment_summary():
    """Log final deployment summary"""
    if asset_logger:
        asset_logger.log_asset_summary()

    if deployment_logger:
        deployment_logger.info("Enhanced deployment logging completed")


# Convenience function to log API calls with context
def log_api_call_with_context(operation: str, url: str, payload: Dict = None):
    """Log API call with contextual information"""
    if not deployment_logger:
        return

    deployment_logger.debug(f"API Call: {operation}")
    deployment_logger.debug(f"  URL: {url}")

    if payload:
        log_payload_details(operation, payload)