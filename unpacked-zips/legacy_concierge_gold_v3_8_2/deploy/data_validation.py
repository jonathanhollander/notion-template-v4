"""Data Validation Framework for Notion Deployment.

Implements comprehensive data validation with:
- Field type validation
- Required field checking
- Format validation (email, phone, URL)
- Range and length validation
- Custom validation rules
- Cross-field validation
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from constants import *

logger = logging.getLogger(__name__)


class ValidationType(Enum):
    """Types of validation rules."""
    REQUIRED = "required"
    TYPE = "type"
    FORMAT = "format"
    RANGE = "range"
    LENGTH = "length"
    PATTERN = "pattern"
    CUSTOM = "custom"
    CROSS_FIELD = "cross_field"


class DataValidator:
    """Validates data against defined rules."""
    
    def __init__(self):
        """Initialize validator."""
        self.validation_rules = {}
        self.validation_results = []
        self.custom_validators = {}
        
        # Built-in format validators
        self.format_validators = {
            'email': self._validate_email,
            'phone': self._validate_phone,
            'url': self._validate_url,
            'date': self._validate_date,
            'ssn': self._validate_ssn,
            'zip': self._validate_zip
        }
    
    def define_rules(self, entity_type: str, rules: Dict[str, List[Dict[str, Any]]]):
        """Define validation rules for an entity type.
        
        Args:
            entity_type: Type of entity (e.g., 'contact', 'asset')
            rules: Dictionary of field names to validation rules
        """
        self.validation_rules[entity_type] = rules
        logger.info(f"Defined validation rules for {entity_type}")
    
    def validate(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against rules.
        
        Args:
            entity_type: Type of entity
            data: Data to validate
            
        Returns:
            Validation results
        """
        if entity_type not in self.validation_rules:
            return {'valid': True, 'errors': [], 'warnings': []}
        
        errors = []
        warnings = []
        rules = self.validation_rules[entity_type]
        
        for field_name, field_rules in rules.items():
            field_value = data.get(field_name)
            
            for rule in field_rules:
                result = self._apply_rule(field_name, field_value, rule, data)
                if result['status'] == 'error':
                    errors.append(result['message'])
                elif result['status'] == 'warning':
                    warnings.append(result['message'])
        
        validation_result = {
            'entity_type': entity_type,
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'timestamp': datetime.now().isoformat()
        }
        
        self.validation_results.append(validation_result)
        return validation_result
    
    def _apply_rule(self, field_name: str, field_value: Any, 
                   rule: Dict[str, Any], full_data: Dict[str, Any]) -> Dict[str, str]:
        """Apply a single validation rule.
        
        Args:
            field_name: Name of field
            field_value: Value to validate
            rule: Validation rule
            full_data: Complete data object for cross-field validation
            
        Returns:
            Validation result
        """
        rule_type = ValidationType(rule.get('type', 'required'))
        
        if rule_type == ValidationType.REQUIRED:
            if field_value is None or field_value == '':
                return {
                    'status': 'error',
                    'message': f"{field_name} is required"
                }
        
        elif rule_type == ValidationType.TYPE:
            expected_type = rule.get('expected_type')
            if not self._check_type(field_value, expected_type):
                return {
                    'status': 'error',
                    'message': f"{field_name} must be of type {expected_type}"
                }
        
        elif rule_type == ValidationType.FORMAT:
            format_type = rule.get('format')
            if format_type in self.format_validators:
                if not self.format_validators[format_type](field_value):
                    return {
                        'status': 'error',
                        'message': f"{field_name} has invalid {format_type} format"
                    }
        
        elif rule_type == ValidationType.RANGE:
            min_val = rule.get('min')
            max_val = rule.get('max')
            if min_val is not None and field_value < min_val:
                return {
                    'status': 'error',
                    'message': f"{field_name} must be at least {min_val}"
                }
            if max_val is not None and field_value > max_val:
                return {
                    'status': 'error',
                    'message': f"{field_name} must be at most {max_val}"
                }
        
        elif rule_type == ValidationType.LENGTH:
            min_len = rule.get('min')
            max_len = rule.get('max')
            value_len = len(str(field_value)) if field_value else 0
            if min_len is not None and value_len < min_len:
                return {
                    'status': 'error',
                    'message': f"{field_name} must be at least {min_len} characters"
                }
            if max_len is not None and value_len > max_len:
                return {
                    'status': 'error',
                    'message': f"{field_name} must be at most {max_len} characters"
                }
        
        elif rule_type == ValidationType.PATTERN:
            pattern = rule.get('pattern')
            if pattern and not re.match(pattern, str(field_value)):
                return {
                    'status': 'error',
                    'message': f"{field_name} does not match required pattern"
                }
        
        elif rule_type == ValidationType.CROSS_FIELD:
            validator_name = rule.get('validator')
            if validator_name in self.custom_validators:
                result = self.custom_validators[validator_name](field_value, full_data)
                if not result['valid']:
                    return {
                        'status': 'error',
                        'message': result.get('message', f"Cross-field validation failed for {field_name}")
                    }
        
        return {'status': 'ok', 'message': ''}
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            'string': str,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
            'date': (str, datetime)
        }
        
        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True
    
    def _validate_email(self, value: str) -> bool:
        """Validate email format."""
        if not value:
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(value)))
    
    def _validate_phone(self, value: str) -> bool:
        """Validate phone number format."""
        if not value:
            return False
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)\.]', '', str(value))
        # Check if it's a valid phone number (10-15 digits)
        return bool(re.match(r'^\+?\d{10,15}$', cleaned))
    
    def _validate_url(self, value: str) -> bool:
        """Validate URL format."""
        if not value:
            return False
        pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(pattern, str(value)))
    
    def _validate_date(self, value: str) -> bool:
        """Validate date format."""
        if not value:
            return False
        try:
            datetime.fromisoformat(str(value))
            return True
        except:
            return False
    
    def _validate_ssn(self, value: str) -> bool:
        """Validate SSN format."""
        if not value:
            return False
        cleaned = re.sub(r'[\s\-]', '', str(value))
        return bool(re.match(r'^\d{9}$', cleaned))
    
    def _validate_zip(self, value: str) -> bool:
        """Validate ZIP code format."""
        if not value:
            return False
        return bool(re.match(r'^\d{5}(-\d{4})?$', str(value)))
    
    def register_custom_validator(self, name: str, validator: Callable):
        """Register a custom validator function.
        
        Args:
            name: Validator name
            validator: Validator function
        """
        self.custom_validators[name] = validator
    
    def validate_batch(self, entity_type: str, 
                      data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate multiple records.
        
        Args:
            entity_type: Type of entity
            data_list: List of data records
            
        Returns:
            Batch validation results
        """
        results = {
            'total': len(data_list),
            'valid': 0,
            'invalid': 0,
            'errors': [],
            'warnings': []
        }
        
        for i, data in enumerate(data_list):
            result = self.validate(entity_type, data)
            if result['valid']:
                results['valid'] += 1
            else:
                results['invalid'] += 1
                results['errors'].extend([
                    f"Record {i+1}: {error}" for error in result['errors']
                ])
            results['warnings'].extend([
                f"Record {i+1}: {warning}" for warning in result['warnings']
            ])
        
        return results
    
    def get_validation_report(self) -> Dict[str, Any]:
        """Get validation report summary.
        
        Returns:
            Validation report
        """
        total_validations = len(self.validation_results)
        valid_count = sum(1 for r in self.validation_results if r['valid'])
        
        return {
            'total_validations': total_validations,
            'valid': valid_count,
            'invalid': total_validations - valid_count,
            'success_rate': (valid_count / total_validations * 100) if total_validations > 0 else 0,
            'recent_errors': [
                r['errors'] for r in self.validation_results[-10:] if not r['valid']
            ]
        }


def setup_data_validation(state: Dict[str, Any]) -> Dict[str, Any]:
    """Setup data validation for Estate Planning system.
    
    Args:
        state: Current deployment state
        
    Returns:
        Validation setup results
    """
    validator = DataValidator()
    
    # Define validation rules for different entity types
    
    # Contact validation rules
    validator.define_rules('contact', {
        'Name': [
            {'type': ValidationType.REQUIRED.value},
            {'type': ValidationType.LENGTH.value, 'min': 2, 'max': 100}
        ],
        'Email': [
            {'type': ValidationType.FORMAT.value, 'format': 'email'}
        ],
        'Phone': [
            {'type': ValidationType.FORMAT.value, 'format': 'phone'}
        ],
        'Relationship': [
            {'type': ValidationType.REQUIRED.value}
        ]
    })
    
    # Asset validation rules
    validator.define_rules('asset', {
        'Asset Name': [
            {'type': ValidationType.REQUIRED.value},
            {'type': ValidationType.LENGTH.value, 'min': 2, 'max': 200}
        ],
        'Value': [
            {'type': ValidationType.TYPE.value, 'expected_type': 'number'},
            {'type': ValidationType.RANGE.value, 'min': 0}
        ],
        'Category': [
            {'type': ValidationType.REQUIRED.value}
        ]
    })
    
    # Document validation rules
    validator.define_rules('document', {
        'Document Name': [
            {'type': ValidationType.REQUIRED.value}
        ],
        'Type': [
            {'type': ValidationType.REQUIRED.value}
        ],
        'Expiry Date': [
            {'type': ValidationType.FORMAT.value, 'format': 'date'}
        ]
    })
    
    # Custom cross-field validator for financial accounts
    def validate_account_balance(value, data):
        """Validate account balance against account type."""
        account_type = data.get('Account Type')
        if account_type == 'Credit Card' and value > 0:
            return {'valid': False, 'message': 'Credit card balance should be negative'}
        return {'valid': True}
    
    validator.register_custom_validator('account_balance', validate_account_balance)
    
    # Store validator in state
    state['data_validator'] = validator
    
    return {
        'rules_defined': len(validator.validation_rules),
        'entity_types': list(validator.validation_rules.keys()),
        'custom_validators': len(validator.custom_validators)
    }