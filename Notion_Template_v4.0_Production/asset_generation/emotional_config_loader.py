#!/usr/bin/env python3
"""
Emotional Configuration Loader
Handles loading, validation, and management of YAML configuration files
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil
import os
from dataclasses import dataclass, field
from enum import Enum

class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass

class ConfigBackupError(Exception):
    """Raised when configuration backup operations fail"""
    pass

@dataclass 
class EmotionalToneConfig:
    """Configuration for an emotional tone"""
    name: str
    description: str
    keywords: List[str]
    intensity: float
    use_cases: List[str]
    emotional_weight: str

@dataclass
class StyleElementsConfig:
    """Configuration for style elements"""
    materials: List[str] = field(default_factory=list)
    lighting: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    textures: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    composition: List[str] = field(default_factory=list)

@dataclass
class EmotionalConfig:
    """Complete emotional configuration"""
    version: str
    created: str
    last_modified: str
    description: str
    emotional_tones: Dict[str, EmotionalToneConfig]
    style_elements: StyleElementsConfig
    emotional_mappings: Dict[str, Any]

class EmotionalConfigLoader:
    """Loads and manages emotional intelligence configuration from YAML files"""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration loader"""
        self.config_dir = Path(config_dir or os.path.dirname(__file__))
        self.active_config_file = self.config_dir / "emotional_config.yaml"
        self.defaults_config_file = self.config_dir / "emotional_defaults.yaml"
        self.backups_dir = self.config_dir / "backups" / "emotional_config"
        
        # Ensure backups directory exists
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self._active_config = None
        self._defaults_config = None
    
    def load_active_config(self) -> EmotionalConfig:
        """Load the active configuration file"""
        try:
            with open(self.active_config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self._active_config = self._parse_config(config_data)
            return self._active_config
            
        except FileNotFoundError:
            # If active config doesn't exist, create from defaults
            return self.reset_to_defaults()
        except Exception as e:
            raise ConfigValidationError(f"Failed to load active config: {e}")
    
    def load_defaults_config(self) -> EmotionalConfig:
        """Load the immutable defaults configuration"""
        try:
            with open(self.defaults_config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self._defaults_config = self._parse_config(config_data)
            return self._defaults_config
            
        except FileNotFoundError:
            raise ConfigValidationError("Defaults configuration file not found - system integrity compromised")
        except Exception as e:
            raise ConfigValidationError(f"Failed to load defaults config: {e}")
    
    def _parse_config(self, config_data: Dict[str, Any]) -> EmotionalConfig:
        """Parse YAML configuration data into structured objects"""
        try:
            # Parse emotional tones
            emotional_tones = {}
            for tone_key, tone_data in config_data.get('emotional_tones', {}).items():
                emotional_tones[tone_key] = EmotionalToneConfig(
                    name=tone_data['name'],
                    description=tone_data['description'],
                    keywords=tone_data['keywords'],
                    intensity=tone_data['intensity'],
                    use_cases=tone_data['use_cases'],
                    emotional_weight=tone_data['emotional_weight']
                )
            
            # Parse style elements
            style_data = config_data.get('style_elements', {})
            style_elements = StyleElementsConfig(
                materials=style_data.get('materials', []),
                lighting=style_data.get('lighting', []),
                colors=style_data.get('colors', []),
                textures=style_data.get('textures', []),
                objects=style_data.get('objects', []),
                composition=style_data.get('composition', [])
            )
            
            # Create complete configuration
            return EmotionalConfig(
                version=config_data.get('version', '1.0.0'),
                created=config_data.get('created', ''),
                last_modified=config_data.get('last_modified', ''),
                description=config_data.get('description', ''),
                emotional_tones=emotional_tones,
                style_elements=style_elements,
                emotional_mappings=config_data.get('emotional_mappings', {})
            )
            
        except KeyError as e:
            raise ConfigValidationError(f"Missing required configuration key: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Configuration parsing error: {e}")
    
    def validate_config(self, config: EmotionalConfig) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check version
        if not config.version:
            issues.append("Missing version information")
        
        # Check emotional tones
        if not config.emotional_tones:
            issues.append("No emotional tones defined")
        
        for tone_key, tone in config.emotional_tones.items():
            if not tone.name:
                issues.append(f"Tone '{tone_key}' missing name")
            if not tone.keywords:
                issues.append(f"Tone '{tone_key}' has no keywords")
            if not 0 <= tone.intensity <= 1:
                issues.append(f"Tone '{tone_key}' intensity must be between 0 and 1")
        
        # Check style elements
        if not any([
            config.style_elements.materials,
            config.style_elements.lighting,
            config.style_elements.colors,
            config.style_elements.textures,
            config.style_elements.objects,
            config.style_elements.composition
        ]):
            issues.append("No style elements defined")
        
        # Check emotional mappings
        if not config.emotional_mappings:
            issues.append("No emotional mappings defined")
        
        return issues
    
    def backup_config(self, config_file: Path = None, custom_suffix: str = None) -> Path:
        """Create timestamped backup of configuration file"""
        try:
            source_file = config_file or self.active_config_file
            
            if not source_file.exists():
                raise ConfigBackupError(f"Source file does not exist: {source_file}")
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            if custom_suffix:
                backup_name = f"emotional_config_{timestamp}_{custom_suffix}.yaml"
            else:
                backup_name = f"emotional_config_{timestamp}.yaml"
            
            backup_path = self.backups_dir / backup_name
            
            # Copy file
            shutil.copy2(source_file, backup_path)
            
            # Clean old backups (keep only 10 most recent)
            self._cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            raise ConfigBackupError(f"Backup failed: {e}")
    
    def _cleanup_old_backups(self, max_backups: int = 10):
        """Remove old backup files, keeping only the most recent"""
        try:
            backup_files = list(self.backups_dir.glob("emotional_config_*.yaml"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                
        except Exception:
            # Don't fail if cleanup fails
            pass
    
    def save_config(self, config: EmotionalConfig, create_backup: bool = True) -> Path:
        """Save configuration to active config file"""
        try:
            # Validate configuration first
            issues = self.validate_config(config)
            if issues:
                raise ConfigValidationError(f"Configuration validation failed: {'; '.join(issues)}")
            
            # Create backup if requested and file exists
            if create_backup and self.active_config_file.exists():
                self.backup_config()
            
            # Convert config to dictionary
            config_dict = self._config_to_dict(config)
            
            # Update last_modified timestamp
            config_dict['last_modified'] = datetime.now().strftime("%Y-%m-%d")
            
            # Write to file
            with open(self.active_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, 
                         default_flow_style=False, 
                         allow_unicode=True,
                         indent=2,
                         sort_keys=False)
            
            return self.active_config_file
            
        except Exception as e:
            raise ConfigValidationError(f"Failed to save configuration: {e}")
    
    def _config_to_dict(self, config: EmotionalConfig) -> Dict[str, Any]:
        """Convert EmotionalConfig object to dictionary for YAML output"""
        
        # Convert emotional tones
        emotional_tones_dict = {}
        for tone_key, tone in config.emotional_tones.items():
            emotional_tones_dict[tone_key] = {
                'name': tone.name,
                'description': tone.description,
                'keywords': tone.keywords,
                'intensity': tone.intensity,
                'use_cases': tone.use_cases,
                'emotional_weight': tone.emotional_weight
            }
        
        # Convert style elements
        style_elements_dict = {
            'materials': config.style_elements.materials,
            'lighting': config.style_elements.lighting,
            'colors': config.style_elements.colors,
            'textures': config.style_elements.textures,
            'objects': config.style_elements.objects,
            'composition': config.style_elements.composition
        }
        
        return {
            'version': config.version,
            'created': config.created,
            'last_modified': config.last_modified,
            'description': config.description,
            'system_info': {
                'baseline_version': config.version,
                'can_reset_to_baseline': True,
                'backup_before_changes': True,
                'validated': True
            },
            'emotional_tones': emotional_tones_dict,
            'style_elements': style_elements_dict,
            'emotional_mappings': config.emotional_mappings
        }
    
    def reset_to_defaults(self) -> EmotionalConfig:
        """Reset active configuration to immutable defaults"""
        try:
            # Load defaults
            defaults = self.load_defaults_config()
            
            # Create backup of current config if it exists
            if self.active_config_file.exists():
                self.backup_config(custom_suffix="before_reset")
            
            # Save defaults as active config
            self.save_config(defaults, create_backup=False)
            
            return defaults
            
        except Exception as e:
            raise ConfigValidationError(f"Reset to defaults failed: {e}")
    
    def get_emotional_tone_names(self) -> List[str]:
        """Get list of available emotional tone names"""
        config = self.load_active_config()
        return list(config.emotional_tones.keys())
    
    def get_style_element_categories(self) -> List[str]:
        """Get list of style element category names"""
        return ['materials', 'lighting', 'colors', 'textures', 'objects', 'composition']
    
    def update_emotional_tone(self, tone_key: str, tone_config: EmotionalToneConfig) -> EmotionalConfig:
        """Update a single emotional tone in the active configuration"""
        config = self.load_active_config()
        config.emotional_tones[tone_key] = tone_config
        self.save_config(config)
        return config
    
    def add_style_element(self, category: str, element: str) -> EmotionalConfig:
        """Add a new style element to a category"""
        config = self.load_active_config()
        
        category_list = getattr(config.style_elements, category, None)
        if category_list is None:
            raise ConfigValidationError(f"Invalid style category: {category}")
        
        if element not in category_list:
            category_list.append(element)
            self.save_config(config)
        
        return config
    
    def remove_style_element(self, category: str, element: str) -> EmotionalConfig:
        """Remove a style element from a category"""
        config = self.load_active_config()
        
        category_list = getattr(config.style_elements, category, None)
        if category_list is None:
            raise ConfigValidationError(f"Invalid style category: {category}")
        
        if element in category_list:
            category_list.remove(element)
            self.save_config(config)
        
        return config

def test_config_loader():
    """Test the configuration loader"""
    print("Testing Emotional Configuration Loader")
    print("=" * 50)
    
    try:
        loader = EmotionalConfigLoader()
        
        # Load active config
        print("Loading active configuration...")
        config = loader.load_active_config()
        print(f"✓ Loaded {len(config.emotional_tones)} emotional tones")
        print(f"✓ Loaded {len(config.style_elements.materials)} materials")
        
        # Validate config
        print("\nValidating configuration...")
        issues = loader.validate_config(config)
        if issues:
            print("⚠ Validation issues:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("✓ Configuration is valid")
        
        # Test backup
        print("\nTesting backup functionality...")
        backup_path = loader.backup_config()
        print(f"✓ Backup created: {backup_path}")
        
        # Test reset to defaults
        print("\nTesting reset to defaults...")
        defaults = loader.reset_to_defaults()
        print(f"✓ Reset successful, version: {defaults.version}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_config_loader()