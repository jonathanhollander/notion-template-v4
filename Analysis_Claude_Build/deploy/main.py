#!/usr/bin/env python3
"""
Main Deployment Script for Notion Template v4.0
Refactored with clean architecture
"""
import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

from auth import NotionAuth
from api_client import NotionAPIClient
from yaml_processor import YAMLProcessor
from csv_processor import CSVProcessor

class NotionTemplateDeployer:
    """Main orchestrator for Notion template deployment"""
    
    def __init__(self, parent_page_id: str = None, dry_run: bool = False):
        """Initialize deployer with configuration"""
        self.parent_page_id = parent_page_id or os.getenv("NOTION_PARENT_PAGEID")
        if not self.parent_page_id:
            raise ValueError("Parent page ID not provided")
        
        self.dry_run = dry_run
        self.auth = NotionAuth()
        self.client = NotionAPIClient(self.auth)
        self.yaml_processor = YAMLProcessor()
        self.csv_processor = CSVProcessor()
        
        self.created_pages = []
        self.errors = []
    
    def deploy(self):
        """Main deployment workflow"""
        print("=" * 60)
        print("Notion Template Deployment v4.0")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        print(f"📍 Parent Page ID: {self.parent_page_id}")
        print(f"🔑 API Version: {self.auth.api_version}")
        print()
        
        # Load configurations
        print("📂 Loading YAML configurations...")
        yaml_configs = self.yaml_processor.load_all_configs()
        print(f"✓ Loaded {len(yaml_configs)} configuration files")
        print()
        
        # Load CSV data
        print("📊 Loading CSV data...")
        csv_data = self.csv_processor.load_all_data()
        print(f"✓ Loaded {len(csv_data)} data files")
        print()
        
        # Deploy each configuration type
        for config_name, config in yaml_configs.items():
            self.deploy_config(config_name, config, csv_data)
        
        # Summary
        self.print_summary()
    
    def deploy_config(self, name: str, config: Dict, csv_data: Dict):
        """Deploy a single configuration"""
        print(f"🚀 Deploying {name}...")
        
        try:
            # Check if this config has associated CSV data
            associated_data = csv_data.get(name, [])
            
            if associated_data:
                print(f"  Found {len(associated_data)} data rows")
                self.deploy_with_data(name, config, associated_data)
            else:
                self.deploy_static(name, config)
            
            print(f"✓ Completed {name}")
            
        except Exception as e:
            error_msg = f"Error deploying {name}: {e}"
            print(f"❌ {error_msg}")
            self.errors.append(error_msg)
        
        print()
    
    def deploy_static(self, name: str, config: Dict):
        """Deploy static configuration without CSV data"""
        if self.dry_run:
            print(f"  [DRY RUN] Would create page: {name}")
            return
        
        # Create main page
        properties = self.build_properties_from_config(config)
        page = self.client.create_page(self.parent_page_id, properties)
        self.created_pages.append(page['id'])
        print(f"  Created page: {page['id']}")
        
        # Add any child blocks if defined
        if 'blocks' in config:
            self.add_blocks(page['id'], config['blocks'])
    
    def deploy_with_data(self, name: str, config: Dict, data: List[Dict]):
        """Deploy configuration with CSV data"""
        if self.dry_run:
            print(f"  [DRY RUN] Would create {len(data)} pages for {name}")
            return
        
        # Transform CSV data to Notion format
        mapping = config.get('csv_mapping', {})
        if mapping:
            transformed_data = self.csv_processor.transform_for_notion(data, mapping)
        else:
            # Use default transformation
            transformed_data = self.default_transform(data)
        
        # Create pages for each data row
        for i, row_properties in enumerate(transformed_data):
            try:
                page = self.client.create_page(self.parent_page_id, row_properties)
                self.created_pages.append(page['id'])
                
                if (i + 1) % 10 == 0:
                    print(f"  Created {i + 1}/{len(transformed_data)} pages")
                    
            except Exception as e:
                self.errors.append(f"Row {i+1} of {name}: {e}")
    
    def build_properties_from_config(self, config: Dict) -> Dict:
        """Build Notion properties from configuration"""
        properties = {}
        
        # Extract title
        if 'title' in config:
            properties['Name'] = {
                'title': [{'text': {'content': config['title']}}]
            }
        
        # Extract other properties
        for key, value in config.items():
            if key in ['title', 'blocks', 'csv_mapping']:
                continue
                
            # Auto-detect property type
            if isinstance(value, bool):
                properties[key] = {'checkbox': value}
            elif isinstance(value, (int, float)):
                properties[key] = {'number': value}
            elif isinstance(value, list):
                # Convert to multi-select or tags
                properties[key] = {
                    'multi_select': [{'name': str(item)} for item in value]
                }
            else:
                # Default to rich text
                properties[key] = {
                    'rich_text': [{'text': {'content': str(value)}}]
                }
        
        return properties
    
    def default_transform(self, data: List[Dict]) -> List[Dict]:
        """Default transformation for CSV data without mapping"""
        transformed = []
        
        for row in data:
            properties = {}
            
            for key, value in row.items():
                if not value:
                    continue
                
                # Use first column as title
                if not properties:
                    properties['Name'] = {
                        'title': [{'text': {'content': str(value)}}]
                    }
                else:
                    properties[key] = {
                        'rich_text': [{'text': {'content': str(value)}}]
                    }
            
            transformed.append(properties)
        
        return transformed
    
    def add_blocks(self, page_id: str, blocks: List[Dict]):
        """Add blocks to a page"""
        notion_blocks = []
        
        for block in blocks:
            block_type = block.get('type', 'paragraph')
            content = block.get('content', '')
            
            notion_block = {
                'type': block_type,
                block_type: {
                    'rich_text': [{'text': {'content': content}}]
                }
            }
            notion_blocks.append(notion_block)
        
        if notion_blocks and not self.dry_run:
            self.client.append_blocks(page_id, notion_blocks)
            print(f"  Added {len(notion_blocks)} blocks")
    
    def print_summary(self):
        """Print deployment summary"""
        print("=" * 60)
        print("📋 DEPLOYMENT SUMMARY")
        print("=" * 60)
        
        if self.dry_run:
            print("🔍 DRY RUN COMPLETED - No changes were made")
        else:
            print(f"✓ Created {len(self.created_pages)} pages")
            
            if self.errors:
                print(f"⚠️  Encountered {len(self.errors)} errors:")
                for error in self.errors[:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(self.errors) > 5:
                    print(f"  ... and {len(self.errors) - 5} more")
            else:
                print("✓ No errors encountered")
        
        print("=" * 60)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Deploy Notion Template v4.0')
    parser.add_argument('--parent-id', help='Parent page ID')
    parser.add_argument('--dry-run', action='store_true', help='Test without making changes')
    parser.add_argument('--config', help='Custom configuration file')
    
    args = parser.parse_args()
    
    try:
        deployer = NotionTemplateDeployer(
            parent_page_id=args.parent_id,
            dry_run=args.dry_run
        )
        deployer.deploy()
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()