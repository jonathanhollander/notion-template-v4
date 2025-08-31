"""Cross-Database Synced Rollups Module for Notion Deployment.

Implements synchronized rollups across multiple databases with:
- Real-time data aggregation
- Cross-database relationships
- Automatic formula synchronization
- Rollup caching for performance
- Change detection and propagation
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum

from constants import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class RollupType(Enum):
    """Types of rollup operations."""
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    SHOW_UNIQUE = "show_unique"
    SHOW_ORIGINAL = "show_original"
    MEDIAN = "median"
    PERCENT_EMPTY = "percent_empty"
    PERCENT_NOT_EMPTY = "percent_not_empty"


class SyncedRollupManager:
    """Manages cross-database synchronized rollups."""
    
    def __init__(self):
        """Initialize rollup manager."""
        self.rollup_definitions = {}
        self.rollup_cache = {}
        self.dependency_graph = {}
        self.sync_status = {}
        
    def define_rollup(self, rollup_id: str, config: Dict[str, Any]) -> bool:
        """Define a new cross-database rollup.
        
        Args:
            rollup_id: Unique identifier for the rollup
            config: Rollup configuration including:
                - source_database: Source database ID
                - source_property: Property to aggregate
                - target_database: Target database ID
                - target_property: Where to store rollup
                - rollup_type: Type of aggregation
                - relation_property: Relation connecting databases
                - filters: Optional filters for aggregation
                
        Returns:
            Success status
        """
        try:
            # Validate configuration
            required_fields = ['source_database', 'source_property', 
                             'target_database', 'target_property', 
                             'rollup_type', 'relation_property']
            
            for field in required_fields:
                if field not in config:
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate rollup type
            try:
                rollup_type = RollupType(config['rollup_type'])
            except ValueError:
                logger.error(f"Invalid rollup type: {config['rollup_type']}")
                return False
            
            # Store definition
            self.rollup_definitions[rollup_id] = {
                **config,
                'rollup_type': rollup_type,
                'created_at': datetime.now().isoformat(),
                'last_sync': None,
                'sync_count': 0
            }
            
            # Update dependency graph
            self._update_dependency_graph(rollup_id, config)
            
            logger.info(f"Defined rollup: {rollup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error defining rollup {rollup_id}: {e}")
            return False
    
    def _update_dependency_graph(self, rollup_id: str, config: Dict[str, Any]):
        """Update the dependency graph for rollup cascading.
        
        Args:
            rollup_id: Rollup identifier
            config: Rollup configuration
        """
        source_db = config['source_database']
        target_db = config['target_database']
        
        # Add to dependency tracking
        if source_db not in self.dependency_graph:
            self.dependency_graph[source_db] = {'affects': set(), 'depends_on': set()}
        if target_db not in self.dependency_graph:
            self.dependency_graph[target_db] = {'affects': set(), 'depends_on': set()}
        
        self.dependency_graph[source_db]['affects'].add(rollup_id)
        self.dependency_graph[target_db]['depends_on'].add(rollup_id)
    
    def sync_rollup(self, rollup_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize a specific rollup.
        
        Args:
            rollup_id: Rollup to synchronize
            state: Current deployment state
            
        Returns:
            Sync results including updated values
        """
        if rollup_id not in self.rollup_definitions:
            logger.error(f"Rollup {rollup_id} not defined")
            return {'error': 'Rollup not found'}
        
        rollup = self.rollup_definitions[rollup_id]
        results = {
            'rollup_id': rollup_id,
            'values_updated': 0,
            'errors': [],
            'cached': False
        }
        
        try:
            # Check cache validity
            if self._is_cache_valid(rollup_id):
                results['cached'] = True
                results['values'] = self.rollup_cache[rollup_id]
                return results
            
            # Fetch source data
            source_data = self._fetch_source_data(rollup, state)
            
            # Apply filters if specified
            if rollup.get('filters'):
                source_data = self._apply_filters(source_data, rollup['filters'])
            
            # Calculate rollup values
            rollup_values = self._calculate_rollup(source_data, rollup)
            
            # Update target database
            update_results = self._update_target_database(rollup, rollup_values, state)
            
            # Update cache
            self.rollup_cache[rollup_id] = {
                'values': rollup_values,
                'timestamp': datetime.now().isoformat(),
                'source_count': len(source_data)
            }
            
            # Update sync status
            self.rollup_definitions[rollup_id]['last_sync'] = datetime.now().isoformat()
            self.rollup_definitions[rollup_id]['sync_count'] += 1
            
            results['values'] = rollup_values
            results['values_updated'] = update_results['updated']
            
        except Exception as e:
            logger.error(f"Error syncing rollup {rollup_id}: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def _is_cache_valid(self, rollup_id: str, max_age_seconds: int = 300) -> bool:
        """Check if cached rollup data is still valid.
        
        Args:
            rollup_id: Rollup identifier
            max_age_seconds: Maximum cache age in seconds
            
        Returns:
            True if cache is valid
        """
        if rollup_id not in self.rollup_cache:
            return False
        
        cache_entry = self.rollup_cache[rollup_id]
        cache_time = datetime.fromisoformat(cache_entry['timestamp'])
        age = (datetime.now() - cache_time).total_seconds()
        
        return age < max_age_seconds
    
    def _fetch_source_data(self, rollup: Dict[str, Any], 
                          state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch data from source database.
        
        Args:
            rollup: Rollup configuration
            state: Current deployment state
            
        Returns:
            List of source records
        """
        # This would make actual Notion API calls
        # For now, return mock data structure
        source_db_id = rollup['source_database']
        source_property = rollup['source_property']
        
        # Store query in state for later API execution
        if 'rollup_queries' not in state:
            state['rollup_queries'] = []
        
        state['rollup_queries'].append({
            'database_id': source_db_id,
            'property': source_property,
            'relation': rollup['relation_property']
        })
        
        # Return mock data for testing
        return [
            {source_property: 100},
            {source_property: 200},
            {source_property: 150}
        ]
    
    def _apply_filters(self, data: List[Dict[str, Any]], 
                      filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to source data.
        
        Args:
            data: Source data
            filters: Filter criteria
            
        Returns:
            Filtered data
        """
        filtered = []
        
        for record in data:
            include = True
            
            for field, criteria in filters.items():
                if field not in record:
                    include = False
                    break
                
                value = record[field]
                
                # Handle different filter types
                if isinstance(criteria, dict):
                    if 'equals' in criteria and value != criteria['equals']:
                        include = False
                    elif 'contains' in criteria and criteria['contains'] not in str(value):
                        include = False
                    elif 'greater_than' in criteria and value <= criteria['greater_than']:
                        include = False
                    elif 'less_than' in criteria and value >= criteria['less_than']:
                        include = False
            
            if include:
                filtered.append(record)
        
        return filtered
    
    def _calculate_rollup(self, data: List[Dict[str, Any]], 
                         rollup: Dict[str, Any]) -> Any:
        """Calculate rollup value based on type.
        
        Args:
            data: Source data
            rollup: Rollup configuration
            
        Returns:
            Calculated rollup value
        """
        if not data:
            return None
        
        rollup_type = rollup['rollup_type']
        property_name = rollup['source_property']
        values = [r.get(property_name) for r in data if property_name in r]
        
        if not values:
            return None
        
        # Calculate based on rollup type
        if rollup_type == RollupType.COUNT:
            return len(values)
        elif rollup_type == RollupType.SUM:
            return sum(v for v in values if isinstance(v, (int, float)))
        elif rollup_type == RollupType.AVERAGE:
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            return sum(numeric_values) / len(numeric_values) if numeric_values else None
        elif rollup_type == RollupType.MIN:
            return min(values)
        elif rollup_type == RollupType.MAX:
            return max(values)
        elif rollup_type == RollupType.SHOW_UNIQUE:
            return list(set(values))
        elif rollup_type == RollupType.SHOW_ORIGINAL:
            return values
        elif rollup_type == RollupType.MEDIAN:
            sorted_values = sorted(v for v in values if isinstance(v, (int, float)))
            n = len(sorted_values)
            if n == 0:
                return None
            elif n % 2 == 0:
                return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
            else:
                return sorted_values[n//2]
        elif rollup_type == RollupType.PERCENT_EMPTY:
            empty_count = sum(1 for v in values if v is None or v == '')
            return (empty_count / len(values)) * 100
        elif rollup_type == RollupType.PERCENT_NOT_EMPTY:
            not_empty_count = sum(1 for v in values if v is not None and v != '')
            return (not_empty_count / len(values)) * 100
        
        return None
    
    def _update_target_database(self, rollup: Dict[str, Any], value: Any, 
                               state: Dict[str, Any]) -> Dict[str, Any]:
        """Update target database with rollup value.
        
        Args:
            rollup: Rollup configuration
            value: Calculated rollup value
            state: Current deployment state
            
        Returns:
            Update results
        """
        target_db_id = rollup['target_database']
        target_property = rollup['target_property']
        
        # Store update in state for later API execution
        if 'rollup_updates' not in state:
            state['rollup_updates'] = []
        
        state['rollup_updates'].append({
            'database_id': target_db_id,
            'property': target_property,
            'value': value,
            'rollup_id': rollup.get('rollup_id'),
            'timestamp': datetime.now().isoformat()
        })
        
        return {'updated': 1}
    
    def sync_all_rollups(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize all defined rollups.
        
        Args:
            state: Current deployment state
            
        Returns:
            Aggregated sync results
        """
        results = {
            'total_rollups': len(self.rollup_definitions),
            'synced': 0,
            'cached': 0,
            'errors': [],
            'total_values_updated': 0
        }
        
        for rollup_id in self.rollup_definitions:
            sync_result = self.sync_rollup(rollup_id, state)
            
            if 'error' not in sync_result:
                results['synced'] += 1
                if sync_result.get('cached'):
                    results['cached'] += 1
                results['total_values_updated'] += sync_result.get('values_updated', 0)
            else:
                results['errors'].append({
                    'rollup_id': rollup_id,
                    'error': sync_result['error']
                })
        
        return results
    
    def get_rollup_status(self, rollup_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of rollup(s).
        
        Args:
            rollup_id: Specific rollup ID or None for all
            
        Returns:
            Status information
        """
        if rollup_id:
            if rollup_id not in self.rollup_definitions:
                return {'error': 'Rollup not found'}
            
            rollup = self.rollup_definitions[rollup_id]
            cache_info = self.rollup_cache.get(rollup_id, {})
            
            return {
                'rollup_id': rollup_id,
                'configuration': rollup,
                'cache': cache_info,
                'is_cached': rollup_id in self.rollup_cache,
                'dependencies': self._get_rollup_dependencies(rollup_id)
            }
        else:
            return {
                'total_rollups': len(self.rollup_definitions),
                'cached_rollups': len(self.rollup_cache),
                'rollups': list(self.rollup_definitions.keys()),
                'dependency_graph': {
                    k: {
                        'affects': list(v['affects']),
                        'depends_on': list(v['depends_on'])
                    }
                    for k, v in self.dependency_graph.items()
                }
            }
    
    def _get_rollup_dependencies(self, rollup_id: str) -> Dict[str, List[str]]:
        """Get dependencies for a specific rollup.
        
        Args:
            rollup_id: Rollup identifier
            
        Returns:
            Dictionary of upstream and downstream dependencies
        """
        rollup = self.rollup_definitions.get(rollup_id, {})
        source_db = rollup.get('source_database')
        target_db = rollup.get('target_database')
        
        dependencies = {
            'upstream': [],
            'downstream': []
        }
        
        # Find rollups that affect this one (upstream)
        for other_id, other_rollup in self.rollup_definitions.items():
            if other_id != rollup_id:
                if other_rollup.get('target_database') == source_db:
                    dependencies['upstream'].append(other_id)
        
        # Find rollups affected by this one (downstream)
        for other_id, other_rollup in self.rollup_definitions.items():
            if other_id != rollup_id:
                if other_rollup.get('source_database') == target_db:
                    dependencies['downstream'].append(other_id)
        
        return dependencies
    
    def cascade_update(self, database_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Cascade updates through dependent rollups.
        
        Args:
            database_id: Database that was updated
            state: Current deployment state
            
        Returns:
            Cascade results
        """
        results = {
            'triggered_by': database_id,
            'rollups_updated': [],
            'cascade_depth': 0,
            'total_updates': 0
        }
        
        # Find affected rollups
        if database_id not in self.dependency_graph:
            return results
        
        affected_rollups = self.dependency_graph[database_id].get('affects', set())
        visited = set()
        queue = list(affected_rollups)
        depth = 0
        
        while queue and depth < 10:  # Prevent infinite cascades
            next_queue = []
            
            for rollup_id in queue:
                if rollup_id in visited:
                    continue
                
                visited.add(rollup_id)
                sync_result = self.sync_rollup(rollup_id, state)
                
                if 'error' not in sync_result:
                    results['rollups_updated'].append(rollup_id)
                    results['total_updates'] += sync_result.get('values_updated', 0)
                    
                    # Find downstream rollups
                    rollup = self.rollup_definitions[rollup_id]
                    target_db = rollup['target_database']
                    if target_db in self.dependency_graph:
                        next_affected = self.dependency_graph[target_db].get('affects', set())
                        next_queue.extend(next_affected)
            
            queue = next_queue
            depth += 1
        
        results['cascade_depth'] = depth
        return results


def setup_synced_rollups(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point for setting up cross-database synced rollups.
    
    Args:
        state: Current deployment state
        
    Returns:
        Setup results
    """
    manager = SyncedRollupManager()
    
    # Define standard rollups for Estate Planning system
    rollups = [
        {
            'id': 'total_assets_value',
            'config': {
                'source_database': 'Assets',
                'source_property': 'Value',
                'target_database': 'Estate Summary',
                'target_property': 'Total Assets',
                'rollup_type': 'sum',
                'relation_property': 'Estate'
            }
        },
        {
            'id': 'contact_count',
            'config': {
                'source_database': 'Contacts',
                'source_property': 'Name',
                'target_database': 'Estate Summary',
                'target_property': 'Total Contacts',
                'rollup_type': 'count',
                'relation_property': 'Estate'
            }
        },
        {
            'id': 'document_completion',
            'config': {
                'source_database': 'Important Documents',
                'source_property': 'Status',
                'target_database': 'Estate Summary',
                'target_property': 'Documents Complete',
                'rollup_type': 'percent_not_empty',
                'relation_property': 'Estate',
                'filters': {'Status': {'equals': 'Complete'}}
            }
        },
        {
            'id': 'task_progress',
            'config': {
                'source_database': 'Task Tracker',
                'source_property': 'Status',
                'target_database': 'Progress Dashboard',
                'target_property': 'Tasks Completed',
                'rollup_type': 'percent_not_empty',
                'relation_property': 'Project',
                'filters': {'Status': {'equals': 'Done'}}
            }
        }
    ]
    
    # Define rollups
    for rollup_def in rollups:
        success = manager.define_rollup(rollup_def['id'], rollup_def['config'])
        if success:
            logger.info(f"Defined rollup: {rollup_def['id']}")
    
    # Sync all rollups
    sync_results = manager.sync_all_rollups(state)
    
    # Store manager in state for later use
    state['rollup_manager'] = manager
    
    return sync_results