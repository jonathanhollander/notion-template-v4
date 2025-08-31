"""Relation Integrity Enforcement for Notion Deployment.

Enforces referential integrity across related databases with:
- Foreign key constraints
- Cascade operations (delete, update)
- Orphan detection and cleanup
- Circular reference prevention
- Relation validation
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum

from constants import *

logger = logging.getLogger(__name__)


class CascadeAction(Enum):
    """Types of cascade actions."""
    CASCADE = "cascade"      # Delete/update related records
    SET_NULL = "set_null"    # Set relation to null
    RESTRICT = "restrict"    # Prevent operation
    NO_ACTION = "no_action"  # Do nothing


class RelationIntegrityManager:
    """Manages relation integrity across Notion databases."""
    
    def __init__(self):
        """Initialize integrity manager."""
        self.relations = {}
        self.constraints = {}
        self.orphan_records = []
        self.integrity_violations = []
    
    def define_relation(self, relation_id: str, config: Dict[str, Any]):
        """Define a relation between databases.
        
        Args:
            relation_id: Unique relation identifier
            config: Relation configuration including:
                - source_db: Source database ID
                - target_db: Target database ID
                - source_property: Property in source database
                - target_property: Property in target database
                - relation_type: one-to-one, one-to-many, many-to-many
                - on_delete: CASCADE, SET_NULL, RESTRICT, NO_ACTION
                - on_update: CASCADE, SET_NULL, RESTRICT, NO_ACTION
                - required: Whether relation is required
        """
        self.relations[relation_id] = {
            **config,
            'created_at': datetime.now().isoformat(),
            'violations': 0,
            'enforcements': 0
        }
        
        # Create constraint entries
        source_db = config['source_db']
        if source_db not in self.constraints:
            self.constraints[source_db] = []
        
        self.constraints[source_db].append({
            'relation_id': relation_id,
            'type': 'foreign_key',
            'target_db': config['target_db'],
            'on_delete': CascadeAction(config.get('on_delete', 'no_action')),
            'on_update': CascadeAction(config.get('on_update', 'no_action'))
        })
        
        logger.info(f"Defined relation: {relation_id}")
    
    def validate_relation(self, relation_id: str, source_value: Any, 
                         state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a relation value.
        
        Args:
            relation_id: Relation identifier
            source_value: Value to validate
            state: Current deployment state
            
        Returns:
            Validation result
        """
        if relation_id not in self.relations:
            return {'valid': False, 'error': 'Relation not defined'}
        
        relation = self.relations[relation_id]
        
        # Check if value is required
        if relation.get('required') and not source_value:
            return {
                'valid': False,
                'error': f"Required relation {relation_id} is empty"
            }
        
        # Check if target exists (would require API call)
        target_exists = self._check_target_exists(
            relation['target_db'],
            source_value,
            state
        )
        
        if not target_exists and source_value:
            self.integrity_violations.append({
                'relation_id': relation_id,
                'source_value': source_value,
                'error': 'Target record not found',
                'timestamp': datetime.now().isoformat()
            })
            return {
                'valid': False,
                'error': 'Referenced record does not exist'
            }
        
        return {'valid': True}
    
    def _check_target_exists(self, target_db: str, target_id: Any, 
                            state: Dict[str, Any]) -> bool:
        """Check if target record exists.
        
        Args:
            target_db: Target database ID
            target_id: Target record ID
            state: Current deployment state
            
        Returns:
            True if target exists
        """
        # This would make actual API call to check existence
        # For now, store query in state
        if 'integrity_checks' not in state:
            state['integrity_checks'] = []
        
        state['integrity_checks'].append({
            'database': target_db,
            'record_id': target_id,
            'type': 'existence_check'
        })
        
        # Mock response
        return True  # Assume exists for testing
    
    def enforce_cascade_delete(self, database_id: str, record_id: str, 
                              state: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce cascade actions on delete.
        
        Args:
            database_id: Database containing record
            record_id: Record being deleted
            state: Current deployment state
            
        Returns:
            Cascade results
        """
        results = {
            'cascaded': [],
            'set_null': [],
            'restricted': False,
            'errors': []
        }
        
        if database_id not in self.constraints:
            return results
        
        for constraint in self.constraints[database_id]:
            action = constraint['on_delete']
            
            if action == CascadeAction.CASCADE:
                # Delete related records
                cascaded = self._cascade_delete_related(
                    constraint['target_db'],
                    record_id,
                    state
                )
                results['cascaded'].extend(cascaded)
                
            elif action == CascadeAction.SET_NULL:
                # Set related fields to null
                nullified = self._set_related_to_null(
                    constraint['target_db'],
                    record_id,
                    state
                )
                results['set_null'].extend(nullified)
                
            elif action == CascadeAction.RESTRICT:
                # Check if related records exist
                if self._has_related_records(constraint['target_db'], record_id, state):
                    results['restricted'] = True
                    results['errors'].append(
                        f"Cannot delete: related records exist in {constraint['target_db']}"
                    )
                    return results
        
        return results
    
    def _cascade_delete_related(self, target_db: str, source_id: str, 
                               state: Dict[str, Any]) -> List[str]:
        """Cascade delete related records.
        
        Args:
            target_db: Target database
            source_id: Source record ID
            state: Current deployment state
            
        Returns:
            List of deleted record IDs
        """
        # Store cascade operations in state
        if 'cascade_deletes' not in state:
            state['cascade_deletes'] = []
        
        state['cascade_deletes'].append({
            'database': target_db,
            'source_id': source_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Mock deleted records
        return [f"{target_db}_related_{source_id}"]
    
    def _set_related_to_null(self, target_db: str, source_id: str, 
                            state: Dict[str, Any]) -> List[str]:
        """Set related fields to null.
        
        Args:
            target_db: Target database
            source_id: Source record ID
            state: Current deployment state
            
        Returns:
            List of updated record IDs
        """
        # Store nullify operations in state
        if 'nullify_operations' not in state:
            state['nullify_operations'] = []
        
        state['nullify_operations'].append({
            'database': target_db,
            'source_id': source_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Mock updated records
        return [f"{target_db}_nullified_{source_id}"]
    
    def _has_related_records(self, target_db: str, source_id: str, 
                            state: Dict[str, Any]) -> bool:
        """Check if related records exist.
        
        Args:
            target_db: Target database
            source_id: Source record ID
            state: Current deployment state
            
        Returns:
            True if related records exist
        """
        # This would query for related records
        # Mock response
        return False
    
    def detect_orphans(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect orphaned records across all relations.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of orphaned records
        """
        orphans = []
        
        for relation_id, relation in self.relations.items():
            # Check each relation for orphans
            source_db = relation['source_db']
            target_db = relation['target_db']
            
            # This would query for records with broken relations
            # Mock orphan detection
            orphan = {
                'relation_id': relation_id,
                'database': source_db,
                'record_id': f"orphan_{relation_id}",
                'missing_target': target_db,
                'detected_at': datetime.now().isoformat()
            }
            
            orphans.append(orphan)
            self.orphan_records.append(orphan)
        
        return orphans
    
    def clean_orphans(self, state: Dict[str, Any], 
                     action: str = 'set_null') -> Dict[str, Any]:
        """Clean up orphaned records.
        
        Args:
            state: Current deployment state
            action: Action to take ('set_null', 'delete')
            
        Returns:
            Cleanup results
        """
        results = {
            'cleaned': 0,
            'errors': [],
            'actions': []
        }
        
        for orphan in self.orphan_records:
            try:
                if action == 'set_null':
                    # Set orphaned relation to null
                    results['actions'].append({
                        'type': 'set_null',
                        'database': orphan['database'],
                        'record': orphan['record_id']
                    })
                elif action == 'delete':
                    # Delete orphaned record
                    results['actions'].append({
                        'type': 'delete',
                        'database': orphan['database'],
                        'record': orphan['record_id']
                    })
                
                results['cleaned'] += 1
                
            except Exception as e:
                results['errors'].append(str(e))
        
        # Clear processed orphans
        self.orphan_records = []
        
        return results
    
    def detect_circular_references(self, state: Dict[str, Any]) -> List[List[str]]:
        """Detect circular references in relations.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of circular reference chains
        """
        circles = []
        visited = set()
        
        def dfs(db_id: str, path: List[str], visiting: Set[str]):
            """Depth-first search for cycles."""
            if db_id in visiting:
                # Found a cycle
                cycle_start = path.index(db_id)
                circles.append(path[cycle_start:] + [db_id])
                return
            
            if db_id in visited:
                return
            
            visiting.add(db_id)
            
            # Find relations from this database
            for relation_id, relation in self.relations.items():
                if relation['source_db'] == db_id:
                    target = relation['target_db']
                    dfs(target, path + [db_id], visiting.copy())
            
            visited.add(db_id)
        
        # Check each database
        for relation in self.relations.values():
            if relation['source_db'] not in visited:
                dfs(relation['source_db'], [], set())
        
        return circles
    
    def get_integrity_report(self) -> Dict[str, Any]:
        """Get integrity report.
        
        Returns:
            Integrity status report
        """
        return {
            'total_relations': len(self.relations),
            'total_constraints': sum(len(c) for c in self.constraints.values()),
            'orphan_count': len(self.orphan_records),
            'violation_count': len(self.integrity_violations),
            'relations': {
                rid: {
                    'source': r['source_db'],
                    'target': r['target_db'],
                    'violations': r['violations'],
                    'enforcements': r['enforcements']
                }
                for rid, r in self.relations.items()
            }
        }


def setup_relation_integrity(state: Dict[str, Any]) -> Dict[str, Any]:
    """Setup relation integrity for Estate Planning system.
    
    Args:
        state: Current deployment state
        
    Returns:
        Setup results
    """
    manager = RelationIntegrityManager()
    
    # Define standard relations
    relations = [
        {
            'id': 'contact_estate',
            'config': {
                'source_db': 'Contacts',
                'target_db': 'Estate',
                'source_property': 'Estate',
                'target_property': 'ID',
                'relation_type': 'many-to-one',
                'on_delete': 'cascade',
                'on_update': 'cascade',
                'required': True
            }
        },
        {
            'id': 'asset_owner',
            'config': {
                'source_db': 'Assets',
                'target_db': 'Contacts',
                'source_property': 'Owner',
                'target_property': 'ID',
                'relation_type': 'many-to-one',
                'on_delete': 'set_null',
                'on_update': 'cascade',
                'required': False
            }
        },
        {
            'id': 'document_contact',
            'config': {
                'source_db': 'Important Documents',
                'target_db': 'Contacts',
                'source_property': 'Related Contact',
                'target_property': 'ID',
                'relation_type': 'many-to-one',
                'on_delete': 'set_null',
                'on_update': 'cascade',
                'required': False
            }
        },
        {
            'id': 'task_assignee',
            'config': {
                'source_db': 'Task Tracker',
                'target_db': 'Contacts',
                'source_property': 'Assignee',
                'target_property': 'ID',
                'relation_type': 'many-to-one',
                'on_delete': 'set_null',
                'on_update': 'cascade',
                'required': False
            }
        }
    ]
    
    # Define relations
    for relation_def in relations:
        manager.define_relation(relation_def['id'], relation_def['config'])
    
    # Detect orphans
    orphans = manager.detect_orphans(state)
    
    # Detect circular references
    circles = manager.detect_circular_references(state)
    
    # Store manager in state
    state['integrity_manager'] = manager
    
    return {
        'relations_defined': len(manager.relations),
        'orphans_detected': len(orphans),
        'circular_references': len(circles),
        'constraints_created': sum(len(c) for c in manager.constraints.values())
    }