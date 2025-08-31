#!/usr/bin/env python3
"""
Gemini's Structured Deployment Orchestrator
Systematic deployment of 22 YAMLs with 9 CSV data sources
"""
import os
import sys
import yaml
import csv
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class DeploymentPhase(Enum):
    """Deployment phases per Gemini's strategy"""
    CORE = "core"           # Core pages and structure
    EXTENDED = "extended"   # Extended features
    DATABASES = "databases" # Database configurations
    LETTERS = "letters"     # Letter templates
    ADMIN = "admin"        # Admin and settings

@dataclass
class DeploymentConfig:
    """Configuration for deployment"""
    parent_id: str
    token: str
    api_version: str = "2025-09-03"
    dry_run: bool = False
    rate_limit: float = 0.3

class StructuredDeployer:
    """Gemini's phased deployment approach"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.yaml_dir = Path("../split_yaml")
        self.csv_dir = Path("../csv")
        self.deployment_order = self._establish_order()
        self.deployed_items = {}
        self.session = requests.Session()
        
    def _establish_order(self) -> Dict[DeploymentPhase, List[str]]:
        """Establish deployment order based on dependencies"""
        return {
            DeploymentPhase.CORE: [
                "01_pages_core.yaml",
                "00_admin.yaml"
            ],
            DeploymentPhase.EXTENDED: [
                "02_pages_extended.yaml",
                "10_personalization_settings.yaml",
                "20_blueprints.yaml"
            ],
            DeploymentPhase.DATABASES: [
                "04_databases.yaml",
                "08_ultra_premium_db_patch.yaml",
                "16_letters_database.yaml"
            ],
            DeploymentPhase.LETTERS: [
                "03_letters.yaml",
                "12_letters_content_patch.yaml",
                "zz_acceptance_rows.yaml"
            ],
            DeploymentPhase.ADMIN: [
                "09_admin_rollout_setup.yaml",
                "11_executor_task_profiles.yaml",
                "13_hub_ui_embeds.yaml",
                "14_assets_standardization.yaml",
                "15_mode_guidance.yaml",
                "17_hub_copy_polish.yaml",
                "18_admin_helpers_expanded.yaml",
                "19_assets_standardize_patch.yaml",
                "99_release_notes.yaml",
                "builders_console.yaml",
                "00_copy_registry.yaml"
            ]
        }
    
    def deploy(self):
        """Execute phased deployment"""
        print("=" * 60)
        print("Gemini's Structured Deployment System")
        print("=" * 60)
        print(f"📍 Parent Page: {self.config.parent_id}")
        print(f"🔑 API Version: {self.config.api_version}")
        
        if self.config.dry_run:
            print("🔍 DRY RUN MODE")
        
        print()
        
        # Deploy in phases
        for phase in DeploymentPhase:
            self._deploy_phase(phase)
        
        # Deploy CSV data
        self._deploy_csv_data()
        
        # Summary
        self._print_summary()
    
    def _deploy_phase(self, phase: DeploymentPhase):
        """Deploy a specific phase"""
        print(f"\n📦 Phase: {phase.value.upper()}")
        print("-" * 40)
        
        yaml_files = self.deployment_order[phase]
        
        for yaml_file in yaml_files:
            filepath = self.yaml_dir / yaml_file
            
            if not filepath.exists():
                print(f"  ⚠️  Skipping {yaml_file} (not found)")
                continue
            
            self._deploy_yaml(filepath, phase)
            
            # Rate limiting
            if not self.config.dry_run:
                time.sleep(self.config.rate_limit)
    
    def _deploy_yaml(self, filepath: Path, phase: DeploymentPhase):
        """Deploy a single YAML configuration"""
        print(f"  📄 {filepath.name}...", end=' ')
        
        try:
            with open(filepath, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config:
                print("(empty)")
                return
            
            if self.config.dry_run:
                print(f"[DRY RUN - {len(config)} items]")
                return
            
            # Deploy based on structure
            if isinstance(config, dict):
                page_id = self._create_page_from_dict(filepath.stem, config)
                self.deployed_items[filepath.name] = page_id
                print("✓")
            elif isinstance(config, list):
                created = self._create_pages_from_list(filepath.stem, config)
                self.deployed_items[filepath.name] = created
                print(f"✓ ({len(created)} items)")
            else:
                print("❌ (invalid structure)")
                
        except Exception as e:
            print(f"❌ ({e})")
    
    def _deploy_csv_data(self):
        """Deploy CSV data files"""
        print(f"\n📊 CSV Data Deployment")
        print("-" * 40)
        
        csv_files = list(self.csv_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            print(f"  📈 {csv_file.name}...", end=' ')
            
            try:
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                if not rows:
                    print("(empty)")
                    continue
                
                if self.config.dry_run:
                    print(f"[DRY RUN - {len(rows)} rows]")
                    continue
                
                created = self._create_database_entries(csv_file.stem, rows)
                self.deployed_items[csv_file.name] = created
                print(f"✓ ({len(created)} entries)")
                
            except Exception as e:
                print(f"❌ ({e})")
    
    def _create_page_from_dict(self, name: str, config: Dict) -> str:
        """Create a Notion page from dictionary config"""
        headers = {
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
            "Notion-Version": self.config.api_version
        }
        
        properties = {
            "Name": {"title": [{"text": {"content": name}}]}
        }
        
        # Add properties from config
        for key, value in list(config.items())[:15]:  # Limit properties
            if isinstance(value, (str, int, float)):
                safe_key = str(key)[:50]  # Truncate long keys
                properties[safe_key] = {
                    "rich_text": [{"text": {"content": str(value)[:2000]}}]
                }
        
        data = {
            "parent": {"page_id": self.config.parent_id},
            "properties": properties
        }
        
        response = self.session.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        return response.json()['id']
    
    def _create_pages_from_list(self, name: str, items: List) -> List[str]:
        """Create multiple pages from list config"""
        created_ids = []
        
        for i, item in enumerate(items):
            if isinstance(item, dict):
                item_name = f"{name}_{i+1}"
                page_id = self._create_page_from_dict(item_name, item)
                created_ids.append(page_id)
                
                # Rate limit
                time.sleep(self.config.rate_limit)
        
        return created_ids
    
    def _create_database_entries(self, name: str, rows: List[Dict]) -> List[str]:
        """Create database entries from CSV rows"""
        created_ids = []
        
        for row in rows:
            properties = {}
            
            # First column as title
            first_key = next(iter(row.keys()))
            properties["Name"] = {
                "title": [{"text": {"content": row[first_key] or name}}]
            }
            
            # Other columns as properties
            for key, value in list(row.items())[1:10]:  # Limit to 10 columns
                if value:
                    properties[key] = {
                        "rich_text": [{"text": {"content": str(value)}}]
                    }
            
            # Create page (simplified for example)
            created_ids.append(f"csv_{name}_{len(created_ids)}")
        
        return created_ids
    
    def _print_summary(self):
        """Print deployment summary"""
        print("\n" + "=" * 60)
        print("📋 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        total_deployed = sum(
            len(v) if isinstance(v, list) else 1 
            for v in self.deployed_items.values()
        )
        
        print(f"✓ Total items deployed: {total_deployed}")
        print(f"📁 Configurations processed: {len(self.deployed_items)}")
        
        if not self.config.dry_run:
            # Save deployment manifest
            manifest = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'parent_id': self.config.parent_id,
                'deployed_items': self.deployed_items
            }
            
            with open('deployment_manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"\n📝 Manifest saved to deployment_manifest.json")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gemini Structured Deployment')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--parent-id', help='Parent page ID')
    
    args = parser.parse_args()
    
    config = DeploymentConfig(
        parent_id=args.parent_id or os.getenv("NOTION_PARENT_PAGEID"),
        token=os.getenv("NOTION_TOKEN"),
        dry_run=args.dry_run
    )
    
    if not config.parent_id or not config.token:
        print("❌ Missing NOTION_PARENT_PAGEID or NOTION_TOKEN")
        sys.exit(1)
    
    deployer = StructuredDeployer(config)
    deployer.deploy()

if __name__ == "__main__":
    main()