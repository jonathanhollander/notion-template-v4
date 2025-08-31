"""
CSV Data Processor
Handles loading and processing of CSV data files
"""
import csv
import json
from pathlib import Path
from typing import Dict, List, Any

class CSVProcessor:
    """Process CSV data files for Notion import"""
    
    def __init__(self, csv_dir: str = "../csv"):
        self.csv_dir = Path(csv_dir)
        self.data = {}
        
    def load_csv_file(self, filepath: Path) -> List[Dict]:
        """Load a single CSV file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return []
    
    def load_all_data(self) -> Dict[str, List[Dict]]:
        """Load all CSV files from directory"""
        if not self.csv_dir.exists():
            print(f"CSV directory not found: {self.csv_dir}")
            return {}
        
        csv_files = list(self.csv_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            data_name = csv_file.stem
            self.data[data_name] = self.load_csv_file(csv_file)
            print(f"Loaded {data_name}: {len(self.data[data_name])} rows")
        
        return self.data
    
    def merge_datasets(self, datasets: List[List[Dict]]) -> List[Dict]:
        """Merge multiple CSV datasets with deduplication"""
        merged = []
        seen_keys = set()
        
        for dataset in datasets:
            for row in dataset:
                # Create unique key from row data
                row_key = json.dumps(row, sort_keys=True)
                if row_key not in seen_keys:
                    seen_keys.add(row_key)
                    merged.append(row)
        
        return merged
    
    def transform_for_notion(self, data: List[Dict], mapping: Dict) -> List[Dict]:
        """Transform CSV data to Notion properties format"""
        transformed = []
        
        for row in data:
            notion_properties = {}
            
            for csv_field, notion_config in mapping.items():
                if csv_field in row:
                    value = row[csv_field]
                    prop_type = notion_config.get('type', 'rich_text')
                    
                    if prop_type == 'title':
                        notion_properties[notion_config['name']] = {
                            'title': [{'text': {'content': str(value)}}]
                        }
                    elif prop_type == 'rich_text':
                        notion_properties[notion_config['name']] = {
                            'rich_text': [{'text': {'content': str(value)}}]
                        }
                    elif prop_type == 'number':
                        try:
                            notion_properties[notion_config['name']] = {
                                'number': float(value) if value else None
                            }
                        except ValueError:
                            pass
                    elif prop_type == 'checkbox':
                        notion_properties[notion_config['name']] = {
                            'checkbox': bool(value)
                        }
                    elif prop_type == 'select':
                        notion_properties[notion_config['name']] = {
                            'select': {'name': str(value)} if value else None
                        }
            
            transformed.append(notion_properties)
        
        return transformed