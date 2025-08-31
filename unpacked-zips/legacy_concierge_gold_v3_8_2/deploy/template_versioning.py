"""Template Versioning System for Notion Deployment.

Implements comprehensive version control for templates with:
- Semantic versioning (major.minor.patch)
- Version history tracking
- Rollback capabilities
- Migration path management
- Compatibility checking
- Change log generation
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import copy

from constants import *

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class VersionType(Enum):
    """Types of version changes."""
    MAJOR = "major"    # Breaking changes
    MINOR = "minor"    # New features, backward compatible
    PATCH = "patch"    # Bug fixes, backward compatible


class ChangeType(Enum):
    """Types of changes in templates."""
    ADDED = "added"
    MODIFIED = "modified"
    REMOVED = "removed"
    DEPRECATED = "deprecated"
    SECURITY = "security"
    FIXED = "fixed"


class TemplateVersionManager:
    """Manages template versioning and migrations."""
    
    def __init__(self, base_dir: str = "versions"):
        """Initialize version manager.
        
        Args:
            base_dir: Directory to store version history
        """
        self.base_dir = base_dir
        self.current_version = None
        self.version_history = []
        self.migration_paths = {}
        self.compatibility_matrix = {}
        self._ensure_directories()
        self._load_version_history()
    
    def _ensure_directories(self):
        """Ensure version directories exist."""
        dirs = [
            self.base_dir,
            os.path.join(self.base_dir, "snapshots"),
            os.path.join(self.base_dir, "migrations"),
            os.path.join(self.base_dir, "changelogs")
        ]
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def _load_version_history(self):
        """Load version history from disk."""
        history_file = os.path.join(self.base_dir, "version_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.version_history = data.get('history', [])
                    self.current_version = data.get('current_version')
                    self.migration_paths = data.get('migration_paths', {})
                    self.compatibility_matrix = data.get('compatibility', {})
            except Exception as e:
                logger.error(f"Error loading version history: {e}")
    
    def _save_version_history(self):
        """Save version history to disk."""
        history_file = os.path.join(self.base_dir, "version_history.json")
        data = {
            'current_version': self.current_version,
            'history': self.version_history,
            'migration_paths': self.migration_paths,
            'compatibility': self.compatibility_matrix
        }
        
        try:
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving version history: {e}")
    
    def parse_version(self, version_string: str) -> Tuple[int, int, int]:
        """Parse semantic version string.
        
        Args:
            version_string: Version in format "major.minor.patch"
            
        Returns:
            Tuple of (major, minor, patch)
        """
        try:
            parts = version_string.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid version format")
            return tuple(int(p) for p in parts)
        except Exception as e:
            logger.error(f"Error parsing version {version_string}: {e}")
            return (0, 0, 0)
    
    def format_version(self, major: int, minor: int, patch: int) -> str:
        """Format version tuple as string.
        
        Args:
            major: Major version
            minor: Minor version
            patch: Patch version
            
        Returns:
            Formatted version string
        """
        return f"{major}.{minor}.{patch}"
    
    def increment_version(self, version_type: VersionType) -> str:
        """Increment version based on change type.
        
        Args:
            version_type: Type of version increment
            
        Returns:
            New version string
        """
        if not self.current_version:
            self.current_version = "1.0.0"
            return self.current_version
        
        major, minor, patch = self.parse_version(self.current_version)
        
        if version_type == VersionType.MAJOR:
            major += 1
            minor = 0
            patch = 0
        elif version_type == VersionType.MINOR:
            minor += 1
            patch = 0
        elif version_type == VersionType.PATCH:
            patch += 1
        
        new_version = self.format_version(major, minor, patch)
        return new_version
    
    def create_version(self, template_data: Dict[str, Any], 
                      version_type: VersionType,
                      changes: List[Dict[str, Any]],
                      author: str = "system") -> Dict[str, Any]:
        """Create a new version of the template.
        
        Args:
            template_data: Template configuration data
            version_type: Type of version change
            changes: List of changes made
            author: Author of the changes
            
        Returns:
            Version creation results
        """
        # Generate new version number
        new_version = self.increment_version(version_type)
        
        # Calculate template hash
        template_hash = self._calculate_hash(template_data)
        
        # Create version snapshot
        snapshot_path = os.path.join(
            self.base_dir, "snapshots", f"v{new_version}.json"
        )
        
        version_entry = {
            'version': new_version,
            'previous_version': self.current_version,
            'created_at': datetime.now().isoformat(),
            'author': author,
            'type': version_type.value,
            'hash': template_hash,
            'changes': changes,
            'snapshot_path': snapshot_path
        }
        
        # Save snapshot
        try:
            with open(snapshot_path, 'w') as f:
                json.dump({
                    'version': new_version,
                    'metadata': version_entry,
                    'template': template_data
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving version snapshot: {e}")
            return {'error': str(e)}
        
        # Generate changelog
        self._generate_changelog(new_version, changes)
        
        # Update version history
        self.version_history.append(version_entry)
        self.current_version = new_version
        
        # Create migration if needed
        if self.version_history and len(self.version_history) > 1:
            self._create_migration(
                self.version_history[-2]['version'],
                new_version,
                changes
            )
        
        # Update compatibility matrix
        self._update_compatibility(new_version, version_type)
        
        # Save updated history
        self._save_version_history()
        
        logger.info(f"Created version {new_version}")
        
        return {
            'version': new_version,
            'snapshot_path': snapshot_path,
            'changes_count': len(changes)
        }
    
    def _calculate_hash(self, data: Any) -> str:
        """Calculate hash of template data.
        
        Args:
            data: Template data
            
        Returns:
            SHA256 hash string
        """
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def _generate_changelog(self, version: str, changes: List[Dict[str, Any]]):
        """Generate changelog for version.
        
        Args:
            version: Version number
            changes: List of changes
        """
        changelog_path = os.path.join(
            self.base_dir, "changelogs", f"CHANGELOG_v{version}.md"
        )
        
        with open(changelog_path, 'w') as f:
            f.write(f"# Changelog for Version {version}\n\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Group changes by type
            grouped = {}
            for change in changes:
                change_type = change.get('type', ChangeType.MODIFIED.value)
                if change_type not in grouped:
                    grouped[change_type] = []
                grouped[change_type].append(change)
            
            # Write grouped changes
            for change_type in [ChangeType.ADDED, ChangeType.MODIFIED, 
                               ChangeType.REMOVED, ChangeType.DEPRECATED,
                               ChangeType.SECURITY, ChangeType.FIXED]:
                if change_type.value in grouped:
                    f.write(f"\n## {change_type.value.title()}\n\n")
                    for change in grouped[change_type.value]:
                        f.write(f"- {change.get('description', 'No description')}\n")
                        if 'details' in change:
                            f.write(f"  - Details: {change['details']}\n")
    
    def _create_migration(self, from_version: str, to_version: str, 
                         changes: List[Dict[str, Any]]):
        """Create migration path between versions.
        
        Args:
            from_version: Source version
            to_version: Target version
            changes: Changes between versions
        """
        migration_key = f"{from_version}_to_{to_version}"
        migration_path = os.path.join(
            self.base_dir, "migrations", f"migrate_{migration_key}.json"
        )
        
        migration = {
            'from_version': from_version,
            'to_version': to_version,
            'created_at': datetime.now().isoformat(),
            'changes': changes,
            'steps': self._generate_migration_steps(changes)
        }
        
        try:
            with open(migration_path, 'w') as f:
                json.dump(migration, f, indent=2)
            
            # Update migration paths
            if from_version not in self.migration_paths:
                self.migration_paths[from_version] = {}
            self.migration_paths[from_version][to_version] = migration_path
            
        except Exception as e:
            logger.error(f"Error creating migration: {e}")
    
    def _generate_migration_steps(self, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate migration steps from changes.
        
        Args:
            changes: List of changes
            
        Returns:
            List of migration steps
        """
        steps = []
        
        for change in changes:
            change_type = change.get('type', ChangeType.MODIFIED.value)
            
            if change_type == ChangeType.ADDED.value:
                steps.append({
                    'action': 'add',
                    'target': change.get('target'),
                    'data': change.get('data')
                })
            elif change_type == ChangeType.REMOVED.value:
                steps.append({
                    'action': 'remove',
                    'target': change.get('target')
                })
            elif change_type == ChangeType.MODIFIED.value:
                steps.append({
                    'action': 'modify',
                    'target': change.get('target'),
                    'old_data': change.get('old_data'),
                    'new_data': change.get('new_data')
                })
        
        return steps
    
    def _update_compatibility(self, version: str, version_type: VersionType):
        """Update compatibility matrix for new version.
        
        Args:
            version: New version
            version_type: Type of version change
        """
        if version not in self.compatibility_matrix:
            self.compatibility_matrix[version] = {
                'backward_compatible': [],
                'forward_compatible': [],
                'breaking_changes': version_type == VersionType.MAJOR
            }
        
        # Determine compatibility based on version type
        if version_type == VersionType.PATCH:
            # Patch versions are compatible with same minor version
            for v in self.version_history:
                v_major, v_minor, _ = self.parse_version(v['version'])
                new_major, new_minor, _ = self.parse_version(version)
                if v_major == new_major and v_minor == new_minor:
                    self.compatibility_matrix[version]['backward_compatible'].append(v['version'])
        
        elif version_type == VersionType.MINOR:
            # Minor versions are backward compatible with same major version
            for v in self.version_history:
                v_major, _, _ = self.parse_version(v['version'])
                new_major, _, _ = self.parse_version(version)
                if v_major == new_major:
                    self.compatibility_matrix[version]['backward_compatible'].append(v['version'])
    
    def get_version(self, version: str) -> Optional[Dict[str, Any]]:
        """Get specific version data.
        
        Args:
            version: Version to retrieve
            
        Returns:
            Version data or None
        """
        snapshot_path = os.path.join(
            self.base_dir, "snapshots", f"v{version}.json"
        )
        
        if os.path.exists(snapshot_path):
            try:
                with open(snapshot_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading version {version}: {e}")
        
        return None
    
    def rollback_to_version(self, target_version: str) -> Dict[str, Any]:
        """Rollback to a specific version.
        
        Args:
            target_version: Version to rollback to
            
        Returns:
            Rollback results
        """
        # Get target version data
        version_data = self.get_version(target_version)
        if not version_data:
            return {'error': f'Version {target_version} not found'}
        
        # Create backup of current version
        if self.current_version:
            backup_version = f"{self.current_version}_rollback_backup"
            current_data = self.get_version(self.current_version)
            if current_data:
                backup_path = os.path.join(
                    self.base_dir, "snapshots", f"v{backup_version}.json"
                )
                with open(backup_path, 'w') as f:
                    json.dump(current_data, f, indent=2)
        
        # Update current version
        self.current_version = target_version
        self._save_version_history()
        
        logger.info(f"Rolled back to version {target_version}")
        
        return {
            'rolled_back_to': target_version,
            'previous_version': backup_version if self.current_version else None,
            'template_data': version_data.get('template')
        }
    
    def get_migration_path(self, from_version: str, to_version: str) -> List[str]:
        """Find migration path between versions.
        
        Args:
            from_version: Starting version
            to_version: Target version
            
        Returns:
            List of versions in migration path
        """
        # Simple BFS to find path
        if from_version == to_version:
            return [from_version]
        
        visited = set()
        queue = [(from_version, [from_version])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current in visited:
                continue
            visited.add(current)
            
            # Check direct migrations
            if current in self.migration_paths:
                for next_version in self.migration_paths[current]:
                    if next_version == to_version:
                        return path + [to_version]
                    queue.append((next_version, path + [next_version]))
        
        return []  # No path found
    
    def check_compatibility(self, version1: str, version2: str) -> Dict[str, bool]:
        """Check compatibility between two versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Compatibility information
        """
        v1_major, v1_minor, v1_patch = self.parse_version(version1)
        v2_major, v2_minor, v2_patch = self.parse_version(version2)
        
        return {
            'compatible': v1_major == v2_major,  # Same major version
            'backward_compatible': (v1_major == v2_major and v1_minor <= v2_minor),
            'forward_compatible': (v1_major == v2_major and v1_minor >= v2_minor),
            'requires_migration': v1_major != v2_major or v1_minor != v2_minor
        }
    
    def get_version_diff(self, version1: str, version2: str) -> Dict[str, Any]:
        """Get differences between two versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            Differences between versions
        """
        data1 = self.get_version(version1)
        data2 = self.get_version(version2)
        
        if not data1 or not data2:
            return {'error': 'One or both versions not found'}
        
        template1 = data1.get('template', {})
        template2 = data2.get('template', {})
        
        # Find differences
        added = []
        modified = []
        removed = []
        
        # Check for added/modified
        for key in template2:
            if key not in template1:
                added.append(key)
            elif template1[key] != template2[key]:
                modified.append(key)
        
        # Check for removed
        for key in template1:
            if key not in template2:
                removed.append(key)
        
        return {
            'version1': version1,
            'version2': version2,
            'added': added,
            'modified': modified,
            'removed': removed,
            'total_changes': len(added) + len(modified) + len(removed)
        }


def setup_template_versioning(state: Dict[str, Any], 
                             template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for template versioning.
    
    Args:
        state: Current deployment state
        template_data: Template configuration data
        
    Returns:
        Versioning setup results
    """
    manager = TemplateVersionManager()
    
    # Check if this is first version
    if not manager.current_version:
        # Create initial version
        changes = [{
            'type': ChangeType.ADDED.value,
            'description': 'Initial template version',
            'target': 'template',
            'data': template_data
        }]
        
        result = manager.create_version(
            template_data,
            VersionType.MAJOR,
            changes,
            author='system'
        )
        
        logger.info(f"Created initial version: {result['version']}")
    else:
        # Detect changes from current version
        current_data = manager.get_version(manager.current_version)
        if current_data:
            diff = manager.get_version_diff(
                manager.current_version,
                'working'  # Placeholder for working changes
            )
            
            if diff['total_changes'] > 0:
                # Determine version type based on changes
                version_type = VersionType.PATCH
                if diff['removed'] or len(diff['added']) > 5:
                    version_type = VersionType.MINOR
                if 'breaking' in str(diff).lower():
                    version_type = VersionType.MAJOR
                
                # Create change list
                changes = []
                for item in diff['added']:
                    changes.append({
                        'type': ChangeType.ADDED.value,
                        'description': f'Added {item}',
                        'target': item
                    })
                for item in diff['modified']:
                    changes.append({
                        'type': ChangeType.MODIFIED.value,
                        'description': f'Modified {item}',
                        'target': item
                    })
                for item in diff['removed']:
                    changes.append({
                        'type': ChangeType.REMOVED.value,
                        'description': f'Removed {item}',
                        'target': item
                    })
                
                # Create new version
                result = manager.create_version(
                    template_data,
                    version_type,
                    changes,
                    author='system'
                )
                
                logger.info(f"Created version: {result['version']}")
    
    # Store manager in state
    state['version_manager'] = manager
    state['current_version'] = manager.current_version
    
    return {
        'current_version': manager.current_version,
        'version_count': len(manager.version_history),
        'has_migrations': len(manager.migration_paths) > 0
    }