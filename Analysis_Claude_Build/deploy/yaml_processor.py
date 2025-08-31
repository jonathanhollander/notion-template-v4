"""
YAML Configuration Processor
Handles loading and merging of YAML configurations
"""
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any

class YAMLProcessor:
    """Process and merge YAML configuration files"""
    
    def __init__(self, yaml_dir: str = "../split_yaml"):
        self.yaml_dir = Path(yaml_dir)
        self.configs = {}
        
    def load_yaml_file(self, filepath: Path) -> Dict[str, Any]:
        """Load a single YAML file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
    
    def load_all_configs(self) -> Dict[str, Dict]:
        """Load all YAML files from directory"""
        if not self.yaml_dir.exists():
            raise FileNotFoundError(f"YAML directory not found: {self.yaml_dir}")
        
        yaml_files = list(self.yaml_dir.glob("*.yaml")) + list(self.yaml_dir.glob("*.yml"))
        
        for yaml_file in yaml_files:
            config_name = yaml_file.stem
            self.configs[config_name] = self.load_yaml_file(yaml_file)
            print(f"Loaded {config_name}: {len(self.configs[config_name])} items")
        
        return self.configs
    
    def merge_configs(self, configs: List[Dict]) -> Dict:
        """Merge multiple configurations with deduplication"""
        merged = {}
        
        for config in configs:
            for key, value in config.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(value, dict) and isinstance(merged[key], dict):
                    # Recursive merge for nested dicts
                    merged[key] = self.merge_configs([merged[key], value])
                elif isinstance(value, list) and isinstance(merged[key], list):
                    # Combine lists and remove duplicates
                    merged[key] = list(set(merged[key] + value))
                # Otherwise keep existing value (first occurrence wins)
        
        return merged
    
    def get_config_by_type(self, config_type: str) -> Dict:
        """Get configuration by type (e.g., 'builders_console', 'legal_will')"""
        return self.configs.get(config_type, {})
    
    def get_all_separate(self) -> Dict[str, Dict]:
        """Get all configurations as separate files"""
        return self.configs
    
    def process_sequentially(self) -> List[Dict]:
        """Process YAML files maintaining separation"""
        processed = []
        for name, config in self.configs.items():
            processed.append({
                'name': name,
                'config': config,
                'item_count': len(config)
            })
        return processed