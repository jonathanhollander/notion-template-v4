"""Conditional Page Creation for Notion Deployment.

Implements conditional page creation within Notion with:
- Rule-based page generation
- Template selection based on conditions
- Dynamic property population
- Parent-child relationship management
- Conditional visibility through filters
- Automated page naming conventions
"""

import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from constants import *

logger = logging.getLogger(__name__)


class ConditionType(Enum):
    """Types of conditions for page creation."""
    PROPERTY_VALUE = "property_value"      # Based on property values
    RELATION_EXISTS = "relation_exists"    # Based on relation presence
    DATE_RANGE = "date_range"             # Based on date conditions
    FORMULA_RESULT = "formula_result"      # Based on formula output
    USER_ROLE = "user_role"               # Based on user permissions
    COUNT_THRESHOLD = "count_threshold"    # Based on count of items


class ConditionalPageManager:
    """Manages conditional page creation in Notion."""
    
    def __init__(self):
        """Initialize conditional page manager."""
        self.rules = []
        self.templates = {}
        self.created_pages = []
        self.skipped_conditions = []
    
    def add_rule(self, rule_id: str, config: Dict[str, Any]):
        """Add a conditional page creation rule.
        
        Args:
            rule_id: Unique rule identifier
            config: Rule configuration including:
                - condition_type: Type of condition
                - condition_params: Parameters for condition evaluation
                - template_id: Template to use when condition is met
                - parent_page_id: Parent page for created pages
                - naming_pattern: Pattern for page naming
                - properties: Properties to populate
                - create_once: Whether to create only once per condition
        """
        self.rules.append({
            'id': rule_id,
            **config,
            'created_at': datetime.now().isoformat(),
            'executions': 0,
            'pages_created': []
        })
        
        logger.info(f"Added conditional page rule: {rule_id}")
    
    def register_template(self, template_id: str, template: Dict[str, Any]):
        """Register a page template.
        
        Args:
            template_id: Unique template identifier
            template: Template configuration with blocks and properties
        """
        self.templates[template_id] = {
            **template,
            'registered_at': datetime.now().isoformat(),
            'usage_count': 0
        }
    
    def evaluate_conditions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Evaluate all rules and determine which pages to create.
        
        Args:
            state: Current deployment state
            
        Returns:
            List of pages to create
        """
        pages_to_create = []
        
        for rule in self.rules:
            if self._should_create_page(rule, state):
                page_config = self._prepare_page_config(rule, state)
                pages_to_create.append({
                    'rule_id': rule['id'],
                    'config': page_config
                })
                rule['executions'] += 1
        
        return pages_to_create
    
    def _should_create_page(self, rule: Dict[str, Any], 
                           state: Dict[str, Any]) -> bool:
        """Check if page should be created based on rule.
        
        Args:
            rule: Rule configuration
            state: Current deployment state
            
        Returns:
            True if page should be created
        """
        condition_type = ConditionType(rule['condition_type'])
        params = rule['condition_params']
        
        # Check if already created (for create_once rules)
        if rule.get('create_once') and len(rule['pages_created']) > 0:
            return False
        
        # Evaluate condition based on type
        if condition_type == ConditionType.PROPERTY_VALUE:
            return self._check_property_value(params, state)
        elif condition_type == ConditionType.RELATION_EXISTS:
            return self._check_relation_exists(params, state)
        elif condition_type == ConditionType.DATE_RANGE:
            return self._check_date_range(params, state)
        elif condition_type == ConditionType.FORMULA_RESULT:
            return self._check_formula_result(params, state)
        elif condition_type == ConditionType.USER_ROLE:
            return self._check_user_role(params, state)
        elif condition_type == ConditionType.COUNT_THRESHOLD:
            return self._check_count_threshold(params, state)
        
        return False
    
    def _check_property_value(self, params: Dict[str, Any], 
                             state: Dict[str, Any]) -> bool:
        """Check property value condition.
        
        Args:
            params: Condition parameters
            state: Current deployment state
            
        Returns:
            True if condition is met
        """
        database_id = params.get('database_id')
        property_name = params.get('property_name')
        expected_value = params.get('value')
        operator = params.get('operator', 'equals')
        
        # Check in state for matching records
        records = state.get('database_records', {}).get(database_id, [])
        
        for record in records:
            value = record.get('properties', {}).get(property_name)
            
            if operator == 'equals' and value == expected_value:
                return True
            elif operator == 'contains' and expected_value in str(value):
                return True
            elif operator == 'greater_than' and value > expected_value:
                return True
            elif operator == 'less_than' and value < expected_value:
                return True
        
        return False
    
    def _check_relation_exists(self, params: Dict[str, Any], 
                              state: Dict[str, Any]) -> bool:
        """Check if relation exists.
        
        Args:
            params: Condition parameters
            state: Current deployment state
            
        Returns:
            True if relation exists
        """
        source_db = params.get('source_database')
        target_db = params.get('target_database')
        
        # Check in state for relation
        relations = state.get('relations', [])
        for relation in relations:
            if (relation.get('source') == source_db and 
                relation.get('target') == target_db):
                return True
        
        return False
    
    def _check_date_range(self, params: Dict[str, Any], 
                         state: Dict[str, Any]) -> bool:
        """Check date range condition.
        
        Args:
            params: Condition parameters
            state: Current deployment state
            
        Returns:
            True if date condition is met
        """
        property_name = params.get('property_name')
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        
        # This would check actual dates in Notion
        # For now, return True if within deployment date range
        current_date = datetime.now().isoformat()
        return start_date <= current_date <= end_date
    
    def _check_formula_result(self, params: Dict[str, Any], 
                             state: Dict[str, Any]) -> bool:
        """Check formula result condition.
        
        Args:
            params: Condition parameters
            state: Current deployment state
            
        Returns:
            True if formula condition is met
        """
        formula_id = params.get('formula_id')
        expected_result = params.get('expected_result')
        
        # Check formula results in state
        formula_results = state.get('formula_results', {})
        result = formula_results.get(formula_id)
        
        return result == expected_result
    
    def _check_user_role(self, params: Dict[str, Any], 
                        state: Dict[str, Any]) -> bool:
        """Check user role condition.
        
        Args:
            params: Condition parameters
            state: Current deployment state
            
        Returns:
            True if user has required role
        """
        required_role = params.get('role')
        
        # Check user role in state
        user_role = state.get('user_role', 'Viewer')
        
        # Role hierarchy: Admin > Executor > Family > Advisor > Viewer
        role_hierarchy = ['Admin', 'Executor', 'Family', 'Advisor', 'Viewer']
        
        if required_role in role_hierarchy and user_role in role_hierarchy:
            return role_hierarchy.index(user_role) <= role_hierarchy.index(required_role)
        
        return False
    
    def _check_count_threshold(self, params: Dict[str, Any], 
                              state: Dict[str, Any]) -> bool:
        """Check count threshold condition.
        
        Args:
            params: Condition parameters
            state: Current deployment state
            
        Returns:
            True if count threshold is met
        """
        database_id = params.get('database_id')
        threshold = params.get('threshold')
        operator = params.get('operator', 'greater_than')
        
        # Count records in database
        records = state.get('database_records', {}).get(database_id, [])
        count = len(records)
        
        if operator == 'greater_than':
            return count > threshold
        elif operator == 'less_than':
            return count < threshold
        elif operator == 'equals':
            return count == threshold
        
        return False
    
    def _prepare_page_config(self, rule: Dict[str, Any], 
                           state: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare page configuration based on rule.
        
        Args:
            rule: Rule configuration
            state: Current deployment state
            
        Returns:
            Page configuration
        """
        template_id = rule.get('template_id')
        template = self.templates.get(template_id, {})
        
        # Generate page name
        naming_pattern = rule.get('naming_pattern', 'Page {timestamp}')
        page_name = naming_pattern.format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'),
            rule_id=rule['id'],
            count=len(rule['pages_created']) + 1
        )
        
        # Prepare properties
        properties = {}
        for prop_name, prop_config in rule.get('properties', {}).items():
            if isinstance(prop_config, dict) and 'from_state' in prop_config:
                # Get value from state
                state_key = prop_config['from_state']
                properties[prop_name] = state.get(state_key)
            else:
                properties[prop_name] = prop_config
        
        return {
            'parent_id': rule.get('parent_page_id'),
            'title': page_name,
            'properties': properties,
            'blocks': template.get('blocks', []),
            'icon': template.get('icon'),
            'cover': template.get('cover')
        }
    
    def create_conditional_pages(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create all conditional pages based on rules.
        
        Args:
            state: Current deployment state
            
        Returns:
            Creation results
        """
        results = {
            'evaluated_rules': len(self.rules),
            'pages_created': 0,
            'pages_skipped': 0,
            'errors': []
        }
        
        # Evaluate conditions
        pages_to_create = self.evaluate_conditions(state)
        
        for page_spec in pages_to_create:
            try:
                # This would make actual API call to create page
                # For now, mock the creation
                page_id = self._create_page(page_spec['config'], state)
                
                # Track created page
                rule = next(r for r in self.rules if r['id'] == page_spec['rule_id'])
                rule['pages_created'].append(page_id)
                self.created_pages.append({
                    'id': page_id,
                    'rule_id': page_spec['rule_id'],
                    'created_at': datetime.now().isoformat()
                })
                
                results['pages_created'] += 1
                
            except Exception as e:
                results['errors'].append({
                    'rule_id': page_spec['rule_id'],
                    'error': str(e)
                })
        
        results['pages_skipped'] = len(self.rules) - len(pages_to_create)
        
        return results
    
    def _create_page(self, config: Dict[str, Any], 
                    state: Dict[str, Any]) -> str:
        """Create a page in Notion.
        
        Args:
            config: Page configuration
            state: Current deployment state
            
        Returns:
            Created page ID
        """
        # Store page creation in state
        if 'conditional_pages' not in state:
            state['conditional_pages'] = []
        
        page_id = f"page_{datetime.now().timestamp()}"
        
        state['conditional_pages'].append({
            'id': page_id,
            'parent_id': config['parent_id'],
            'title': config['title'],
            'properties': config['properties'],
            'created_at': datetime.now().isoformat()
        })
        
        return page_id
    
    def get_creation_report(self) -> Dict[str, Any]:
        """Get conditional page creation report.
        
        Returns:
            Creation report
        """
        return {
            'total_rules': len(self.rules),
            'total_templates': len(self.templates),
            'pages_created': len(self.created_pages),
            'rules_executed': sum(1 for r in self.rules if r['executions'] > 0),
            'most_used_template': max(
                self.templates.items(),
                key=lambda x: x[1]['usage_count']
            )[0] if self.templates else None
        }


def setup_conditional_pages(state: Dict[str, Any]) -> Dict[str, Any]:
    """Setup conditional page creation for Estate Planning system.
    
    Args:
        state: Current deployment state
        
    Returns:
        Setup results
    """
    manager = ConditionalPageManager()
    
    # Register templates for Estate Planning
    templates = {
        'beneficiary_page': {
            'blocks': [
                {'type': 'heading_1', 'text': 'Beneficiary Information'},
                {'type': 'paragraph', 'text': 'Details about beneficiary'},
                {'type': 'divider'},
                {'type': 'database', 'database_id': 'Assets'}
            ],
            'icon': '👤',
            'cover': None
        },
        'estate_summary': {
            'blocks': [
                {'type': 'heading_1', 'text': 'Estate Summary'},
                {'type': 'callout', 'text': 'Important estate information'},
                {'type': 'toggle', 'text': 'Financial Overview'},
                {'type': 'database', 'database_id': 'Financial Accounts'}
            ],
            'icon': '📊',
            'cover': None
        },
        'task_dashboard': {
            'blocks': [
                {'type': 'heading_1', 'text': 'Task Dashboard'},
                {'type': 'database_view', 'database_id': 'Task Tracker', 'view': 'calendar'},
                {'type': 'divider'},
                {'type': 'database_view', 'database_id': 'Task Tracker', 'view': 'board'}
            ],
            'icon': '✅',
            'cover': None
        }
    }
    
    for template_id, template_config in templates.items():
        manager.register_template(template_id, template_config)
    
    # Define conditional page creation rules
    rules = [
        {
            'id': 'create_beneficiary_pages',
            'config': {
                'condition_type': ConditionType.PROPERTY_VALUE.value,
                'condition_params': {
                    'database_id': 'Contacts',
                    'property_name': 'Relationship',
                    'value': 'Beneficiary',
                    'operator': 'equals'
                },
                'template_id': 'beneficiary_page',
                'parent_page_id': state.get('pages', {}).get('Family Hub'),
                'naming_pattern': 'Beneficiary - {timestamp}',
                'properties': {
                    'Type': 'Beneficiary Page',
                    'Created': datetime.now().isoformat()
                },
                'create_once': False
            }
        },
        {
            'id': 'create_estate_summary',
            'config': {
                'condition_type': ConditionType.COUNT_THRESHOLD.value,
                'condition_params': {
                    'database_id': 'Assets',
                    'threshold': 5,
                    'operator': 'greater_than'
                },
                'template_id': 'estate_summary',
                'parent_page_id': state.get('pages', {}).get('Executor Hub'),
                'naming_pattern': 'Estate Summary - {timestamp}',
                'properties': {
                    'Type': 'Summary',
                    'Auto-Generated': True
                },
                'create_once': True
            }
        },
        {
            'id': 'create_task_dashboard',
            'config': {
                'condition_type': ConditionType.USER_ROLE.value,
                'condition_params': {
                    'role': 'Executor'
                },
                'template_id': 'task_dashboard',
                'parent_page_id': state.get('pages', {}).get('Executor Hub'),
                'naming_pattern': 'Task Dashboard - {timestamp}',
                'properties': {
                    'Type': 'Dashboard',
                    'Visibility': 'Executor Only'
                },
                'create_once': True
            }
        }
    ]
    
    for rule_def in rules:
        manager.add_rule(rule_def['id'], rule_def['config'])
    
    # Create conditional pages
    results = manager.create_conditional_pages(state)
    
    # Store manager in state
    state['conditional_page_manager'] = manager
    
    return {
        'rules_defined': len(manager.rules),
        'templates_registered': len(manager.templates),
        'pages_created': results['pages_created'],
        'pages_skipped': results['pages_skipped'],
        'errors': len(results['errors'])
    }