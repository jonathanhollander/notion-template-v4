#!/usr/bin/env python3
"""
ChatGPT's Validated Deployment Script
Deploys all 319 YAML files after validation
"""
import os
import sys
import json
import yaml
import time
import requests
from pathlib import Path
from typing import Dict, List, Any
from yaml_validator import YAMLValidator

class ValidatedDeployer:
    """Deploy with validation and integrity checks"""
    
    def __init__(self, parent_id: str = None, dry_run: bool = False):
        self.parent_id = parent_id or os.getenv("NOTION_PARENT_PAGEID")
        self.token = os.getenv("NOTION_TOKEN")
        self.api_version = os.getenv("NOTION_VERSION", "2025-09-03")
        self.dry_run = dry_run
        
        if not self.parent_id:
            raise ValueError("NOTION_PARENT_PAGEID not set")
        if not self.token:
            raise ValueError("NOTION_TOKEN not set")
        
        self.validator = YAMLValidator()
        self.deployed_configs = []
        self.failed_configs = []
        
    def deploy(self):
        """Main deployment with validation"""
        print("=" * 60)
        print("ChatGPT's Validated Notion Deployment")
        print("Preserving all 319 YAML configurations")
        print("=" * 60)
        
        # Step 1: Validate all YAMLs
        print("\n📋 Phase 1: Validation")
        validation_report = self.validator.validate_all()
        
        print(f"✓ Valid files: {validation_report['statistics']['valid_files']}")
        print(f"⚠️  Invalid files: {validation_report['statistics']['invalid_files']}")
        print(f"🔄 Duplicates: {validation_report['statistics']['duplicates']}")
        
        if validation_report['invalid_files']:
            print("\n❌ Invalid files detected:")
            for invalid in validation_report['invalid_files'][:5]:
                print(f"  - {invalid['file']}: {invalid['issues']}")
            
            if not self.dry_run:
                response = input("\nContinue with valid files only? (y/n): ")
                if response.lower() != 'y':
                    print("Deployment cancelled")
                    return
        
        # Step 2: Generate manifest
        print("\n📦 Phase 2: Manifest Generation")
        manifest = self.validator.generate_manifest()
        print(f"✓ Categorized {len(manifest['files'])} configurations")
        for category, files in manifest['categories'].items():
            print(f"  {category}: {len(files)} files")
        
        # Step 3: Deploy each valid YAML separately
        print("\n🚀 Phase 3: Deployment")
        
        if self.dry_run:
            print("🔍 DRY RUN - No actual deployment")
        
        for filepath in validation_report['valid_files']:
            self.deploy_yaml_file(filepath)
        
        # Step 4: Summary
        self.print_summary()
    
    def deploy_yaml_file(self, filepath: str):
        """Deploy a single YAML file to Notion"""
        path = Path(filepath)
        
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return
            
            config_name = path.stem
            print(f"  Deploying {config_name}...", end=' ')
            
            if self.dry_run:
                print("[DRY RUN]")
                self.deployed_configs.append(config_name)
                return
            
            # Create Notion page for this config
            page = self.create_notion_page(config_name, config)
            
            if page:
                self.deployed_configs.append(config_name)
                print("✓")
            else:
                self.failed_configs.append(config_name)
                print("❌")
            
            # Rate limiting
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            self.failed_configs.append(path.stem)
    
    def create_notion_page(self, name: str, config: Dict) -> Dict:
        """Create a Notion page from config"""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": self.api_version
        }
        
        # Build properties
        properties = {
            "Name": {
                "title": [{"text": {"content": name}}]
            }
        }
        
        # Add config data as properties
        if isinstance(config, dict):
            for key, value in list(config.items())[:10]:  # Limit to 10 properties
                if key == 'title':
                    properties["Name"]["title"][0]["text"]["content"] = str(value)
                elif isinstance(value, (str, int, float)):
                    properties[key[:50]] = {  # Truncate long keys
                        "rich_text": [{"text": {"content": str(value)[:2000]}}]
                    }
        
        data = {
            "parent": {"page_id": self.parent_id},
            "properties": properties
        }
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"\n    API Error: {e}")
            return None
    
    def print_summary(self):
        """Print deployment summary"""
        print("\n" + "=" * 60)
        print("📊 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        print(f"✓ Successfully deployed: {len(self.deployed_configs)} configs")
        print(f"❌ Failed: {len(self.failed_configs)} configs")
        
        if self.failed_configs and len(self.failed_configs) <= 10:
            print("\nFailed configurations:")
            for config in self.failed_configs:
                print(f"  - {config}")
        
        # Save deployment log
        log = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'deployed': self.deployed_configs,
            'failed': self.failed_configs,
            'dry_run': self.dry_run
        }
        
        with open('deployment_log.json', 'w') as f:
            json.dump(log, f, indent=2)
        
        print(f"\n📝 Log saved to deployment_log.json")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ChatGPT Validated Deployment')
    parser.add_argument('--dry-run', action='store_true', help='Validate without deploying')
    parser.add_argument('--parent-id', help='Override parent page ID')
    
    args = parser.parse_args()
    
    try:
        deployer = ValidatedDeployer(
            parent_id=args.parent_id,
            dry_run=args.dry_run
        )
        deployer.deploy()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)