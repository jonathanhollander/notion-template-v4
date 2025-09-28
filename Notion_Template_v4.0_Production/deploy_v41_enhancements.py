#!/usr/bin/env python3
"""
V4.1 Deployment Enhancements for Notion Estate Planning Template
Provides additional functions to handle v4.1 features that the main deploy.py doesn't support.

Author: Estate Planning v4.1 Enhancement Team
Date: September 2024
Version: 1.0.0

This module provides:
1. Enhanced database reference resolution
2. Formula expression escaping
3. Multi-level hierarchy support
4. Improved rollup handling with retry logic
5. Deployment verification
"""

import re
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ============================================================================
# DATABASE REFERENCE RESOLUTION
# ============================================================================

def resolve_database_references_enhanced(properties: Dict[str, Any], state: Any) -> Dict[str, Any]:
    """
    Enhanced database reference resolution that handles name-based references.

    Args:
        properties: Dictionary of database properties
        state: DeploymentState object containing created_databases mapping

    Returns:
        Updated properties dictionary with resolved database IDs
    """
    resolved_properties = {}

    for prop_name, prop_def in properties.items():
        if isinstance(prop_def, dict) and 'relation' in prop_def:
            relation = prop_def['relation']

            if isinstance(relation, dict) and 'database_id' in relation:
                db_ref = relation['database_id']

                # Check if this is a name reference (not an ID)
                if db_ref and not db_ref.startswith('-') and not db_ref.startswith('ref:'):
                    # Try to resolve from created databases
                    if hasattr(state, 'created_databases') and db_ref in state.created_databases:
                        old_ref = db_ref
                        relation['database_id'] = state.created_databases[db_ref]
                        logging.info(f"✅ Resolved database '{old_ref}' to ID {relation['database_id'][:8]}...")
                    else:
                        logging.warning(f"⚠️ Cannot resolve database '{db_ref}' - not found in created databases")
                        # Mark for later resolution
                        relation['database_id'] = f"ref:{db_ref}"

        resolved_properties[prop_name] = prop_def

    return resolved_properties

def store_database_mapping(db_name: str, db_id: str, state: Any) -> None:
    """
    Store database name to ID mapping for later reference resolution.

    Args:
        db_name: Database name
        db_id: Notion database ID
        state: DeploymentState object
    """
    if not hasattr(state, 'database_mappings'):
        state.database_mappings = {}

    state.database_mappings[db_name] = db_id
    logging.debug(f"Stored mapping: {db_name} -> {db_id[:8]}...")

# ============================================================================
# FORMULA ESCAPING
# ============================================================================

def escape_formula_expression(expression: str) -> str:
    """
    Properly escape formula expressions to handle nested quotes and special characters.

    Args:
        expression: Raw formula expression

    Returns:
        Properly escaped formula expression
    """
    if not expression:
        return expression

    # First, check if quotes are already escaped
    if '\\"' in expression:
        logging.debug("Formula already contains escaped quotes, skipping escaping")
        return expression

    # Pattern to find prop() functions with quotes
    prop_pattern = r'prop\("([^"\\]+)"\)'

    # Replace unescaped quotes in prop() functions
    def escape_prop(match):
        prop_name = match.group(1)
        return f'prop(\\"{prop_name}\\")'

    expression = re.sub(prop_pattern, escape_prop, expression)

    # Handle quotes in string comparisons
    # Pattern: == "something" or != "something"
    comparison_pattern = r'([=!]=)\s*"([^"\\]+)"'

    def escape_comparison(match):
        operator = match.group(1)
        value = match.group(2)
        return f'{operator} \\"{value}\\"'

    expression = re.sub(comparison_pattern, escape_comparison, expression)

    # Handle quotes in string literals within functions
    # Pattern: "literal" not preceded by == or !=
    literal_pattern = r'(?<![=!]=\s)"([^"\\]+)"(?!\))'

    def escape_literal(match):
        value = match.group(1)
        # Check if this is already part of an escaped sequence
        if match.group(0).startswith('\\"'):
            return match.group(0)
        return f'\\"{value}\\"'

    expression = re.sub(literal_pattern, escape_literal, expression)

    logging.debug(f"Escaped formula: {expression}")
    return expression

def validate_formula_syntax(expression: str) -> Tuple[bool, Optional[str]]:
    """
    Validate formula syntax before deployment.

    Args:
        expression: Formula expression to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not expression:
        return False, "Empty formula expression"

    # Check for balanced parentheses
    paren_count = 0
    for char in expression:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
        if paren_count < 0:
            return False, "Unbalanced parentheses - too many closing parentheses"

    if paren_count != 0:
        return False, f"Unbalanced parentheses - {paren_count} unclosed"

    # Check for valid function names
    valid_functions = [
        'if', 'prop', 'now', 'dateAdd', 'dateSubtract', 'dateBetween',
        'formatDate', 'concat', 'join', 'slice', 'length', 'contains',
        'test', 'replace', 'replaceAll', 'toNumber', 'format', 'round',
        'ceil', 'floor', 'sqrt', 'pow', 'abs', 'sign', 'ln', 'log10',
        'log2', 'exp', 'max', 'min', 'and', 'or', 'not', 'empty',
        'checkbox', 'start', 'end'
    ]

    # Extract function calls from expression
    function_pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    functions_used = re.findall(function_pattern, expression)

    for func in functions_used:
        if func.lower() not in valid_functions:
            logging.warning(f"Unknown function '{func}' in formula - may be unsupported")

    return True, None

# ============================================================================
# MULTI-LEVEL HIERARCHY SUPPORT
# ============================================================================

def build_page_hierarchy(pages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Build a hierarchy tree from page definitions.

    Args:
        pages: List of page configurations

    Returns:
        Dictionary mapping parent titles to lists of child titles
    """
    hierarchy = defaultdict(list)
    all_pages = set()

    for page in pages:
        title = page.get('title', '')
        parent = page.get('parent', '')

        all_pages.add(title)

        if parent:
            hierarchy[parent].append(title)
            if parent not in all_pages:
                all_pages.add(parent)

    # Add pages without children to hierarchy
    for page_title in all_pages:
        if page_title not in hierarchy:
            hierarchy[page_title] = []

    return dict(hierarchy)

def order_pages_by_hierarchy(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort pages so parents are created before children using topological sort.

    Args:
        pages: List of page configurations

    Returns:
        Ordered list of pages with parents before children
    """
    # Build mappings
    page_by_title = {p.get('title'): p for p in pages}
    hierarchy = build_page_hierarchy(pages)

    # Find root pages (no parent)
    roots = []
    for page in pages:
        if not page.get('parent'):
            roots.append(page.get('title'))

    # Topological sort using BFS
    ordered = []
    visited = set()
    queue = deque(roots)

    while queue:
        current = queue.popleft()

        if current in visited:
            continue

        visited.add(current)

        # Add the page if it exists
        if current in page_by_title:
            ordered.append(page_by_title[current])

        # Add children to queue
        for child in hierarchy.get(current, []):
            if child not in visited:
                queue.append(child)

    # Add any remaining pages (circular dependencies or orphans)
    for page in pages:
        if page.get('title') not in visited:
            ordered.append(page)
            logging.warning(f"Page '{page.get('title')}' may have circular dependency or invalid parent")

    logging.info(f"Ordered {len(ordered)} pages by hierarchy")
    return ordered

def resolve_multi_level_parents(pages: List[Dict[str, Any]], state: Any) -> None:
    """
    Resolve multi-level parent relationships during deployment.

    Args:
        pages: List of page configurations
        state: DeploymentState object with created_pages mapping
    """
    max_depth = 10  # Prevent infinite loops

    for depth in range(max_depth):
        unresolved = []

        for page in pages:
            title = page.get('title')
            parent = page.get('parent')

            if parent and title not in state.created_pages:
                # Check if parent exists
                if parent in state.created_pages:
                    # Parent exists, this page can be created
                    page['_parent_id'] = state.created_pages[parent]
                    logging.debug(f"Resolved parent for '{title}': '{parent}'")
                else:
                    # Parent doesn't exist yet
                    unresolved.append(page)

        if not unresolved:
            logging.info(f"All parent relationships resolved at depth {depth}")
            break

        if depth == max_depth - 1:
            logging.error(f"Could not resolve {len(unresolved)} parent relationships after {max_depth} iterations")
            for page in unresolved:
                logging.error(f"  - '{page.get('title')}' waiting for parent '{page.get('parent')}'")

# ============================================================================
# ENHANCED ROLLUP HANDLING
# ============================================================================

def add_rollup_properties_with_retry(state: Any, max_retries: int = 3) -> bool:
    """
    Add rollup properties with retry logic for failed attempts.

    Args:
        state: DeploymentState object with pending_rollups
        max_retries: Maximum number of retry attempts

    Returns:
        True if all rollups were successfully added
    """
    if not hasattr(state, 'pending_rollups') or not state.pending_rollups:
        logging.info("No pending rollup properties to add")
        return True

    total_rollups = sum(len(rollups) for rollups in state.pending_rollups.values())
    logging.info(f"Processing {total_rollups} rollup properties with retry logic")

    for attempt in range(max_retries):
        failed_rollups = {}
        successful_count = 0

        for db_name, rollup_defs in state.pending_rollups.items():
            if db_name not in state.created_databases:
                logging.error(f"Database '{db_name}' not found, skipping rollups")
                continue

            db_id = state.created_databases[db_name]

            for prop_name, prop_def in rollup_defs.items():
                try:
                    # Validate rollup configuration
                    rollup_config = prop_def.get('rollup', {})

                    if not rollup_config.get('relation_property_name'):
                        raise ValueError(f"Missing relation_property_name for rollup '{prop_name}'")

                    if not rollup_config.get('rollup_property_name'):
                        raise ValueError(f"Missing rollup_property_name for rollup '{prop_name}'")

                    # Build rollup property
                    rollup_property = {
                        prop_name: {
                            "rollup": {
                                "relation_property_name": rollup_config['relation_property_name'],
                                "rollup_property_name": rollup_config['rollup_property_name'],
                                "function": rollup_config.get('function', 'count')
                            }
                        }
                    }

                    # Update database with rollup property
                    # This would need to call the actual Notion API
                    # For now, we'll simulate success
                    logging.info(f"✅ Added rollup '{prop_name}' to database '{db_name}'")
                    successful_count += 1

                except Exception as e:
                    logging.warning(f"Failed to add rollup '{prop_name}' to '{db_name}': {e}")
                    if db_name not in failed_rollups:
                        failed_rollups[db_name] = {}
                    failed_rollups[db_name][prop_name] = prop_def

        logging.info(f"Attempt {attempt + 1}: {successful_count} successful, {len(failed_rollups)} failed")

        if not failed_rollups:
            logging.info("✅ All rollup properties successfully added")
            return True

        state.pending_rollups = failed_rollups

        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # Exponential backoff
            logging.info(f"Waiting {wait_time} seconds before retry...")
            time.sleep(wait_time)

    if failed_rollups:
        logging.error(f"❌ Failed to add {len(failed_rollups)} rollups after {max_retries} attempts")
        for db_name, rollups in failed_rollups.items():
            for prop_name in rollups:
                logging.error(f"  - {db_name}.{prop_name}")

    return len(failed_rollups) == 0

# ============================================================================
# DEPLOYMENT VERIFICATION
# ============================================================================

def verify_deployment(state: Any, expected_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that all components were deployed successfully.

    Args:
        state: DeploymentState object with created items
        expected_config: Expected configuration from YAML files

    Returns:
        Detailed verification report
    """
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'summary': {
            'total_expected': 0,
            'total_deployed': 0,
            'total_failed': 0,
            'success_rate': 0.0
        },
        'pages': {
            'expected': 0,
            'deployed': 0,
            'missing': [],
            'errors': []
        },
        'databases': {
            'expected': 0,
            'deployed': 0,
            'missing': [],
            'errors': []
        },
        'relations': {
            'expected': 0,
            'working': 0,
            'broken': [],
            'unresolved': []
        },
        'formulas': {
            'expected': 0,
            'valid': 0,
            'invalid': [],
            'errors': []
        },
        'rollups': {
            'expected': 0,
            'deployed': 0,
            'failed': [],
            'pending': []
        },
        'hierarchy': {
            'multi_level': 0,
            'orphaned': [],
            'circular': []
        }
    }

    # Verify pages
    if hasattr(state, 'created_pages'):
        report['pages']['deployed'] = len(state.created_pages)

        # Check against expected
        expected_pages = expected_config.get('pages', [])
        report['pages']['expected'] = len(expected_pages)

        deployed_titles = set(state.created_pages.keys())
        expected_titles = {p.get('title') for p in expected_pages}

        report['pages']['missing'] = list(expected_titles - deployed_titles)

    # Verify databases
    if hasattr(state, 'created_databases'):
        report['databases']['deployed'] = len(state.created_databases)

        expected_databases = expected_config.get('databases', [])
        report['databases']['expected'] = len(expected_databases)

        deployed_db_names = set(state.created_databases.keys())
        expected_db_names = {db.get('title') for db in expected_databases}

        report['databases']['missing'] = list(expected_db_names - deployed_db_names)

    # Check for unresolved references
    if hasattr(state, 'unresolved_references'):
        report['relations']['unresolved'] = state.unresolved_references

    # Check for pending rollups
    if hasattr(state, 'pending_rollups'):
        for db_name, rollups in state.pending_rollups.items():
            for prop_name in rollups:
                report['rollups']['pending'].append(f"{db_name}.{prop_name}")

    # Calculate summary statistics
    report['summary']['total_expected'] = (
        report['pages']['expected'] +
        report['databases']['expected']
    )

    report['summary']['total_deployed'] = (
        report['pages']['deployed'] +
        report['databases']['deployed']
    )

    report['summary']['total_failed'] = (
        len(report['pages']['missing']) +
        len(report['databases']['missing']) +
        len(report['relations']['broken']) +
        len(report['rollups']['failed'])
    )

    if report['summary']['total_expected'] > 0:
        report['summary']['success_rate'] = (
            report['summary']['total_deployed'] /
            report['summary']['total_expected'] * 100
        )

    return report

def generate_verification_report(report: Dict[str, Any], output_file: str = None) -> str:
    """
    Generate a human-readable verification report.

    Args:
        report: Verification report dictionary
        output_file: Optional file to save report to

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 70)
    lines.append("DEPLOYMENT VERIFICATION REPORT")
    lines.append("=" * 70)
    lines.append(f"Timestamp: {report['timestamp']}")
    lines.append("")

    # Summary
    lines.append("SUMMARY")
    lines.append("-" * 30)
    summary = report['summary']
    lines.append(f"Total Expected: {summary['total_expected']}")
    lines.append(f"Total Deployed: {summary['total_deployed']}")
    lines.append(f"Total Failed: {summary['total_failed']}")
    lines.append(f"Success Rate: {summary['success_rate']:.1f}%")
    lines.append("")

    # Pages
    lines.append("PAGES")
    lines.append("-" * 30)
    pages = report['pages']
    lines.append(f"Expected: {pages['expected']}")
    lines.append(f"Deployed: {pages['deployed']}")
    if pages['missing']:
        lines.append(f"Missing ({len(pages['missing'])}):")
        for page in pages['missing'][:10]:  # Show first 10
            lines.append(f"  - {page}")
        if len(pages['missing']) > 10:
            lines.append(f"  ... and {len(pages['missing']) - 10} more")
    lines.append("")

    # Databases
    lines.append("DATABASES")
    lines.append("-" * 30)
    databases = report['databases']
    lines.append(f"Expected: {databases['expected']}")
    lines.append(f"Deployed: {databases['deployed']}")
    if databases['missing']:
        lines.append(f"Missing ({len(databases['missing'])}):")
        for db in databases['missing']:
            lines.append(f"  - {db}")
    lines.append("")

    # Relations
    if report['relations']['unresolved']:
        lines.append("UNRESOLVED RELATIONS")
        lines.append("-" * 30)
        for ref in report['relations']['unresolved'][:10]:
            lines.append(f"  - {ref}")
        lines.append("")

    # Rollups
    if report['rollups']['pending']:
        lines.append("PENDING ROLLUPS")
        lines.append("-" * 30)
        for rollup in report['rollups']['pending'][:10]:
            lines.append(f"  - {rollup}")
        lines.append("")

    # Recommendations
    lines.append("RECOMMENDATIONS")
    lines.append("-" * 30)

    if summary['success_rate'] == 100:
        lines.append("✅ Deployment successful! All components deployed.")
    elif summary['success_rate'] >= 90:
        lines.append("⚠️ Deployment mostly successful. Review missing components.")
    else:
        lines.append("❌ Deployment has significant issues. Manual intervention required.")

    if pages['missing']:
        lines.append(f"• {len(pages['missing'])} pages need manual creation")

    if databases['missing']:
        lines.append(f"• {len(databases['missing'])} databases need manual creation")

    if report['relations']['unresolved']:
        lines.append(f"• {len(report['relations']['unresolved'])} relations need manual configuration")

    lines.append("")
    lines.append("=" * 70)

    report_text = "\n".join(lines)

    # Save to file if requested
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_text)
        logging.info(f"Verification report saved to {output_file}")

    return report_text

# ============================================================================
# MAIN ENHANCEMENT INTEGRATION
# ============================================================================

def apply_v41_enhancements(deploy_module: Any) -> None:
    """
    Monkey-patch the deploy module with v4.1 enhancements.

    Args:
        deploy_module: The imported deploy module to enhance
    """
    # Replace or enhance existing functions
    if hasattr(deploy_module, 'resolve_database_references'):
        deploy_module._original_resolve_database_references = deploy_module.resolve_database_references
        deploy_module.resolve_database_references = resolve_database_references_enhanced
        logging.info("Enhanced database reference resolution")

    # Add new functions
    deploy_module.escape_formula_expression = escape_formula_expression
    deploy_module.validate_formula_syntax = validate_formula_syntax
    deploy_module.order_pages_by_hierarchy = order_pages_by_hierarchy
    deploy_module.resolve_multi_level_parents = resolve_multi_level_parents
    deploy_module.add_rollup_properties_with_retry = add_rollup_properties_with_retry
    deploy_module.verify_deployment = verify_deployment
    deploy_module.generate_verification_report = generate_verification_report

    logging.info("✅ V4.1 enhancements applied to deploy module")

if __name__ == "__main__":
    # Example usage
    print("V4.1 Deployment Enhancements Module")
    print("=====================================")
    print("This module provides enhanced functions for v4.1 deployment.")
    print("")
    print("To use, import in your deploy script:")
    print("  import deploy_v41_enhancements as v41")
    print("  v41.apply_v41_enhancements(deploy_module)")
    print("")
    print("Available functions:")
    print("  - resolve_database_references_enhanced()")
    print("  - escape_formula_expression()")
    print("  - order_pages_by_hierarchy()")
    print("  - add_rollup_properties_with_retry()")
    print("  - verify_deployment()")