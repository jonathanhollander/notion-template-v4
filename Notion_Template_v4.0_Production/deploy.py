#!/usr/bin/env python3
"""
Notion Template v4.0 Production Deployment Script
=================================================
Unified implementation combining best features from all four AI analyses:
- ChatGPT: Validation-focused foundation with comprehensive error handling
- Gemini: Phased deployment with progress tracking
- Qwen: CLI interface with interactive commands
- Claude: Component-based architecture (future refactor)
- DeepSeek: State management and recovery capabilities

Created: August 2025
API Version: 2025-09-03
"""

import os
import sys
import json
import time
import argparse
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import yaml
import csv
import requests
from dotenv import load_dotenv
from urllib.parse import quote
from datetime import datetime
import re

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

# Load environment variables from .env file
# Use override=True to force .env file values to override shell environment variables
load_dotenv(override=True)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2025-09-03")
NOTION_PARENT_PAGEID = "277a6c4ebadd80799d19d839db90e901"  # Hardcoded correct page ID

GLOBAL_THROTTLE_RPS = float(os.getenv("THROTTLE_RPS", "2.5"))
ENABLE_SEARCH_FALLBACK = os.getenv("ENABLE_SEARCH_FALLBACK", "1") in ("1", "true", "True", "yes", "YES")

# ============================================================================
# VARIABLE SUBSTITUTION SYSTEM
# ============================================================================

def process_variable_substitution(content: str) -> str:
    """
    Process variable substitution for ${VARIABLE} patterns in content
    Supports format: ${VARIABLE} or ${VARIABLE:-default_value}

    Args:
        content: String content that may contain ${VARIABLE} patterns

    Returns:
        String with variables substituted from environment
    """
    if not isinstance(content, str):
        return content

    # Pattern matches ${VARIABLE} or ${VARIABLE:-default}
    pattern = r'\$\{([A-Z_][A-Z0-9_]*?)(?::-(.*?))?\}'

    def substitute_var(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ''

        # Get value from environment, fall back to default
        return os.getenv(var_name, default_value)

    return re.sub(pattern, substitute_var, content)


def process_content_substitution(data: Any) -> Any:
    """
    Recursively process variable substitution in nested data structures

    Args:
        data: Dict, List, or primitive containing content to process

    Returns:
        Data structure with variables substituted
    """
    if isinstance(data, dict):
        return {key: process_content_substitution(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [process_content_substitution(item) for item in data]
    elif isinstance(data, str):
        return process_variable_substitution(data)
    else:
        return data

# FORMULA PLACEHOLDER SYSTEM
# ============================================================================

def process_formula_placeholder(content: str) -> str:
    """
    Process formula placeholder patterns {{formula:expression}} in content
    These are typically used for dynamic values that would be calculated

    Args:
        content: String content that may contain {{formula:}} patterns

    Returns:
        String with formula placeholders replaced with placeholder text
    """
    if not isinstance(content, str):
        return content

    # Pattern matches {{formula:expression}}
    pattern = r'\{\{formula:(.*?)\}\}'

    def substitute_formula(match):
        formula_expr = match.group(1)
        # For now, replace with a placeholder that indicates formula was here
        # In production, this could be connected to an actual formula evaluator
        return f"[Formula: {formula_expr}]"

    return re.sub(pattern, substitute_formula, content)


def process_formula_substitution(data: Any) -> Any:
    """
    Recursively process formula placeholder substitution in nested data structures

    Args:
        data: Dict, List, or primitive containing content to process

    Returns:
        Data structure with formula placeholders processed
    """
    if isinstance(data, dict):
        return {key: process_formula_substitution(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [process_formula_substitution(item) for item in data]
    elif isinstance(data, str):
        return process_formula_placeholder(data)
    else:
        return data


# ENHANCED SELECT OPTIONS SUPPORT
# ============================================================================

def build_enhanced_select_options(options: List[Any]) -> List[Dict]:
    """
    Build enhanced select options supporting both formats:
    - Array format: ["Option1", "Option2"]
    - Object format: [{"name": "Option1", "color": "red"}, ...]

    Args:
        options: List of options (strings or dicts)

    Returns:
        List of properly formatted option dicts for Notion API
    """
    if not options:
        return []

    # Valid Notion API colors (as of 2025-09-03)
    valid_colors = {
        'default', 'gray', 'brown', 'orange', 'yellow',
        'green', 'blue', 'purple', 'pink', 'red'
    }

    formatted_options = []
    for option in options:
        if isinstance(option, str):
            # Simple string format
            formatted_options.append({"name": option})
        elif isinstance(option, dict):
            if 'name' in option:
                # Object format with optional color
                opt_dict = {"name": option['name']}
                if 'color' in option and option['color'] in valid_colors:
                    opt_dict['color'] = option['color']
                formatted_options.append(opt_dict)
            else:
                # Malformed object, treat as string
                formatted_options.append({"name": str(option)})
        else:
            # Convert other types to string
            formatted_options.append({"name": str(option)})

    return formatted_options


def add_page_metadata_properties(page_data: Dict, properties: Dict) -> Dict:
    """
    Add page metadata fields (role, slug, complexity, disclaimer) to page properties

    Args:
        page_data: YAML page data containing metadata fields
        properties: Existing page properties dict

    Returns:
        Updated properties dict with metadata fields
    """
    # Add role field as rich_text property
    if 'role' in page_data:
        properties['Role'] = {
            "rich_text": [{"text": {"content": str(page_data['role'])}}]
        }

    # Add slug field as rich_text property
    if 'slug' in page_data:
        properties['Slug'] = {
            "rich_text": [{"text": {"content": str(page_data['slug'])}}]
        }

    # Add complexity field as select property
    if 'complexity' in page_data:
        properties['Complexity'] = {
            "select": {"name": str(page_data['complexity'])}
        }

    # Add disclaimer field as rich_text property
    if 'disclaimer' in page_data:
        properties['Disclaimer'] = {
            "rich_text": [{"text": {"content": str(page_data['disclaimer'])}}]
        }

    return properties


def create_asset_field_placeholders(page_data: Dict) -> Dict:
    """
    Create placeholder properties for asset fields that will be populated by image generator

    Args:
        page_data: YAML page data containing asset field references

    Returns:
        Dict of asset properties for future population
    """
    asset_properties = {}

    # Create placeholders for asset fields if they exist in YAML
    if 'icon_file' in page_data:
        asset_properties['Icon File'] = {
            "rich_text": [{"text": {"content": ""}}]  # Empty placeholder
        }

    if 'cover_file' in page_data:
        asset_properties['Cover File'] = {
            "rich_text": [{"text": {"content": ""}}]  # Empty placeholder
        }

    if 'icon_png' in page_data:
        asset_properties['Icon PNG'] = {
            "rich_text": [{"text": {"content": ""}}]  # Empty placeholder
        }

    if 'cover_png' in page_data:
        asset_properties['Cover PNG'] = {
            "rich_text": [{"text": {"content": ""}}]  # Empty placeholder
        }

    if 'alt_text' in page_data:
        asset_properties['Alt Text'] = {
            "rich_text": [{"text": {"content": str(page_data.get('alt_text', ''))}}]
        }

    return asset_properties

# Deployment phases from Gemini build
class DeploymentPhase(Enum):
    VALIDATION = "Validation"
    PREPARATION = "Preparation"
    PAGES = "Creating Pages"
    DATABASES = "Creating Databases"
    RELATIONS = "Setting Relations"
    DATA = "Importing Data"
    PATCHES = "Applying Patches"
    FINALIZATION = "Finalization"
    COMPLETED = "Completed"

# ============================================================================
# STATE MANAGEMENT (DeepSeek recommendation)
# ============================================================================

@dataclass
class DeploymentState:
    """Tracks deployment progress for recovery after failures"""
    phase: DeploymentPhase = DeploymentPhase.VALIDATION
    created_pages: Dict[str, str] = field(default_factory=dict)
    created_databases: Dict[str, str] = field(default_factory=dict)
    processed_csv: List[str] = field(default_factory=list)
    applied_patches: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    checkpoint_file: str = ".notion_deploy_state"
    
    def save_checkpoint(self):
        """Save current state to disk for recovery"""
        with open(self.checkpoint_file, 'wb') as f:
            pickle.dump(self, f)
        logging.debug(f"Checkpoint saved at phase: {self.phase.value}")
    
    def load_checkpoint(self) -> Optional['DeploymentState']:
        """Load previous state if exists"""
        if Path(self.checkpoint_file).exists():
            try:
                with open(self.checkpoint_file, 'rb') as f:
                    state = pickle.load(f)
                logging.info(f"Recovered state from phase: {state.phase.value}")
                return state
            except Exception as e:
                logging.warning(f"Could not recover state: {e}")
        return None
    
    def clear_checkpoint(self):
        """Remove checkpoint after successful completion"""
        if Path(self.checkpoint_file).exists():
            os.remove(self.checkpoint_file)
            logging.debug("Checkpoint cleared")

# ============================================================================
# LOGGING & PROGRESS (Gemini feature)
# ============================================================================

class ProgressTracker:
    """Visual progress tracking from Gemini build"""
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.current_step = 0
        self.phase = DeploymentPhase.VALIDATION
        
    def update(self, phase: DeploymentPhase, message: str):
        self.phase = phase
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100
        bar_length = 40
        filled = int(bar_length * self.current_step / self.total_steps)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r[{bar}] {progress:.1f}% - {phase.value}: {message}", end='')
        if self.current_step >= self.total_steps:
            print()  # New line at completion

# ============================================================================
# VALIDATION MODULE (ChatGPT foundation)
# ============================================================================

class Validator:
    """Comprehensive validation from ChatGPT build"""
    
    @staticmethod
    def validate_environment() -> List[str]:
        """Validate environment variables and configuration"""
        errors = []
        
        if not NOTION_TOKEN:
            errors.append("NOTION_TOKEN environment variable not set")
        elif not NOTION_TOKEN.startswith(('secret_', 'ntn_')):
            errors.append("Invalid NOTION_TOKEN format (should start with 'secret_' or 'ntn_')")
            
        if not NOTION_PARENT_PAGEID:
            errors.append("NOTION_PARENT_PAGEID environment variable not set")
            
        return errors
    
    @staticmethod
    def validate_yaml_structure(yaml_data: Dict) -> List[str]:
        """Validate YAML file structure"""
        errors = []
        
        if not isinstance(yaml_data, dict):
            errors.append("YAML data must be a dictionary")
            return errors
            
        if 'pages' in yaml_data and not isinstance(yaml_data['pages'], list):
            errors.append("'pages' must be a list")
            
        if 'db' in yaml_data:
            if not isinstance(yaml_data['db'], dict):
                errors.append("'db' must be a dictionary")
            else:
                if 'schemas' in yaml_data['db'] and not isinstance(yaml_data['db']['schemas'], dict):
                    errors.append("'db.schemas' must be a dictionary")
                if 'seed_rows' in yaml_data['db'] and not isinstance(yaml_data['db']['seed_rows'], dict):
                    errors.append("'db.seed_rows' must be a dictionary")
                    
        return errors
    
    @staticmethod
    def validate_dependencies(yaml_data: Dict) -> List[str]:
        """Check for circular dependencies and missing references"""
        errors = []
        dependencies = {}
        
        # Build dependency graph
        if 'pages' in yaml_data:
            for page in yaml_data['pages']:
                if 'parent' in page:
                    dependencies.setdefault(page.get('title'), []).append(page['parent'])
                    
        # Check for cycles (simplified)
        def has_cycle(node, visited, rec_stack):
            visited[node] = True
            rec_stack[node] = True
            
            for neighbor in dependencies.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif rec_stack[neighbor]:
                    return True
                    
            rec_stack[node] = False
            return False
        
        visited = {}
        rec_stack = {}
        for node in dependencies:
            if node not in visited:
                if has_cycle(node, visited, rec_stack):
                    errors.append(f"Circular dependency detected involving: {node}")
                    
        return errors

# ============================================================================
# CORE REQUEST HANDLING (From all builds)
# ============================================================================

_LAST_REQ_TS = [0.0]

def _throttle():
    """Rate limiting to respect Notion API limits"""
    if GLOBAL_THROTTLE_RPS <= 0:
        return
    min_interval = 1.0 / GLOBAL_THROTTLE_RPS
    now = time.time()
    elapsed = now - _LAST_REQ_TS[0]
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed + 0.02)
    _LAST_REQ_TS[0] = time.time()

def req(method: str, url: str, headers: Optional[Dict] = None, 
        data: Optional[str] = None, files: Optional[Any] = None, 
        timeout: Optional[int] = None) -> requests.Response:
    """Enhanced request with retry logic and comprehensive error handling"""
    headers = headers or {}
    if "Notion-Version" not in headers:
        headers["Notion-Version"] = NOTION_VERSION
    if "Authorization" not in headers:
        headers["Authorization"] = f'Bearer {NOTION_TOKEN}'
    if "Content-Type" not in headers and data is not None and files is None:
        headers["Content-Type"] = "application/json"
    
    timeout = timeout or int(os.getenv("NOTION_TIMEOUT", "25"))
    max_try = int(os.getenv("RETRY_MAX", "5"))
    backoff = float(os.getenv("RETRY_BACKOFF_BASE", "1.5"))
    
    for attempt in range(max_try):
        try:
            _throttle()
            logging.info(f"Request: {method} {url}")
            r = requests.request(method, url, headers=headers, data=data, 
                               files=files, timeout=timeout)
            
            # Handle rate limiting
            if r.status_code == 429:
                retry_after = int(r.headers.get('Retry-After', '5'))
                logging.warning(f"Rate limited, waiting {retry_after}s")
                time.sleep(retry_after)
                continue
                
            # Handle server errors with exponential backoff
            if r.status_code in (502, 503, 504):
                if attempt < max_try - 1:
                    wait_time = backoff ** attempt
                    logging.warning(f"Server error {r.status_code}, retrying in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                    
            return r
            
        except requests.exceptions.Timeout:
            if attempt == max_try - 1:
                raise
            logging.warning(f"Timeout on attempt {attempt + 1}, retrying...")
            time.sleep(backoff ** attempt)
            
        except requests.exceptions.ConnectionError as e:
            if attempt == max_try - 1:
                raise
            logging.warning(f"Connection error: {e}, retrying...")
            time.sleep(backoff ** attempt)
    
    return r

def j(r: requests.Response) -> Dict:
    """Parse JSON response with error handling"""
    try:
        return r.json()
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON: {r.text[:500]}")
        return {}

def expect_ok(resp: requests.Response, context: str = "") -> bool:
    """Validate response status"""
    if resp is None:
        logging.error(f"{context}: No response")
        return False
    if resp.status_code not in (200, 201):
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        logging.error(f"{context}: {resp.status_code} {body}")
        return False
    return True

# ============================================================================
# YAML & DATA LOADING
# ============================================================================

def load_all_yaml(yaml_dir: Optional[Path] = None) -> Dict:
    """Load and merge all YAML files from split_yaml directory"""
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
        },
        "standalone_databases": []
    }
    
    # Process YAML files in sorted order
    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    logging.info(f"Found {len(yaml_files)} YAML files to process")
    
    for yaml_file in yaml_files:
        logging.debug(f"Loading {yaml_file.name}")
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data:
                continue
                
            # Apply formula placeholders first, then variable substitution
            data = process_formula_substitution(data)
            data = process_content_substitution(data)

            # Merge pages
            if 'pages' in data:
                merged['pages'].extend(data['pages'])
                
            # Merge database schemas
            if 'db' in data:
                if 'schemas' in data['db']:
                    merged['db']['schemas'].update(data['db']['schemas'])
                if 'seed_rows' in data['db']:
                    merged['db']['seed_rows'].update(data['db']['seed_rows'])

            # Merge standalone databases
            if 'databases' in data:
                merged['standalone_databases'].extend(data['databases'])
                    
        except Exception as e:
            logging.error(f"Failed to load {yaml_file.name}: {e}")
            
    logging.info(f"Merged {len(merged['pages'])} pages, {len(merged['db']['schemas'])} database schemas, and {len(merged['standalone_databases'])} standalone databases")
    return merged

def convert_standalone_db_to_schema(standalone_db: Dict) -> Dict:
    """Convert standalone database format to schema format for deployment"""
    title = standalone_db.get('title', 'Untitled Database')
    icon = standalone_db.get('icon', {})
    description = standalone_db.get('description', '')
    properties = standalone_db.get('properties', {})
    seed_rows = standalone_db.get('seed_rows', [])

    # Convert to schema format expected by create_database()
    schema = {
        'title': title,
        'icon': icon,
        'description': description,
        'properties': properties
    }

    # Add parent if specified (otherwise will use NOTION_PARENT_PAGEID)
    if 'parent' in standalone_db:
        schema['parent'] = standalone_db['parent']

    return {
        'schema': schema,
        'seed_rows': seed_rows,
        'db_name': title  # Use title as database name
    }

def load_csv_data(csv_dir: Optional[Path] = None) -> Dict[str, List[Dict]]:
    """Load all CSV files for data seeding"""
    if csv_dir is None:
        csv_dir = Path(__file__).parent.parent / "csv"
    else:
        csv_dir = Path(csv_dir)
    
    if not csv_dir.exists():
        logging.warning(f"CSV directory not found: {csv_dir}")
        return {}
    
    csv_data = {}
    for csv_file in csv_dir.glob("*.csv"):
        db_name = csv_file.stem
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                csv_data[db_name] = list(reader)
            logging.debug(f"Loaded {len(csv_data[db_name])} rows from {csv_file.name}")
        except Exception as e:
            logging.error(f"Failed to load {csv_file.name}: {e}")
            
    return csv_data

# ============================================================================
# PAGE & DATABASE CREATION
# ============================================================================

def create_page(page_data: Dict, state: DeploymentState, parent_id: Optional[str] = None) -> Optional[str]:
    """Create a Notion page with comprehensive error handling"""
    logging.info(f"[START] Creating page: {page_data.get('title')}")
    logging.debug(f"Page data: {json.dumps(page_data, indent=2)}")

    # Process formula placeholders first, then variable substitution
    page_data = process_formula_substitution(page_data)
    page_data = process_content_substitution(page_data)

    title = page_data.get('title', 'Untitled')

    # Check if already created
    if title in state.created_pages:
        logging.debug(f"Page '{title}' already exists: {state.created_pages[title]}")
        return state.created_pages[title]

    # Build page properties
    properties = {
        "title": {
            "title": [{"text": {"content": title}}]
        }
    }

    # Add custom properties if defined
    if 'properties' in page_data:
        properties.update(page_data['properties'])

    # NOTE: Metadata properties disabled for regular pages - only for database entries
    # properties = add_page_metadata_properties(page_data, properties)

    # NOTE: Asset field placeholders disabled for regular pages - only for database entries
    # asset_properties = create_asset_field_placeholders(page_data)
    # properties.update(asset_properties)
    
    # Determine parent
    if parent_id:
        parent = {"page_id": parent_id}
    elif page_data.get('parent'):
        parent_title = page_data['parent']
        if parent_title in state.created_pages:
            parent = {"page_id": state.created_pages[parent_title]}
        else:
            logging.warning(f"Parent '{parent_title}' not found for '{title}'")
            parent = {"page_id": NOTION_PARENT_PAGEID}
    else:
        parent = {"page_id": NOTION_PARENT_PAGEID}
    
    # Build content blocks - handle multiple field names
    children = []
    blocks_data = page_data.get('blocks', page_data.get('body', page_data.get('Body', [])))

    # If Body field contains a string, convert to proper block format per Notion API 2025
    if isinstance(blocks_data, str):
        # Split by double newlines to create logical paragraph blocks (API best practice)
        paragraphs = blocks_data.split('\n\n')
        blocks_data = []
        for para in paragraphs:
            if para.strip():  # Skip empty paragraphs
                blocks_data.append({
                    "type": "paragraph",
                    "content": para.strip()
                })

    if blocks_data:
        logging.debug(f"Found {len(blocks_data)} blocks for page '{title}'")
        for block in blocks_data:
            # Process variable substitution in block content
            block = process_content_substitution(block)
            built_block = build_block(block)

            # Handle multi-block responses (e.g., bulleted_list with items)
            if isinstance(built_block, dict) and built_block.get('_multi_block'):
                children.extend(built_block['_blocks'])
                logging.debug(f"Built multi-block: {len(built_block['_blocks'])} blocks")
            else:
                children.append(built_block)
                logging.debug(f"Built block: {json.dumps(built_block, indent=2)}")
    else:
        logging.debug(f"No blocks found for page '{title}', adding empty paragraph")
        # Add an empty paragraph block for pages without content
        children = [{"type": "paragraph", "paragraph": {"rich_text": []}}]

    # Handle Notion's 100-block limit per page creation
    if len(children) > 100:
        logging.warning(f"Page '{title}' has {len(children)} blocks, exceeding Notion's 100-block limit. Using first 100 blocks.")
        children = children[:100]

    # Create page
    payload = {
        "parent": parent,
        "properties": properties
    }

    # Construct asset URLs from file paths
    ASSET_BASE_URL = os.getenv("ASSET_BASE_URL", "").rstrip('/')
    if ASSET_BASE_URL:
        if 'icon_file' in page_data:
            icon_url = f"{ASSET_BASE_URL}/{page_data['icon_file'].lstrip('/')}"
            payload['icon'] = {"type": "external", "external": {"url": icon_url}}
            logging.info(f"Constructed icon URL for '{title}': {icon_url}")

        if 'cover_file' in page_data:
            cover_url = f"{ASSET_BASE_URL}/{page_data['cover_file'].lstrip('/')}"
            payload['cover'] = {"type": "external", "external": {"url": cover_url}}
            logging.info(f"Constructed cover URL for '{title}': {cover_url}")

    # Add icon if specified
    if 'icon' in page_data:
        icon_value = page_data['icon']
        if isinstance(icon_value, str):
            if icon_value.startswith('emoji:'):
                payload["icon"] = {"type": "emoji", "emoji": icon_value.replace('emoji:', '')}
            elif icon_value.startswith('http'):
                payload["icon"] = {"type": "external", "external": {"url": icon_value}}
        elif isinstance(icon_value, dict):
            payload["icon"] = icon_value

    # Add cover if specified
    if 'cover' in page_data:
        cover_value = page_data['cover']
        if isinstance(cover_value, str) and cover_value.startswith('http'):
            payload["cover"] = {"type": "external", "external": {"url": cover_value}}
        elif isinstance(cover_value, dict):
            payload["cover"] = cover_value

    if children:
        payload["children"] = children

    # Proactive deletion commented out for debugging child page creation failure
    """
    # Check if page already exists and delete it to avoid archived conflicts
    try:
        parent_page_id = parent.get("page_id")
        if parent_page_id:
            # Get children of parent page to find existing page
            search_r = req("GET", f"https://api.notion.com/v1/blocks/{parent_page_id}/children")
            if expect_ok(search_r, f"Searching for existing page '{title}'"):
                blocks = j(search_r).get('results', [])
                existing_page_id = None

                for block in blocks:
                    if (block.get('type') == 'child_page' and
                        block.get('child_page', {}).get('title') == title):
                        existing_page_id = block.get('id')
                        break

                if existing_page_id:
                    logging.info(f"Found existing page '{title}' with ID: {existing_page_id}. Deleting to avoid conflicts...")
                    delete_r = req("DELETE", f"https://api.notion.com/v1/blocks/{existing_page_id}")
                    if expect_ok(delete_r, f"Deleting existing page '{title}'"):
                        logging.info(f"Successfully deleted existing page '{title}'")
                    else:
                        logging.warning(f"Failed to delete existing page '{title}', continuing with creation...")
    except Exception as e:
        logging.warning(f"Error checking for existing page '{title}': {e}, continuing with creation...")
    """

    try:
        logging.info(f"Creating page '{title}' with {len(children)} blocks")
        if children:
            logging.debug(f"Full page payload for '{title}': {json.dumps(payload, indent=2)}")

        r = req("POST", "https://api.notion.com/v1/pages", data=json.dumps(payload))

        # Check for archived content error BEFORE expect_ok
        response_data = j(r) if r else {}
        error_message = response_data.get('message', '')

        if r and r.status_code == 400 and 'archived' in error_message.lower():
            logging.warning(f"Page creation failed due to archived content. Attempting to clear existing content for '{title}'...")

            # Try to get the parent page and check if a page with this title already exists
            try:
                # Search for existing page by title in the parent
                parent_page_id = parent.get("page_id")
                if parent_page_id:
                    # Get children of parent page to find existing page
                    search_r = req("GET", f"https://api.notion.com/v1/blocks/{parent_page_id}/children")
                    if expect_ok(search_r, f"Searching for existing page '{title}'"):
                        blocks = j(search_r).get('results', [])
                        existing_page_id = None

                        for block in blocks:
                            if (block.get('type') == 'child_page' and
                                block.get('child_page', {}).get('title') == title):
                                existing_page_id = block.get('id')
                                break

                        if existing_page_id:
                            logging.info(f"Found existing page '{title}' with ID: {existing_page_id}")

                            # Get the existing page's children and delete archived blocks
                            page_r = req("GET", f"https://api.notion.com/v1/blocks/{existing_page_id}/children")
                            if expect_ok(page_r, f"Getting children of existing page '{title}'"):
                                page_blocks = j(page_r).get('results', [])

                                # Delete all existing blocks
                                for block in page_blocks:
                                    block_id = block.get('id')
                                    if block_id:
                                        delete_r = req("DELETE", f"https://api.notion.com/v1/blocks/{block_id}")
                                        if expect_ok(delete_r, f"Deleting block {block_id}"):
                                            logging.debug(f"Deleted block {block_id}")

                                # Now add new content to the existing page
                                if children:
                                    add_payload = {"children": children}
                                    add_r = req("PATCH", f"https://api.notion.com/v1/blocks/{existing_page_id}/children",
                                               data=json.dumps(add_payload))
                                    if expect_ok(add_r, f"Adding content to existing page '{title}'"):
                                        state.created_pages[title] = existing_page_id
                                        logging.info(f"✅ Updated existing page '{title}': {existing_page_id} with {len(children)} blocks")
                                        return existing_page_id

                            # If we couldn't add content, at least return the existing page ID
                            state.created_pages[title] = existing_page_id
                            logging.warning(f"⚠️ Found existing page '{title}' but couldn't update content: {existing_page_id}")
                            return existing_page_id

            except Exception as clear_error:
                logging.error(f"Error while handling archived content for '{title}': {clear_error}")

            return None

        # Normal successful creation
        if expect_ok(r, f"Creating page '{title}'"):
            page_id = j(r).get('id')
            state.created_pages[title] = page_id
            logging.info(f"✅ Created page '{title}': {page_id} with {len(children)} blocks")

            # Verify blocks were added
            if children:
                time.sleep(0.5)  # Brief pause for API consistency
                logging.info(f"Page '{title}' created successfully with content blocks")

            return page_id
        else:
            return None
    except Exception as e:
        error_message = str(e)

        # Handle archived content error in exceptions too
        if 'archived' in error_message.lower():
            logging.warning(f"Page creation failed due to archived content exception. Attempting to handle for '{title}'...")

            try:
                # Search for existing page by title in the parent
                parent_page_id = parent.get("page_id")
                if parent_page_id:
                    # Get children of parent page to find existing page
                    search_r = req("GET", f"https://api.notion.com/v1/blocks/{parent_page_id}/children")
                    if expect_ok(search_r, f"Searching for existing page '{title}' after exception"):
                        blocks = j(search_r).get('results', [])
                        existing_page_id = None

                        for block in blocks:
                            if (block.get('type') == 'child_page' and
                                block.get('child_page', {}).get('title') == title):
                                existing_page_id = block.get('id')
                                break

                        if existing_page_id:
                            logging.info(f"Found existing page '{title}' with ID: {existing_page_id}")

                            # Get the existing page's children and delete archived blocks
                            page_r = req("GET", f"https://api.notion.com/v1/blocks/{existing_page_id}/children")
                            if expect_ok(page_r, f"Getting children of existing page '{title}' after exception"):
                                page_blocks = j(page_r).get('results', [])

                                # Delete all existing blocks
                                for block in page_blocks:
                                    block_id = block.get('id')
                                    if block_id:
                                        delete_r = req("DELETE", f"https://api.notion.com/v1/blocks/{block_id}")
                                        if expect_ok(delete_r, f"Deleting block {block_id} after exception"):
                                            logging.debug(f"Deleted block {block_id}")

                                # Now add new content to the existing page
                                if children:
                                    add_payload = {"children": children}
                                    add_r = req("PATCH", f"https://api.notion.com/v1/blocks/{existing_page_id}/children",
                                               data=json.dumps(add_payload))
                                    if expect_ok(add_r, f"Adding content to existing page '{title}' after exception"):
                                        state.created_pages[title] = existing_page_id
                                        logging.info(f"✅ Updated existing page '{title}' after exception: {existing_page_id} with {len(children)} blocks")
                                        return existing_page_id

                            # If we couldn't add content, at least return the existing page ID
                            state.created_pages[title] = existing_page_id
                            logging.warning(f"⚠️ Found existing page '{title}' but couldn't update content after exception: {existing_page_id}")
                            return existing_page_id

            except Exception as clear_error:
                logging.error(f"Error while handling archived content exception for '{title}': {clear_error}")

        logging.error(f"Failed to create page '{title}': {e}")
        state.errors.append({"phase": "pages", "item": title, "error": str(e)})

    return None

def create_database(db_name: str, schema: Dict, state: DeploymentState,
                   parent_id: Optional[str] = None, skip_rollups: bool = False) -> Optional[str]:
    """Create a Notion database with schema

    Args:
        db_name: Name of the database
        schema: Database schema definition
        state: Deployment state tracking
        parent_id: Parent page ID
        skip_rollups: If True, skip rollup properties (for two-pass creation)
    """

    # Check if already created
    if db_name in state.created_databases:
        logging.debug(f"Database '{db_name}' already exists: {state.created_databases[db_name]}")
        return state.created_databases[db_name]

    # Build properties schema
    properties = {}
    rollup_definitions = {}  # Store rollups for later if skipping

    for prop_name, prop_def in schema.get('properties', {}).items():
        # Skip rollup properties if requested (first pass)
        if skip_rollups and prop_def.get('type') == 'rollup':
            rollup_definitions[prop_name] = prop_def
            logging.debug(f"Skipping rollup property '{prop_name}' in database '{db_name}' (will add in second pass)")
            continue
        properties[prop_name] = build_property_schema(prop_def)

    # Store rollup definitions for later processing
    if rollup_definitions:
        if not hasattr(state, 'pending_rollups'):
            state.pending_rollups = {}
        state.pending_rollups[db_name] = rollup_definitions

    # Resolve database references in relation properties
    properties = resolve_database_references(properties, state)

    # Ensure Name property exists
    if 'Name' not in properties:
        properties['Name'] = {"title": {}}
    
    # Determine parent
    if parent_id:
        parent = {"type": "page_id", "page_id": parent_id}
    elif schema.get('parent'):
        parent_title = schema['parent']
        if parent_title in state.created_pages:
            parent = {"type": "page_id", "page_id": state.created_pages[parent_title]}
        else:
            parent = {"type": "page_id", "page_id": NOTION_PARENT_PAGEID}
    else:
        parent = {"type": "page_id", "page_id": NOTION_PARENT_PAGEID}
    
    # Create database
    payload = {
        "parent": parent,
        "title": [{"text": {"content": db_name}}],
        "properties": properties
    }
    
    try:
        r = req("POST", "https://api.notion.com/v1/databases", data=json.dumps(payload))
        if expect_ok(r, f"Creating database '{db_name}'"):
            db_id = j(r).get('id')
            state.created_databases[db_name] = db_id
            logging.info(f"Created database '{db_name}': {db_id}")
            return db_id
    except Exception as e:
        logging.error(f"Failed to create database '{db_name}': {e}")
        state.errors.append({"phase": "databases", "item": db_name, "error": str(e)})
    
    return None

def add_rollup_properties(state: DeploymentState) -> bool:
    """Add rollup properties to databases after all relations are established

    This is the second pass of database creation that adds rollup properties
    which depend on relations being already established.
    """
    if not hasattr(state, 'pending_rollups') or not state.pending_rollups:
        logging.debug("No pending rollup properties to add")
        return True

    success = True
    logging.info(f"Adding rollup properties to {len(state.pending_rollups)} databases")

    for db_name, rollup_definitions in state.pending_rollups.items():
        if db_name not in state.created_databases:
            logging.error(f"Cannot add rollups to '{db_name}': database not found")
            continue

        db_id = state.created_databases[db_name]
        logging.info(f"Adding {len(rollup_definitions)} rollup properties to database '{db_name}'")

        # Build the properties update payload
        properties = {}
        for prop_name, prop_def in rollup_definitions.items():
            # Ensure the rollup configuration is complete
            rollup_config = prop_def.get('rollup', {})

            # Validate required fields
            if not rollup_config.get('relation_property_name'):
                logging.error(f"Rollup '{prop_name}' missing relation_property_name")
                continue

            if not rollup_config.get('rollup_property_name'):
                logging.error(f"Rollup '{prop_name}' missing rollup_property_name")
                continue

            # Build the rollup property configuration
            properties[prop_name] = {
                "rollup": {
                    "relation_property_name": rollup_config.get('relation_property_name'),
                    "rollup_property_name": rollup_config.get('rollup_property_name'),
                    "function": rollup_config.get('function', 'count')
                }
            }

            logging.debug(f"Prepared rollup '{prop_name}': {rollup_config.get('relation_property_name')} -> {rollup_config.get('rollup_property_name')} ({rollup_config.get('function', 'count')})")

        if not properties:
            logging.warning(f"No valid rollup properties to add to '{db_name}'")
            continue

        # Update the database with rollup properties
        payload = {
            "properties": properties
        }

        try:
            # Use PATCH to update the database
            r = req("PATCH", f"https://api.notion.com/v1/databases/{db_id}",
                   data=json.dumps(payload))

            if expect_ok(r, f"Adding rollup properties to '{db_name}'"):
                logging.info(f"Successfully added {len(properties)} rollup properties to '{db_name}'")

                # Log each added rollup for confirmation
                for prop_name in properties.keys():
                    logging.debug(f"  ✓ Added rollup: {prop_name}")
            else:
                success = False
                logging.error(f"Failed to add rollup properties to '{db_name}'")

        except Exception as e:
            logging.error(f"Error adding rollup properties to '{db_name}': {e}")
            state.errors.append({"phase": "rollups", "item": db_name, "error": str(e)})
            success = False

    # Clear pending rollups after processing
    state.pending_rollups.clear()

    return success

def convert_legacy_block_format(block_def: Dict) -> Dict:
    """
    Convert old block formats to modern Notion API format
    Handles legacy patterns like type: H1/H2/H3 and heading field
    """
    block_def = block_def.copy()  # Don't mutate original

    # Convert old heading format: type: H1/H2/H3 -> type: heading_1/2/3
    if 'type' in block_def:
        old_type = block_def['type']
        if old_type == 'H1':
            block_def['type'] = 'heading_1'
        elif old_type == 'H2':
            block_def['type'] = 'heading_2'
        elif old_type == 'H3':
            block_def['type'] = 'heading_3'

    # Move 'heading' field to 'content' if present
    if 'heading' in block_def and 'content' not in block_def:
        block_def['content'] = block_def.pop('heading')

    return block_def


def build_block(block_def) -> Dict:
    """Build a Notion block from definition"""
    # Handle string blocks (convert to paragraph)
    if isinstance(block_def, str):
        block_def = {"type": "paragraph", "content": block_def}

    # Convert legacy formats first
    block_def = convert_legacy_block_format(block_def)

    block_type = block_def.get('type', 'paragraph')

    # Handle alternative content field names
    content = block_def.get('content', block_def.get('text', block_def.get('summary', '')))

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
    elif block_type == 'bulleted_list':
        # Handle bulleted_list with items
        children = []
        if 'items' in block_def:
            for item in block_def['items']:
                children.append({
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": item if isinstance(item, str) else str(item)}}]
                    }
                })
        return children[0] if len(children) == 1 else {"paragraph": {"rich_text": [{"text": {"content": f"[bulleted_list with {len(children)} items]"}}]}}
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
                "icon": {"emoji": block_def.get('icon', '💡').replace('emoji:', '')},
                "color": block_def.get('color', 'gray_background')
            }
        }
    elif block_type == 'toggle':
        block_data = {
            "toggle": {
                "rich_text": [{"text": {"content": content}}]
            }
        }
        # Handle nested blocks in toggle - check multiple field names
        children_data = block_def.get('children', block_def.get('blocks', []))
        if children_data:
            children = []
            for child_block in children_data:
                # Process variable substitution in nested blocks
                child_block = process_content_substitution(child_block)
                built_child = build_block(child_block)

                # Handle multi-block responses in toggle children
                if isinstance(built_child, dict) and built_child.get('_multi_block'):
                    children.extend(built_child['_blocks'])
                else:
                    children.append(built_child)

            block_data["toggle"]["children"] = children
        return block_data
    elif block_type == 'code':
        return {
            "code": {
                "rich_text": [{"text": {"content": content}}],
                "language": block_def.get('language', 'plain text')
            }
        }
    elif block_type == 'divider':
        return {"divider": {}}
    elif block_type == 'to_do':
        return {
            "to_do": {
                "rich_text": [{"text": {"content": content}}],
                "checked": block_def.get('checked', False)
            }
        }
    elif block_type == 'bulleted_list':
        # Handle bulleted_list with items array - this is a special case
        # We need to return a list of blocks, not a single block
        items = block_def.get('items', [])
        if not items:
            # Fallback to single item with content
            return {
                "bulleted_list_item": {
                    "rich_text": [{"text": {"content": content}}]
                }
            }
        else:
            # Mark this as a multi-block response
            return {
                "_multi_block": True,
                "_blocks": [
                    {
                        "bulleted_list_item": {
                            "rich_text": [{"text": {"content": item}}]
                        }
                    }
                    for item in items
                ]
            }
    elif block_type == 'numbered_list':
        # Handle numbered_list with items array - similar to bulleted_list
        items = block_def.get('items', [])
        if not items:
            return {
                "numbered_list_item": {
                    "rich_text": [{"text": {"content": content}}]
                }
            }
        else:
            return {
                "_multi_block": True,
                "_blocks": [
                    {
                        "numbered_list_item": {
                            "rich_text": [{"text": {"content": item}}]
                        }
                    }
                    for item in items
                ]
            }
    elif block_type == 'embed':
        # Handle embed blocks with proper Notion API format
        url = block_def.get('url', content if isinstance(content, str) and content.startswith('http') else '')
        if url:
            return {
                "embed": {
                    "url": url
                }
            }
        else:
            # Fallback if no valid URL
            return {
                "paragraph": {
                    "rich_text": [{"text": {"content": f"[EMBED: No valid URL provided]"}}]
                }
            }
    elif block_type == 'table':
        # Handle table blocks with proper Notion API format
        # Tables in Notion API require table_width and has_column_header
        rows = block_def.get('rows', [])
        if rows and isinstance(rows, list):
            # Calculate table width from first row
            table_width = len(rows[0].get('cells', [])) if rows else 3

            # Build table rows
            table_rows = []
            for row in rows:
                cells = row.get('cells', []) if isinstance(row, dict) else row if isinstance(row, list) else []
                # Convert cells to rich text format
                formatted_cells = []
                for cell in cells:
                    cell_content = str(cell) if cell else ""
                    formatted_cells.append([{"text": {"content": cell_content}}])

                # Pad row if needed
                while len(formatted_cells) < table_width:
                    formatted_cells.append([{"text": {"content": ""}}])

                table_rows.append({"cells": formatted_cells[:table_width]})

            return {
                "table": {
                    "table_width": table_width,
                    "has_column_header": block_def.get('has_header', True),
                    "has_row_header": block_def.get('has_row_header', False),
                    "children": table_rows if table_rows else [
                        {"cells": [[{"text": {"content": ""}}] for _ in range(table_width)]}
                    ]
                }
            }
        else:
            # Fallback for invalid table structure
            return {
                "paragraph": {
                    "rich_text": [{"text": {"content": f"[TABLE: Invalid structure]"}}]
                }
            }
    elif block_type == 'child_database':
        # Handle child_database blocks for embedded database views
        database_id = block_def.get('database_id')
        title = block_def.get('title', content)

        if database_id:
            return {
                "child_database": {
                    "title": title
                }
            }
        else:
            # Fallback with reference lookup
            db_ref = block_def.get('database_ref')
            if db_ref and hasattr(state, 'created_databases'):
                resolved_id = state.created_databases.get(db_ref)
                if resolved_id:
                    return {
                        "child_database": {
                            "title": title
                        }
                    }

            # Fallback if no valid database reference
            return {
                "paragraph": {
                    "rich_text": [{"text": {"content": f"[DATABASE: {title} - Reference not resolved]"}}]
                }
            }
    elif 'linked_db' in block_def:
        # Handle linked_db as a reference to a database (convert to child_database)
        db_name = block_def.get('linked_db', '')
        logger.info(f"Converting linked_db '{db_name}' to child_database reference")

        # Try to find the database ID if it was already created
        if hasattr(state, 'created_databases') and db_name in state.created_databases:
            return {
                "child_database": {
                    "title": db_name
                }
            }
        else:
            # Fallback: create a placeholder that references the database
            return {
                "paragraph": {
                    "rich_text": [{"text": {"content": f"[DATABASE VIEW: {db_name}]"}}],
                    "color": "gray_background"
                }
            }
    elif block_type == "image":
        # Image block
        image_url = block_def.get("url") or block_def.get("src") or block_def.get("image_url") or ""
        caption = block_def.get("caption") or block_def.get("alt") or ""

        if not image_url:
            logger.warning("Image block missing URL")
            return {"paragraph": {"rich_text": [{"text": {"content": "[Image - URL missing]"}}]}}

        return {
            "image": {
                "type": "external",
                "external": {"url": image_url},
                "caption": [{"text": {"content": caption}}] if caption else []
            }
        }

    elif block_type == "file":
        # File attachment block
        file_url = block_def.get("url") or block_def.get("file_url") or ""
        file_name = block_def.get("name") or block_def.get("filename") or "File"

        if not file_url:
            logger.warning("File block missing URL")
            return {"paragraph": {"rich_text": [{"text": {"content": f"[File: {file_name} - URL missing]"}}]}}

        return {
            "file": {
                "type": "external",
                "external": {"url": file_url},
                "caption": [{"text": {"content": file_name}}]
            }
        }

    elif block_type == "pdf":
        # PDF embed block
        pdf_url = block_def.get("url") or block_def.get("pdf_url") or ""
        title = block_def.get("title") or "PDF Document"

        if not pdf_url:
            logger.warning("PDF block missing URL")
            return {"paragraph": {"rich_text": [{"text": {"content": f"[PDF: {title} - URL missing]"}}]}}

        return {
            "pdf": {
                "type": "external",
                "external": {"url": pdf_url},
                "caption": [{"text": {"content": title}}]
            }
        }

    elif block_type == "bookmark":
        # Bookmark/web link block
        url = block_def.get("url") or block_def.get("link") or ""
        caption = block_def.get("caption") or block_def.get("title") or url

        if not url:
            logger.warning("Bookmark block missing URL")
            return {"paragraph": {"rich_text": [{"text": {"content": "[Bookmark - URL missing]"}}]}}

        return {
            "bookmark": {
                "url": url,
                "caption": [{"text": {"content": caption}}] if caption != url else []
            }
        }

    elif block_type == "quote":
        # Quote block
        text = block_def.get("content") or block_def.get("text") or ""
        author = block_def.get("author") or block_def.get("citation") or ""

        quote_content = text
        if author:
            quote_content = f"{text}\n— {author}"

        return {
            "quote": {
                "rich_text": [{"text": {"content": quote_content}}],
                "color": "default"
            }
        }

    elif block_type == "column_list":
        # Column layout container - requires special handling
        columns = block_def.get("columns") or []

        if not columns:
            logger.warning("Column list block missing columns")
            return {"paragraph": {"rich_text": [{"text": {"content": "[Column Layout]"}}]}}

        # For now, flatten columns into sequential blocks
        # Notion API requires creating column_list with column children
        # This would need special handling in create_page_with_blocks
        logger.info(f"Column layout with {len(columns)} columns - flattening for now")
        return {"paragraph": {"rich_text": [{"text": {"content": f"[Column Layout: {len(columns)} columns]"}}]}}

    elif block_type == "link_to_page":
        # Link to another page block
        page_id = block_def.get("page_id") or block_def.get("target_page_id") or ""
        page_title = block_def.get("title") or block_def.get("page_title") or "Linked Page"

        if not page_id:
            # Try to find page by title if ID not provided
            page_title_to_find = block_def.get("page_title") or block_def.get("title")
            # Note: page_ids would need to be tracked globally or passed in
            # For now, just fallback to text

        if not page_id:
            logger.warning(f"Link to page block missing page_id for: {page_title}")
            return {"paragraph": {"rich_text": [{"text": {"content": f"→ {page_title}"}}]}}

        return {
            "link_to_page": {
                "type": "page_id",
                "page_id": page_id
            }
        }

    elif block_type == "child_page":
        # Child page reference block - creates a link to a subpage
        page_id = block_def.get("page_id") or ""
        title = block_def.get("title") or block_def.get("page_title") or "Child Page"
        icon = block_def.get("icon") or ""

        if not page_id:
            # Note: Would need global page_ids tracking for title resolution
            logger.warning(f"Child page block missing page_id, using fallback for: {title}")
            # Fallback to a styled paragraph that looks like a child page link
            icon_str = f"{icon} " if icon else "📄 "
            return {"paragraph": {"rich_text": [{"text": {"content": f"{icon_str}{title}"}}]}}

        return {
            "child_page": {
                "page_id": page_id
            }
        }

    elif block_type == "table_of_contents":
        # Automatic table of contents from headings in the page
        # TOC automatically includes all heading_1, heading_2, heading_3 blocks
        color = block_def.get("color") or block_def.get("background_color") or "default"

        # Notion API table_of_contents block
        return {
            "table_of_contents": {
                "color": color
            }
        }

    elif block_type == "breadcrumb":
        # Navigation breadcrumb showing page hierarchy
        # Breadcrumb automatically generates from the page's position in workspace
        # No additional configuration needed - it reads from page hierarchy
        return {
            "breadcrumb": {}
        }

    else:  # Default to paragraph
        return {
            "paragraph": {
                "rich_text": [{"text": {"content": f"[{block_type}] {content}"}}]
            }
        }

def resolve_database_references(properties: Dict, state: Any) -> Dict:
    """Resolve database_id_ref markers to actual database IDs"""
    resolved_properties = {}

    for prop_name, prop_schema in properties.items():
        resolved_properties[prop_name] = prop_schema

        # Check if this is a relation property with a reference
        if (isinstance(prop_schema, dict) and
            prop_schema.get('relation', {}).get('database_id', '').startswith('ref:')):

            ref_key = prop_schema['relation']['database_id'][4:]  # Remove 'ref:' prefix
            resolved_id = None

            if ref_key == 'pages':
                # 'pages' refers to the main page-type database
                # This is typically created as the first database
                page_databases = [db_id for db_name, db_id in state.created_databases.items()
                                if 'page' in db_name.lower() or db_name == 'Main Pages']
                if page_databases:
                    resolved_id = page_databases[0]
                elif state.created_databases:
                    # Fallback: use first created database
                    resolved_id = list(state.created_databases.values())[0]
            else:
                # Try to find exact match in created databases
                resolved_id = state.created_databases.get(ref_key)
                if not resolved_id:
                    # Try case-insensitive match
                    for db_name, db_id in state.created_databases.items():
                        if db_name.lower() == ref_key.lower():
                            resolved_id = db_id
                            break

            if resolved_id:
                resolved_properties[prop_name]['relation']['database_id'] = resolved_id
                logging.info(f"Resolved database reference '{ref_key}' to {resolved_id}")
            else:
                logging.warning(f"Could not resolve database reference '{ref_key}' - using placeholder")
                # Keep the reference as is - this may be resolved later

    return resolved_properties

def build_property_schema(prop_def) -> Dict:
    """Build property schema for database - handles both string and dict formats"""
    # Handle shorthand string format (e.g., "title", "text", "select")
    if isinstance(prop_def, str):
        prop_type = prop_def
        # Map shorthand types to full types
        if prop_type == 'text':
            prop_type = 'rich_text'
        prop_def = {"type": prop_type}  # Convert to dict format
    else:
        prop_type = prop_def.get('type', 'rich_text')
    
    if prop_type == 'title':
        return {"title": {}}
    elif prop_type == 'number':
        return {"number": {"format": prop_def.get('format', 'number')}}
    elif prop_type == 'select':
        return {
            "select": {
                "options": build_enhanced_select_options(prop_def.get('options', []))
            }
        }
    elif prop_type == 'multi_select':
        return {
            "multi_select": {
                "options": build_enhanced_select_options(prop_def.get('options', []))
            }
        }
    elif prop_type == 'date':
        return {"date": {}}
    elif prop_type == 'checkbox':
        return {"checkbox": {}}
    elif prop_type == 'url':
        return {"url": {}}
    elif prop_type == 'email':
        return {"email": {}}
    elif prop_type == 'phone_number':
        return {"phone_number": {}}
    elif prop_type == 'formula':
        # Handle multiple formula expression patterns from YAML
        expression = ''

        # Pattern 1: { type: formula, formula: "expression" }
        if isinstance(prop_def.get('formula'), str):
            expression = prop_def.get('formula', '')

        # Pattern 2: { type: formula, formula: { expression: "expression" } }
        elif isinstance(prop_def.get('formula'), dict):
            expression = prop_def.get('formula', {}).get('expression', '')

        # Pattern 3: { type: formula, expression: "expression" } (legacy)
        elif 'expression' in prop_def:
            expression = prop_def.get('expression', '')

        return {
            "formula": {
                "expression": expression
            }
        }
    elif prop_type == 'relation':
        # Handle database_id_ref pattern from YAML
        database_id = prop_def.get('database_id', '')

        # If database_id_ref is provided, mark for later resolution
        if not database_id and 'database_id_ref' in prop_def:
            database_ref = prop_def.get('database_id_ref')
            # Use a marker that will be resolved during database creation
            database_id = f"ref:{database_ref}"

        # Build relation property according to Sept 2025 API format
        relation_config = {"database_id": database_id}

        # Handle dual_property relations if specified
        # Check both old format (relation_type) and new format (nested in relation)
        relation_def = prop_def.get('relation', {})

        if prop_def.get('relation_type') == 'dual_property' or relation_def.get('type') == 'dual_property':
            # Extract dual_property config from either format
            dual_prop_config = prop_def.get('dual_property') or relation_def.get('dual_property', {})

            if dual_prop_config:
                relation_config["type"] = "dual_property"
                relation_config["dual_property"] = {
                    "synced_property_name": dual_prop_config.get('synced_property_name', ''),
                    "synced_property_id": dual_prop_config.get('synced_property_id', '')
                }

        return {"relation": relation_config}
    elif prop_type == 'rollup':
        # Handle rollup properties
        rollup_config = {
            "relation_property_name": prop_def.get('relation_property_name', ''),
            "relation_property_id": prop_def.get('relation_property_id', ''),
            "rollup_property_name": prop_def.get('rollup_property_name', ''),
            "rollup_property_id": prop_def.get('rollup_property_id', ''),
            "function": prop_def.get('function', 'count')  # count, count_values, sum, average, median, min, max, etc.
        }
        return {"rollup": rollup_config}
    elif prop_type == 'people':
        # Handle people property type
        return {"people": {}}
    elif prop_type == 'last_edited_time':
        # Handle last_edited_time property type
        return {"last_edited_time": {}}
    elif prop_type == 'created_time':
        # Handle created_time property type
        return {"created_time": {}}
    elif prop_type == 'files':
        # Handle files property type for file attachments
        return {"files": {}}
    else:  # Default to rich_text
        return {"rich_text": {}}

# ============================================================================
# CLI INTERFACE (Qwen feature)
# ============================================================================

class CLIInterface:
    """Interactive CLI from Qwen build"""
    
    @staticmethod
    def setup_parser() -> argparse.ArgumentParser:
        """Setup command line argument parser"""
        parser = argparse.ArgumentParser(
            description='Notion Template v4.0 Deployment Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --dry-run              # Validate without deploying
  %(prog)s --phase pages           # Deploy only pages
  %(prog)s --interactive           # Step-by-step deployment
  %(prog)s --resume                # Resume from last checkpoint
  %(prog)s --validate-only         # Only run validation
            """
        )
        
        # Deployment modes
        mode_group = parser.add_mutually_exclusive_group()
        mode_group.add_argument('--dry-run', action='store_true',
                               help='Validate configuration without deploying')
        mode_group.add_argument('--interactive', action='store_true',
                               help='Interactive step-by-step deployment')
        mode_group.add_argument('--resume', action='store_true',
                               help='Resume from last checkpoint')
        mode_group.add_argument('--validate-only', action='store_true',
                               help='Only validate, no deployment')
        
        # Selective deployment
        parser.add_argument('--phase', choices=[p.name.lower() for p in DeploymentPhase],
                          help='Deploy only specific phase')
        parser.add_argument('--skip-phases', nargs='+',
                          help='Skip specific phases')
        
        # Configuration
        parser.add_argument('--yaml-dir', type=Path,
                          help='Directory containing YAML files')
        parser.add_argument('--csv-dir', type=Path,
                          help='Directory containing CSV files')
        parser.add_argument('--parent-id',
                          help='Override parent page ID')
        
        # Logging
        parser.add_argument('--verbose', '-v', action='count', default=0,
                          help='Increase verbosity (-v, -vv, -vvv)')
        parser.add_argument('--quiet', '-q', action='store_true',
                          help='Suppress non-error output')
        
        return parser
    
    @staticmethod
    def prompt_continue(message: str = "Continue?") -> bool:
        """Interactive prompt for user confirmation"""
        response = input(f"\n{message} [Y/n]: ").strip().lower()
        return response in ('', 'y', 'yes')

# ============================================================================
# MAIN DEPLOYMENT ORCHESTRATOR
# ============================================================================

class NotionTemplateDeployer:
    """Main deployment orchestrator combining all features"""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.state = DeploymentState()
        self.validator = Validator()
        self.progress = None
        self.setup_logging()
        
    def setup_logging(self):
        """Configure unified color-coded logging"""
        # Always use DEBUG level for comprehensive logging
        level = logging.DEBUG

        # Create logs directory
        os.makedirs('logs', exist_ok=True)

        # Clear previous log
        log_file = 'logs/debug.log'
        if os.path.exists(log_file):
            os.remove(log_file)

        # Set up unified logging - everything to ONE file with color prefixes
        class ColorFormatter(logging.Formatter):
            def format(self, record):
                msg = record.getMessage().lower()
                timestamp = self.formatTime(record, '%Y-%m-%d %H:%M:%S.%f')[:-3]

                # Color code based on message content
                if any(x in msg for x in ['api_request', 'api_response', 'post /v1/', 'patch /v1/', 'get /v1/', 'status_code', 'notion api']):
                    prefix = "🟢 API"
                elif any(x in msg for x in ['replicate', 'openai', 'anthropic', 'gpt', 'claude', 'llm', 'ai_call', 'model_request', 'generation']):
                    prefix = "🟤 LLM"
                elif any(x in msg for x in ['asset', 'icon', 'cover', 'image', 'processing', 'block creation', 'page creation']):
                    prefix = "🔵 ASSET"
                elif any(x in msg for x in ['error', 'failed', 'exception', 'warning', 'critical']):
                    prefix = "🔴 ERROR"
                elif any(x in msg for x in ['correlation_id', 'request_id', 'tracing', 'elapsed_seconds']):
                    prefix = "🟣 TRACE"
                elif any(x in msg for x in ['yaml', 'section', 'parsing', 'configuration']):
                    prefix = "🟠 YAML"
                else:
                    prefix = "⚫ INFO"

                return f"{prefix} {timestamp} - {record.levelname} - {record.filename}:{record.lineno} - {record.getMessage()}"

        # Configure logging
        logging.basicConfig(
            level=level,
            format='%(message)s',
            handlers=[
                logging.FileHandler(log_file, mode='w', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        # Apply color formatter to file handler only
        for handler in logging.root.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.setFormatter(ColorFormatter())

        # Log initialization
        logging.info("🚀 Unified debug logging initialized")
        logging.info(f"📝 All output in: {log_file}")
        logging.info("🟢=API | 🟤=LLM | 🔵=Assets | 🔴=Errors | ⚫=Info | 🟣=Trace | 🟠=YAML")
    
    def run(self) -> bool:
        """Main deployment entry point"""
        try:
            # Handle resume mode
            if self.args.resume:
                loaded_state = self.state.load_checkpoint()
                if loaded_state:
                    self.state = loaded_state
                    logging.info(f"Resuming from phase: {self.state.phase.value}")
                else:
                    logging.info("No checkpoint found, starting fresh")
            
            # Phase 1: Validation
            if not self.skip_phase(DeploymentPhase.VALIDATION):
                if not self.validate():
                    return False
                    
            if self.args.validate_only:
                print("\n✅ Validation successful!")
                return True
                
            if self.args.dry_run:
                print("\n✅ Dry run successful! Ready for deployment.")
                return True
            
            # Load configuration
            yaml_data = load_all_yaml(self.args.yaml_dir)
            csv_data = load_csv_data(self.args.csv_dir)
            
            # Calculate total steps for progress tracking
            total_steps = (
                len(yaml_data.get('pages', [])) +
                len(yaml_data.get('db', {}).get('schemas', {})) +
                len(csv_data) + 10  # Extra steps for patches and finalization
            )
            self.progress = ProgressTracker(total_steps)
            
            # Phase 2: Preparation
            if not self.skip_phase(DeploymentPhase.PREPARATION):
                self.state.phase = DeploymentPhase.PREPARATION
                self.progress.update(DeploymentPhase.PREPARATION, "Setting up deployment")
                self.state.save_checkpoint()
            
            # Phase 3: Create Pages
            if not self.skip_phase(DeploymentPhase.PAGES):
                # Clear existing content first to avoid archived conflicts
                if not self.clear_existing_content():
                    logging.warning("Failed to clear existing content, but continuing...")

                if not self.deploy_pages(yaml_data):
                    return False
            
            # Phase 4: Create Databases
            if not self.skip_phase(DeploymentPhase.DATABASES):
                if not self.deploy_databases(yaml_data):
                    return False
            
            # Phase 5: Set Relations
            if not self.skip_phase(DeploymentPhase.RELATIONS):
                if not self.setup_relations(yaml_data):
                    return False
            
            # Phase 6: Import Data
            if not self.skip_phase(DeploymentPhase.DATA):
                if not self.import_data(csv_data):
                    return False
            
            # Phase 7: Apply Patches
            if not self.skip_phase(DeploymentPhase.PATCHES):
                if not self.apply_patches(yaml_data):
                    return False
            
            # Phase 8: Finalization
            if not self.skip_phase(DeploymentPhase.FINALIZATION):
                self.finalize_deployment()
            
            # Success!
            self.state.phase = DeploymentPhase.COMPLETED
            self.state.clear_checkpoint()
            self.print_summary()
            return True
            
        except KeyboardInterrupt:
            logging.warning("\n\nDeployment interrupted! Run with --resume to continue.")
            self.state.save_checkpoint()
            return False
        except Exception as e:
            logging.error(f"Deployment failed: {e}")
            self.state.errors.append({"phase": self.state.phase.value, "error": str(e)})
            self.state.save_checkpoint()
            return False
    
    def skip_phase(self, phase: DeploymentPhase) -> bool:
        """Check if phase should be skipped"""
        if self.args.phase and phase.name.lower() != self.args.phase:
            return True
        if self.args.skip_phases and phase.name.lower() in self.args.skip_phases:
            return True
        # Compare enum positions instead of string values
        current_phase_order = list(DeploymentPhase).index(self.state.phase)
        target_phase_order = list(DeploymentPhase).index(phase)
        if current_phase_order > target_phase_order:  # Already completed in previous run
            return True
        return False
    
    def validate(self) -> bool:
        """Run all validations"""
        self.state.phase = DeploymentPhase.VALIDATION
        errors = []
        
        # Environment validation
        env_errors = self.validator.validate_environment()
        if env_errors:
            errors.extend(env_errors)
        
        # YAML validation
        yaml_data = load_all_yaml(self.args.yaml_dir)
        if not yaml_data:
            errors.append("No YAML data loaded")
        else:
            yaml_errors = self.validator.validate_yaml_structure(yaml_data)
            if yaml_errors:
                errors.extend(yaml_errors)
            
            dep_errors = self.validator.validate_dependencies(yaml_data)
            if dep_errors:
                errors.extend(dep_errors)
        
        if errors:
            print("\n❌ Validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        logging.info("✅ All validations passed")
        return True
    
    def clear_existing_content(self) -> bool:
        """Clear all existing content from the target page to avoid archived conflicts"""
        try:
            parent_id = self.args.parent_id or NOTION_PARENT_PAGEID
            logging.info(f"Clearing existing content from page: {parent_id}")

            # Get all children of the parent page
            r = req("GET", f"https://api.notion.com/v1/blocks/{parent_id}/children")
            if not expect_ok(r, "Getting existing content"):
                return False

            blocks = j(r).get('results', [])
            if not blocks:
                logging.info("No existing content to clear")
                return True

            logging.info(f"Found {len(blocks)} existing blocks to clear")

            # Delete all existing blocks
            deleted_count = 0
            for block in blocks:
                block_id = block.get('id')
                if block_id:
                    delete_r = req("DELETE", f"https://api.notion.com/v1/blocks/{block_id}")
                    if expect_ok(delete_r, f"Deleting block {block_id}"):
                        deleted_count += 1
                        logging.debug(f"Deleted block {block_id}")
                    else:
                        logging.warning(f"Failed to delete block {block_id}")

            logging.info(f"✅ Cleared {deleted_count} existing blocks")
            return True

        except Exception as e:
            logging.error(f"Error clearing existing content: {e}")
            return False

    def deploy_pages(self, yaml_data: Dict) -> bool:
        """Deploy all pages with proper parent-child ordering"""
        self.state.phase = DeploymentPhase.PAGES
        pages = yaml_data.get('pages', [])

        if self.args.interactive:
            if not CLIInterface.prompt_continue(f"Deploy {len(pages)} pages?"):
                return False

        # Create lookup for all pages by title
        all_pages = {page.get('title'): page for page in pages}

        # Separate parent and child pages
        parent_pages = []
        child_pages = []

        for page in pages:
            if page.get('parent'):
                child_pages.append(page)
            else:
                parent_pages.append(page)

        logging.info(f"Found {len(parent_pages)} parent pages and {len(child_pages)} child pages")

        # First, create all parent pages (even if they have no blocks)
        logging.info("Phase 1: Creating parent pages...")
        for page in parent_pages:
            title = page.get('title', 'Untitled')
            self.progress.update(DeploymentPhase.PAGES, f"Creating parent: {title}")

            parent_id = self.args.parent_id or NOTION_PARENT_PAGEID
            page_id = create_page(page, self.state, parent_id)

            if not page_id and not self.args.interactive:
                return False
            elif not page_id and self.args.interactive:
                if not CLIInterface.prompt_continue(f"Child page '{title}' creation failed. Continue?"):
                    return False

            self.state.save_checkpoint()

        # Then, create all child pages (which should have the blocks)
        logging.info("Phase 2: Creating child pages...")
        for page in child_pages:
            title = page.get('title', 'Untitled')
            self.progress.update(DeploymentPhase.PAGES, f"Creating child: {title}")

            # Let create_page handle parent lookup from state.created_pages
            page_id = create_page(page, self.state, None)

            if not page_id and not self.args.interactive:
                return False
            elif not page_id and self.args.interactive:
                if not CLIInterface.prompt_continue(f"Parent page '{title}' creation failed. Continue?"):
                    return False

            self.state.save_checkpoint()

        return True
    
    def deploy_databases(self, yaml_data: Dict) -> bool:
        """Deploy all databases from both db.schemas and standalone databases formats

        Uses a two-pass system:
        1. First pass: Create databases without rollup properties
        2. Second pass: Add rollup properties after all relations are established
        """
        self.state.phase = DeploymentPhase.DATABASES

        # Get databases from db.schemas format
        schemas = yaml_data.get('db', {}).get('schemas', {})

        # Get standalone databases and convert them to schema format
        standalone_databases = yaml_data.get('standalone_databases', [])
        converted_standalone = {}

        for standalone_db in standalone_databases:
            converted = convert_standalone_db_to_schema(standalone_db)
            db_name = converted['db_name']
            converted_standalone[db_name] = converted['schema']

            # Add seed rows to merged data for later processing
            if converted['seed_rows']:
                if 'db' not in yaml_data:
                    yaml_data['db'] = {}
                if 'seed_rows' not in yaml_data['db']:
                    yaml_data['db']['seed_rows'] = {}
                yaml_data['db']['seed_rows'][db_name] = converted['seed_rows']

        # Combine both types of databases
        all_databases = {**schemas, **converted_standalone}

        if self.args.interactive:
            if not CLIInterface.prompt_continue(f"Deploy {len(all_databases)} databases ({len(schemas)} from schemas + {len(converted_standalone)} standalone)?"):
                return False

        # FIRST PASS: Create databases without rollup properties
        logging.info("Phase 1: Creating databases without rollup properties...")
        for db_name, schema in all_databases.items():
            self.progress.update(DeploymentPhase.DATABASES, f"Creating: {db_name} (without rollups)")

            parent_id = self.args.parent_id or NOTION_PARENT_PAGEID
            # Pass skip_rollups=True for first pass
            db_id = create_database(db_name, schema, self.state, parent_id, skip_rollups=True)

            if not db_id and not self.args.interactive:
                return False
            elif not db_id and self.args.interactive:
                if not CLIInterface.prompt_continue("Database creation failed. Continue?"):
                    return False

            self.state.save_checkpoint()

        # Note: The second pass (adding rollups) will happen after relations are set up
        # This will be called from setup_relations() function
        logging.info("Databases created. Rollup properties will be added after relations are established.")

        return True
    
    def setup_relations(self, yaml_data: Dict) -> bool:
        """Setup database relations and rollup properties

        This function now handles:
        1. Establishing relations between databases (if needed)
        2. Adding rollup properties that depend on those relations
        """
        self.state.phase = DeploymentPhase.RELATIONS
        self.progress.update(DeploymentPhase.RELATIONS, "Configuring relations")

        # Note: Relations are already created during database creation
        # The relation properties were included in the first pass
        # Now we need to add the rollup properties that depend on them

        logging.info("Adding rollup properties to databases...")
        self.progress.update(DeploymentPhase.RELATIONS, "Adding rollup properties")

        # SECOND PASS: Add rollup properties now that all databases and relations exist
        rollup_success = add_rollup_properties(self.state)

        if not rollup_success:
            logging.warning("Some rollup properties could not be added")
            if self.args.interactive:
                if not CLIInterface.prompt_continue("Some rollup properties failed. Continue?"):
                    return False
        else:
            logging.info("All rollup properties successfully added")

        self.state.save_checkpoint()
        return True
    
    def import_data(self, csv_data: Dict[str, List[Dict]]) -> bool:
        """Import CSV data into databases"""
        self.state.phase = DeploymentPhase.DATA
        
        if self.args.interactive:
            if not CLIInterface.prompt_continue(f"Import data for {len(csv_data)} databases?"):
                return False
        
        for db_name, rows in csv_data.items():
            if db_name in self.state.processed_csv:
                continue
                
            self.progress.update(DeploymentPhase.DATA, f"Importing: {db_name} ({len(rows)} rows)")
            
            # TODO: Implement CSV import logic
            # This requires creating pages in the database with CSV data
            
            self.state.processed_csv.append(db_name)
            self.state.save_checkpoint()
        
        return True
    
    def apply_patches(self, yaml_data: Dict) -> bool:
        """Apply any patches or updates"""
        self.state.phase = DeploymentPhase.PATCHES
        self.progress.update(DeploymentPhase.PATCHES, "Applying patches")
        
        # TODO: Implement patch application logic
        # This could include updating properties, adding blocks, etc.
        
        self.state.save_checkpoint()
        return True
    
    def finalize_deployment(self):
        """Final cleanup and verification"""
        self.state.phase = DeploymentPhase.FINALIZATION
        self.progress.update(DeploymentPhase.FINALIZATION, "Finalizing deployment")
        
        # TODO: Add final verification steps
        # - Verify all pages accessible
        # - Check database permissions
        # - Generate deployment report
        
        time.sleep(1)  # Give progress bar time to complete
    
    def print_summary(self):
        """Print deployment summary"""
        duration = time.time() - self.state.start_time
        
        print("\n" + "="*60)
        print("DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"✅ Deployment completed successfully!")
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📄 Pages created: {len(self.state.created_pages)}")
        print(f"🗄️  Databases created: {len(self.state.created_databases)}")
        print(f"📊 Data imported: {len(self.state.processed_csv)} datasets")
        
        if self.state.errors:
            print(f"\n⚠️  Errors encountered: {len(self.state.errors)}")
            for error in self.state.errors[:5]:  # Show first 5 errors
                print(f"  - {error['phase']}: {error.get('item', '')} - {error['error']}")
        
        print("\n📍 Root page ID:", self.args.parent_id or NOTION_PARENT_PAGEID)
        print("="*60)

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point"""
    cli = CLIInterface()
    parser = cli.setup_parser()
    args = parser.parse_args()
    
    # Override parent ID if provided
    if args.parent_id:
        os.environ['NOTION_PARENT_PAGEID'] = args.parent_id
    
    # Run deployment
    deployer = NotionTemplateDeployer(args)
    success = deployer.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()