#!/usr/bin/env python3
"""
YAML Validation and Integrity Checker
ChatGPT's approach: Validate and preserve all 22 YAML configurations
"""
import yaml
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any

class YAMLValidator:
    """Validate and ensure integrity of all YAML files"""
    
    def __init__(self, yaml_dir: str = "../split_yaml"):
        self.yaml_dir = Path(yaml_dir)
        self.validation_report = {
            'valid_files': [],
            'invalid_files': [],
            'duplicate_content': [],
            'missing_required_fields': [],
            'statistics': {}
        }
    
    def validate_all(self) -> Dict:
        """Validate all YAML files and generate report"""
        yaml_files = list(self.yaml_dir.glob("*.yaml")) + list(self.yaml_dir.glob("*.yml"))
        
        print(f"🔍 Validating {len(yaml_files)} YAML files...")
        
        content_hashes = {}
        
        for yaml_file in yaml_files:
            is_valid, issues = self.validate_file(yaml_file)
            
            if is_valid:
                self.validation_report['valid_files'].append(str(yaml_file))
                
                # Check for duplicate content
                content_hash = self.get_content_hash(yaml_file)
                if content_hash in content_hashes:
                    self.validation_report['duplicate_content'].append({
                        'file1': str(content_hashes[content_hash]),
                        'file2': str(yaml_file),
                        'hash': content_hash
                    })
                else:
                    content_hashes[content_hash] = yaml_file
            else:
                self.validation_report['invalid_files'].append({
                    'file': str(yaml_file),
                    'issues': issues
                })
        
        # Generate statistics
        self.validation_report['statistics'] = {
            'total_files': len(yaml_files),
            'valid_files': len(self.validation_report['valid_files']),
            'invalid_files': len(self.validation_report['invalid_files']),
            'duplicates': len(self.validation_report['duplicate_content']),
            'unique_configs': len(content_hashes)
        }
        
        return self.validation_report
    
    def validate_file(self, filepath: Path) -> Tuple[bool, List[str]]:
        """Validate a single YAML file"""
        issues = []
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if data is None:
                issues.append("Empty file")
                return False, issues
            
            # Check structure
            if not isinstance(data, (dict, list)):
                issues.append(f"Invalid root type: {type(data).__name__}")
            
            # Check for required fields based on filename patterns
            if 'console' in filepath.stem.lower():
                if isinstance(data, dict) and 'title' not in data:
                    issues.append("Missing 'title' field for console config")
            
            if 'legal' in filepath.stem.lower():
                if isinstance(data, dict) and 'document_type' not in data:
                    issues.append("Missing 'document_type' field for legal config")
            
            # Check for suspicious patterns
            if self.has_suspicious_content(data):
                issues.append("Contains suspicious content patterns")
            
        except yaml.YAMLError as e:
            issues.append(f"YAML parse error: {e}")
            return False, issues
        except Exception as e:
            issues.append(f"File error: {e}")
            return False, issues
        
        return len(issues) == 0, issues
    
    def get_content_hash(self, filepath: Path) -> str:
        """Generate hash of file content for duplicate detection"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def has_suspicious_content(self, data: Any) -> bool:
        """Check for suspicious patterns in data"""
        suspicious_patterns = ['<script', 'javascript:', 'onclick', 'onerror']
        
        data_str = json.dumps(data).lower()
        return any(pattern in data_str for pattern in suspicious_patterns)
    
    def generate_manifest(self) -> Dict:
        """Generate manifest of all valid YAML files"""
        manifest = {
            'version': '4.0',
            'total_configs': len(self.validation_report['valid_files']),
            'categories': {},
            'files': []
        }
        
        for filepath in self.validation_report['valid_files']:
            path = Path(filepath)
            category = self.categorize_file(path.stem)
            
            if category not in manifest['categories']:
                manifest['categories'][category] = []
            
            manifest['categories'][category].append(path.name)
            manifest['files'].append({
                'name': path.name,
                'category': category,
                'size': path.stat().st_size
            })
        
        return manifest
    
    def categorize_file(self, filename: str) -> str:
        """Categorize file based on name patterns"""
        filename_lower = filename.lower()
        
        if 'legal' in filename_lower or 'will' in filename_lower:
            return 'legal'
        elif 'console' in filename_lower or 'builder' in filename_lower:
            return 'builders'
        elif 'accept' in filename_lower or 'letter' in filename_lower:
            return 'correspondence'
        elif 'todo' in filename_lower or 'task' in filename_lower:
            return 'productivity'
        elif 'finance' in filename_lower or 'budget' in filename_lower:
            return 'financial'
        elif 'health' in filename_lower or 'medical' in filename_lower:
            return 'health'
        else:
            return 'general'
    
    def save_report(self, output_path: str = "validation_report.json"):
        """Save validation report to file"""
        with open(output_path, 'w') as f:
            json.dump(self.validation_report, f, indent=2)
        print(f"📊 Validation report saved to {output_path}")