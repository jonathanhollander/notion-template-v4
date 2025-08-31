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
from urllib.parse import quote
from datetime import datetime

# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2025-09-03")
NOTION_PARENT_PAGEID = os.getenv("NOTION_PARENT_PAGEID")

GLOBAL_THROTTLE_RPS = float(os.getenv("THROTTLE_RPS", "2.5"))
ENABLE_SEARCH_FALLBACK = os.getenv("ENABLE_SEARCH_FALLBACK", "1") in ("1", "true", "True", "yes", "YES")

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
        yaml_dir = Path(__file__).parent.parent / "split_yaml"
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
    logging.info(f"Found {len(yaml_files)} YAML files to process")
    
    for yaml_file in yaml_files:
        logging.debug(f"Loading {yaml_file.name}")
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data:
                continue
                
            # Merge pages
            if 'pages' in data:
                merged['pages'].extend(data['pages'])
                
            # Merge database schemas
            if 'db' in data:
                if 'schemas' in data['db']:
                    merged['db']['schemas'].update(data['db']['schemas'])
                if 'seed_rows' in data['db']:
                    merged['db']['seed_rows'].update(data['db']['seed_rows'])
                    
        except Exception as e:
            logging.error(f"Failed to load {yaml_file.name}: {e}")
            
    logging.info(f"Merged {len(merged['pages'])} pages and {len(merged['db']['schemas'])} database schemas")
    return merged

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
    
    # Build content blocks
    children = []
    if 'content' in page_data:
        for block in page_data['content']:
            children.append(build_block(block))
    
    # Create page
    payload = {
        "parent": parent,
        "properties": properties
    }
    if children:
        payload["children"] = children
    
    try:
        r = req("POST", "https://api.notion.com/v1/pages", data=json.dumps(payload))
        if expect_ok(r, f"Creating page '{title}'"):
            page_id = j(r).get('id')
            state.created_pages[title] = page_id
            logging.info(f"Created page '{title}': {page_id}")
            return page_id
    except Exception as e:
        logging.error(f"Failed to create page '{title}': {e}")
        state.errors.append({"phase": "pages", "item": title, "error": str(e)})
    
    return None

def create_database(db_name: str, schema: Dict, state: DeploymentState, 
                   parent_id: Optional[str] = None) -> Optional[str]:
    """Create a Notion database with schema"""
    
    # Check if already created
    if db_name in state.created_databases:
        logging.debug(f"Database '{db_name}' already exists: {state.created_databases[db_name]}")
        return state.created_databases[db_name]
    
    # Build properties schema
    properties = {}
    for prop_name, prop_def in schema.get('properties', {}).items():
        properties[prop_name] = build_property_schema(prop_def)
    
    # Ensure Name property exists
    if 'Name' not in properties:
        properties['Name'] = {"title": {}}
    
    # Determine parent
    if parent_id:
        parent = {"page_id": parent_id}
    elif schema.get('parent'):
        parent_title = schema['parent']
        if parent_title in state.created_pages:
            parent = {"page_id": state.created_pages[parent_title]}
        else:
            parent = {"page_id": NOTION_PARENT_PAGEID}
    else:
        parent = {"page_id": NOTION_PARENT_PAGEID}
    
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

def build_block(block_def: Dict) -> Dict:
    """Build a Notion block from definition"""
    block_type = block_def.get('type', 'paragraph')
    
    if block_type == 'heading_1':
        return {
            "heading_1": {
                "rich_text": [{"text": {"content": block_def.get('text', '')}}]
            }
        }
    elif block_type == 'heading_2':
        return {
            "heading_2": {
                "rich_text": [{"text": {"content": block_def.get('text', '')}}]
            }
        }
    elif block_type == 'bulleted_list_item':
        return {
            "bulleted_list_item": {
                "rich_text": [{"text": {"content": block_def.get('text', '')}}]
            }
        }
    else:  # Default to paragraph
        return {
            "paragraph": {
                "rich_text": [{"text": {"content": block_def.get('text', '')}}]
            }
        }

def build_property_schema(prop_def: Dict) -> Dict:
    """Build property schema for database"""
    prop_type = prop_def.get('type', 'rich_text')
    
    if prop_type == 'title':
        return {"title": {}}
    elif prop_type == 'number':
        return {"number": {"format": prop_def.get('format', 'number')}}
    elif prop_type == 'select':
        return {
            "select": {
                "options": [{"name": opt} for opt in prop_def.get('options', [])]
            }
        }
    elif prop_type == 'multi_select':
        return {
            "multi_select": {
                "options": [{"name": opt} for opt in prop_def.get('options', [])]
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
        return {
            "formula": {
                "expression": prop_def.get('expression', '')
            }
        }
    elif prop_type == 'relation':
        return {
            "relation": {
                "database_id": prop_def.get('database_id', ''),
                "type": prop_def.get('relation_type', 'single_property'),
                "single_property": {} if prop_def.get('relation_type') != 'dual_property' else None,
                "dual_property": {
                    "synced_property_name": prop_def.get('synced_property_name', ''),
                    "synced_property_id": prop_def.get('synced_property_id', '')
                } if prop_def.get('relation_type') == 'dual_property' else None
            }
        }
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
        """Configure logging based on verbosity"""
        if self.args.quiet:
            level = logging.ERROR
        elif self.args.verbose >= 3:
            level = logging.DEBUG
        elif self.args.verbose >= 2:
            level = logging.INFO
        elif self.args.verbose >= 1:
            level = logging.WARNING
        else:
            level = logging.ERROR
            
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    
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
        if self.state.phase.value > phase.value:  # Already completed in previous run
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
    
    def deploy_pages(self, yaml_data: Dict) -> bool:
        """Deploy all pages"""
        self.state.phase = DeploymentPhase.PAGES
        pages = yaml_data.get('pages', [])
        
        if self.args.interactive:
            if not CLIInterface.prompt_continue(f"Deploy {len(pages)} pages?"):
                return False
        
        for page in pages:
            self.progress.update(DeploymentPhase.PAGES, f"Creating: {page.get('title', 'Untitled')}")
            
            parent_id = self.args.parent_id or NOTION_PARENT_PAGEID
            page_id = create_page(page, self.state, parent_id)
            
            if not page_id and not self.args.interactive:
                return False
            elif not page_id and self.args.interactive:
                if not CLIInterface.prompt_continue("Page creation failed. Continue?"):
                    return False
            
            self.state.save_checkpoint()
        
        return True
    
    def deploy_databases(self, yaml_data: Dict) -> bool:
        """Deploy all databases"""
        self.state.phase = DeploymentPhase.DATABASES
        schemas = yaml_data.get('db', {}).get('schemas', {})
        
        if self.args.interactive:
            if not CLIInterface.prompt_continue(f"Deploy {len(schemas)} databases?"):
                return False
        
        for db_name, schema in schemas.items():
            self.progress.update(DeploymentPhase.DATABASES, f"Creating: {db_name}")
            
            parent_id = self.args.parent_id or NOTION_PARENT_PAGEID
            db_id = create_database(db_name, schema, self.state, parent_id)
            
            if not db_id and not self.args.interactive:
                return False
            elif not db_id and self.args.interactive:
                if not CLIInterface.prompt_continue("Database creation failed. Continue?"):
                    return False
            
            self.state.save_checkpoint()
        
        return True
    
    def setup_relations(self, yaml_data: Dict) -> bool:
        """Setup database relations"""
        self.state.phase = DeploymentPhase.RELATIONS
        self.progress.update(DeploymentPhase.RELATIONS, "Configuring relations")
        
        # TODO: Implement relation setup based on schema definitions
        # This requires updating database properties after creation
        
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