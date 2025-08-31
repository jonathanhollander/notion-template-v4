"""Formula Auto-Sync for Notion Deployment.

Implements automatic formula synchronization with:
- Formula dependency tracking
- Cross-database formula references
- Automatic formula updates on schema changes
- Formula validation and error checking
- Circular dependency detection
- Formula performance optimization
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from enum import Enum

from constants import *

logger = logging.getLogger(__name__)


class FormulaType(Enum):
    """Types of formulas."""
    SIMPLE = "simple"           # Basic calculations
    ROLLUP = "rollup"           # Aggregated from relations
    REFERENCE = "reference"     # References other properties
    CONDITIONAL = "conditional" # If-then-else logic
    DATE = "date"              # Date calculations
    TEXT = "text"              # String operations
    COMPLEX = "complex"        # Multi-step calculations


class FormulaSyncManager:
    """Manages formula synchronization across Notion databases."""
    
    def __init__(self):
        """Initialize formula sync manager."""
        self.formulas = {}
        self.dependencies = {}
        self.sync_queue = []
        self.validation_errors = []
        self.performance_metrics = {}
    
    def register_formula(self, formula_id: str, config: Dict[str, Any]):
        """Register a formula for synchronization.
        
        Args:
            formula_id: Unique formula identifier
            config: Formula configuration including:
                - database_id: Database containing the formula
                - property_name: Property name
                - expression: Formula expression
                - type: Formula type
                - dependencies: List of dependent properties
                - auto_sync: Whether to auto-sync on changes
        """
        self.formulas[formula_id] = {
            **config,
            'created_at': datetime.now().isoformat(),
            'last_sync': None,
            'sync_count': 0,
            'errors': []
        }
        
        # Build dependency graph
        self._update_dependencies(formula_id, config.get('dependencies', []))
        
        # Validate formula
        validation = self._validate_formula(config['expression'])
        if not validation['valid']:
            self.validation_errors.append({
                'formula_id': formula_id,
                'errors': validation['errors'],
                'timestamp': datetime.now().isoformat()
            })
        
        logger.info(f"Registered formula: {formula_id}")
    
    def _update_dependencies(self, formula_id: str, dependencies: List[str]):
        """Update formula dependency graph.
        
        Args:
            formula_id: Formula identifier
            dependencies: List of dependent property IDs
        """
        self.dependencies[formula_id] = dependencies
        
        # Check for circular dependencies
        if self._has_circular_dependency(formula_id):
            logger.warning(f"Circular dependency detected for formula: {formula_id}")
            self.validation_errors.append({
                'formula_id': formula_id,
                'error': 'Circular dependency detected',
                'timestamp': datetime.now().isoformat()
            })
    
    def _has_circular_dependency(self, formula_id: str, 
                                visited: Optional[Set[str]] = None) -> bool:
        """Check for circular dependencies.
        
        Args:
            formula_id: Formula to check
            visited: Set of visited formulas
            
        Returns:
            True if circular dependency exists
        """
        if visited is None:
            visited = set()
        
        if formula_id in visited:
            return True
        
        visited.add(formula_id)
        
        for dep in self.dependencies.get(formula_id, []):
            if self._has_circular_dependency(dep, visited.copy()):
                return True
        
        return False
    
    def _validate_formula(self, expression: str) -> Dict[str, Any]:
        """Validate a formula expression.
        
        Args:
            expression: Formula expression
            
        Returns:
            Validation result
        """
        errors = []
        
        # Check for basic syntax errors
        if not expression:
            errors.append("Empty formula expression")
        
        # Check parentheses balance
        paren_count = 0
        for char in expression:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            if paren_count < 0:
                errors.append("Unmatched closing parenthesis")
                break
        if paren_count != 0:
            errors.append("Unmatched parentheses")
        
        # Check for common Notion formula functions
        valid_functions = [
            'prop', 'if', 'and', 'or', 'not', 'empty', 'length',
            'concat', 'join', 'slice', 'contains', 'test', 'replace',
            'replaceAll', 'lower', 'upper', 'format', 'toNumber',
            'round', 'ceil', 'floor', 'abs', 'sign', 'sqrt', 'pow',
            'mod', 'min', 'max', 'now', 'today', 'dateAdd', 'dateSubtract',
            'dateBetween', 'formatDate', 'timestamp', 'fromTimestamp'
        ]
        
        # Extract function calls from expression
        function_pattern = r'\b([a-zA-Z]+)\s*\('
        found_functions = re.findall(function_pattern, expression)
        
        for func in found_functions:
            if func not in valid_functions:
                logger.warning(f"Unknown function in formula: {func}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def sync_formula(self, formula_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize a single formula.
        
        Args:
            formula_id: Formula identifier
            state: Current deployment state
            
        Returns:
            Sync results
        """
        if formula_id not in self.formulas:
            return {'success': False, 'error': 'Formula not found'}
        
        formula = self.formulas[formula_id]
        
        # Check if sync is needed
        if not self._needs_sync(formula_id, state):
            return {
                'success': True,
                'skipped': True,
                'reason': 'No changes detected'
            }
        
        # Perform sync
        try:
            # This would make actual API call to update formula
            # For now, mock the sync
            self._perform_sync(formula, state)
            
            # Update sync metadata
            formula['last_sync'] = datetime.now().isoformat()
            formula['sync_count'] += 1
            
            # Track performance
            self._track_performance(formula_id, state)
            
            return {
                'success': True,
                'synced': True,
                'timestamp': formula['last_sync']
            }
            
        except Exception as e:
            formula['errors'].append({
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return {
                'success': False,
                'error': str(e)
            }
    
    def _needs_sync(self, formula_id: str, state: Dict[str, Any]) -> bool:
        """Check if formula needs synchronization.
        
        Args:
            formula_id: Formula identifier
            state: Current deployment state
            
        Returns:
            True if sync is needed
        """
        formula = self.formulas[formula_id]
        
        # Check if auto-sync is enabled
        if not formula.get('auto_sync', True):
            return False
        
        # Check if dependencies have changed
        for dep_id in self.dependencies.get(formula_id, []):
            if self._has_dependency_changed(dep_id, formula['last_sync'], state):
                return True
        
        # Check if formula has never been synced
        if formula['last_sync'] is None:
            return True
        
        return False
    
    def _has_dependency_changed(self, dep_id: str, since: Optional[str], 
                               state: Dict[str, Any]) -> bool:
        """Check if a dependency has changed.
        
        Args:
            dep_id: Dependency identifier
            since: Timestamp to check against
            state: Current deployment state
            
        Returns:
            True if dependency has changed
        """
        # This would check actual change timestamps
        # For now, mock the check
        changes = state.get('property_changes', {})
        if dep_id in changes:
            change_time = changes[dep_id].get('timestamp')
            if since is None or change_time > since:
                return True
        return False
    
    def _perform_sync(self, formula: Dict[str, Any], state: Dict[str, Any]):
        """Perform the actual formula synchronization.
        
        Args:
            formula: Formula configuration
            state: Current deployment state
        """
        # Store sync operation in state
        if 'formula_syncs' not in state:
            state['formula_syncs'] = []
        
        state['formula_syncs'].append({
            'database_id': formula['database_id'],
            'property_name': formula['property_name'],
            'expression': formula['expression'],
            'timestamp': datetime.now().isoformat()
        })
    
    def _track_performance(self, formula_id: str, state: Dict[str, Any]):
        """Track formula performance metrics.
        
        Args:
            formula_id: Formula identifier
            state: Current deployment state
        """
        # This would measure actual performance
        # For now, mock the metrics
        self.performance_metrics[formula_id] = {
            'execution_time': 0.05,  # seconds
            'complexity_score': self._calculate_complexity(
                self.formulas[formula_id]['expression']
            ),
            'dependency_depth': self._get_dependency_depth(formula_id)
        }
    
    def _calculate_complexity(self, expression: str) -> int:
        """Calculate formula complexity score.
        
        Args:
            expression: Formula expression
            
        Returns:
            Complexity score (0-100)
        """
        score = 0
        
        # Count nested functions
        score += expression.count('(') * 2
        
        # Count logical operators
        score += expression.count(' and ') * 3
        score += expression.count(' or ') * 3
        score += expression.count('if(') * 5
        
        # Count property references
        score += expression.count('prop(') * 1
        
        # Cap at 100
        return min(score, 100)
    
    def _get_dependency_depth(self, formula_id: str, depth: int = 0) -> int:
        """Get maximum dependency depth.
        
        Args:
            formula_id: Formula identifier
            depth: Current depth
            
        Returns:
            Maximum dependency depth
        """
        if formula_id not in self.dependencies:
            return depth
        
        max_depth = depth
        for dep_id in self.dependencies[formula_id]:
            dep_depth = self._get_dependency_depth(dep_id, depth + 1)
            max_depth = max(max_depth, dep_depth)
        
        return max_depth
    
    def sync_all(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize all registered formulas.
        
        Args:
            state: Current deployment state
            
        Returns:
            Batch sync results
        """
        results = {
            'total': len(self.formulas),
            'synced': 0,
            'skipped': 0,
            'failed': 0,
            'errors': []
        }
        
        # Sort formulas by dependency order
        sorted_formulas = self._topological_sort()
        
        for formula_id in sorted_formulas:
            result = self.sync_formula(formula_id, state)
            if result['success']:
                if result.get('skipped'):
                    results['skipped'] += 1
                else:
                    results['synced'] += 1
            else:
                results['failed'] += 1
                results['errors'].append({
                    'formula_id': formula_id,
                    'error': result.get('error')
                })
        
        return results
    
    def _topological_sort(self) -> List[str]:
        """Sort formulas in dependency order.
        
        Returns:
            List of formula IDs in dependency order
        """
        visited = set()
        stack = []
        
        def visit(formula_id: str):
            if formula_id in visited:
                return
            visited.add(formula_id)
            
            for dep_id in self.dependencies.get(formula_id, []):
                if dep_id in self.formulas:  # Only visit registered formulas
                    visit(dep_id)
            
            stack.append(formula_id)
        
        for formula_id in self.formulas:
            visit(formula_id)
        
        return stack
    
    def optimize_formulas(self) -> Dict[str, Any]:
        """Optimize formula performance.
        
        Returns:
            Optimization results
        """
        optimizations = []
        
        for formula_id, metrics in self.performance_metrics.items():
            formula = self.formulas[formula_id]
            
            # Suggest optimizations based on metrics
            if metrics['complexity_score'] > 50:
                optimizations.append({
                    'formula_id': formula_id,
                    'suggestion': 'Consider breaking down complex formula',
                    'complexity': metrics['complexity_score']
                })
            
            if metrics['dependency_depth'] > 3:
                optimizations.append({
                    'formula_id': formula_id,
                    'suggestion': 'Deep dependency chain may affect performance',
                    'depth': metrics['dependency_depth']
                })
            
            if metrics['execution_time'] > 0.1:
                optimizations.append({
                    'formula_id': formula_id,
                    'suggestion': 'Formula execution time is high',
                    'time': metrics['execution_time']
                })
        
        return {
            'total_formulas': len(self.formulas),
            'optimizations': optimizations,
            'average_complexity': sum(
                m['complexity_score'] for m in self.performance_metrics.values()
            ) / len(self.performance_metrics) if self.performance_metrics else 0
        }
    
    def get_sync_report(self) -> Dict[str, Any]:
        """Get formula sync report.
        
        Returns:
            Sync status report
        """
        return {
            'total_formulas': len(self.formulas),
            'total_dependencies': sum(
                len(deps) for deps in self.dependencies.values()
            ),
            'validation_errors': len(self.validation_errors),
            'recent_syncs': [
                {
                    'id': fid,
                    'last_sync': f['last_sync'],
                    'sync_count': f['sync_count']
                }
                for fid, f in self.formulas.items()
                if f['last_sync'] is not None
            ][-10:]  # Last 10 syncs
        }


def setup_formula_sync(state: Dict[str, Any]) -> Dict[str, Any]:
    """Setup formula auto-sync for Estate Planning system.
    
    Args:
        state: Current deployment state
        
    Returns:
        Setup results
    """
    manager = FormulaSyncManager()
    
    # Define standard formulas for Estate Planning
    formulas = [
        {
            'id': 'total_assets',
            'config': {
                'database_id': 'Assets',
                'property_name': 'Total Value',
                'expression': 'sum(prop("Value"))',
                'type': FormulaType.ROLLUP.value,
                'dependencies': ['asset_values'],
                'auto_sync': True
            }
        },
        {
            'id': 'net_worth',
            'config': {
                'database_id': 'Estate',
                'property_name': 'Net Worth',
                'expression': 'prop("Total Assets") - prop("Total Liabilities")',
                'type': FormulaType.SIMPLE.value,
                'dependencies': ['total_assets', 'total_liabilities'],
                'auto_sync': True
            }
        },
        {
            'id': 'task_overdue',
            'config': {
                'database_id': 'Task Tracker',
                'property_name': 'Overdue',
                'expression': 'and(prop("Due Date") < now(), prop("Status") != "Done")',
                'type': FormulaType.CONDITIONAL.value,
                'dependencies': ['due_date', 'status'],
                'auto_sync': True
            }
        },
        {
            'id': 'document_expiry',
            'config': {
                'database_id': 'Important Documents',
                'property_name': 'Days Until Expiry',
                'expression': 'dateBetween(prop("Expiry Date"), now(), "days")',
                'type': FormulaType.DATE.value,
                'dependencies': ['expiry_date'],
                'auto_sync': True
            }
        },
        {
            'id': 'contact_full_name',
            'config': {
                'database_id': 'Contacts',
                'property_name': 'Full Name',
                'expression': 'concat(prop("First Name"), " ", prop("Last Name"))',
                'type': FormulaType.TEXT.value,
                'dependencies': ['first_name', 'last_name'],
                'auto_sync': True
            }
        }
    ]
    
    # Register formulas
    for formula_def in formulas:
        manager.register_formula(formula_def['id'], formula_def['config'])
    
    # Perform initial sync
    sync_results = manager.sync_all(state)
    
    # Get optimization suggestions
    optimizations = manager.optimize_formulas()
    
    # Store manager in state
    state['formula_sync_manager'] = manager
    
    return {
        'formulas_registered': len(manager.formulas),
        'formulas_synced': sync_results['synced'],
        'validation_errors': len(manager.validation_errors),
        'optimization_suggestions': len(optimizations['optimizations']),
        'average_complexity': optimizations['average_complexity']
    }