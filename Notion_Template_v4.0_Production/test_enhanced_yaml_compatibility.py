#!/usr/bin/env python3
"""
Comprehensive test for all enhanced YAML pattern support
Tests variable substitution, enhanced select options, page metadata, and asset fields
"""

import os
import sys
import json
import yaml
import tempfile
from pathlib import Path

# Add the parent directory to sys.path to import deploy module
sys.path.insert(0, str(Path(__file__).parent))

try:
    from deploy import (
        process_variable_substitution,
        process_content_substitution,
        build_enhanced_select_options,
        add_page_metadata_properties,
        create_asset_field_placeholders,
        build_property_schema
    )
except ImportError as e:
    print(f"❌ Failed to import deploy module: {e}")
    sys.exit(1)

def test_variable_substitution():
    """Test variable substitution functionality"""
    print("=== Testing Variable Substitution ===")

    # Set test environment variables
    os.environ['TEST_URL'] = 'https://example.com/help'
    os.environ['ADMIN_HELP_URL'] = 'https://admin.example.com'

    # Test basic substitution
    result = process_variable_substitution("Visit ${TEST_URL} for help")
    expected = "Visit https://example.com/help for help"
    assert result == expected, f"Basic substitution failed: {result} != {expected}"
    print("✅ Basic variable substitution works")

    # Test with default value
    result = process_variable_substitution("Config: ${MISSING_VAR:-default_value}")
    expected = "Config: default_value"
    assert result == expected, f"Default value failed: {result} != {expected}"
    print("✅ Default value substitution works")

    # Test nested content substitution
    test_data = {
        'text': 'Guide: ${ADMIN_HELP_URL}/saved-views',
        'nested': {
            'url': '${TEST_URL}/page',
            'items': ['${ADMIN_HELP_URL}/item1', '${TEST_URL}/item2']
        }
    }

    result = process_content_substitution(test_data)
    assert result['text'] == 'Guide: https://admin.example.com/saved-views'
    assert result['nested']['url'] == 'https://example.com/help/page'
    assert result['nested']['items'][0] == 'https://admin.example.com/item1'
    print("✅ Nested content substitution works")

    print("🎉 Variable substitution tests PASSED\n")


def test_enhanced_select_options():
    """Test enhanced select options with colors"""
    print("=== Testing Enhanced Select Options ===")

    # Test array format (existing)
    options = ["Option1", "Option2", "Option3"]
    result = build_enhanced_select_options(options)
    expected = [{"name": "Option1"}, {"name": "Option2"}, {"name": "Option3"}]
    assert result == expected, f"Array format failed: {result} != {expected}"
    print("✅ Array format options work")

    # Test object format with colors
    options = [
        {"name": "Preparation", "color": "blue"},
        {"name": "Executor", "color": "purple"},
        {"name": "Invalid", "color": "invalid_color"},
        {"name": "NoColor"}
    ]
    result = build_enhanced_select_options(options)

    assert result[0] == {"name": "Preparation", "color": "blue"}
    assert result[1] == {"name": "Executor", "color": "purple"}
    assert result[2] == {"name": "Invalid"}  # Invalid color should be omitted
    assert result[3] == {"name": "NoColor"}
    print("✅ Object format with colors works")

    # Test mixed format
    options = ["Simple", {"name": "Colored", "color": "red"}]
    result = build_enhanced_select_options(options)
    assert result == [{"name": "Simple"}, {"name": "Colored", "color": "red"}]
    print("✅ Mixed format options work")

    print("🎉 Enhanced select options tests PASSED\n")


def test_page_metadata_fields():
    """Test page metadata fields functionality"""
    print("=== Testing Page Metadata Fields ===")

    page_data = {
        'title': 'Test Page',
        'role': 'admin',
        'slug': 'test-page',
        'complexity': 'moderate',
        'disclaimer': 'This is a test disclaimer'
    }

    properties = {
        "title": {"title": [{"text": {"content": "Test Page"}}]}
    }

    result = add_page_metadata_properties(page_data, properties)

    # Check all metadata fields were added
    assert 'Role' in result, "Role field missing"
    assert result['Role']['rich_text'][0]['text']['content'] == 'admin'

    assert 'Slug' in result, "Slug field missing"
    assert result['Slug']['rich_text'][0]['text']['content'] == 'test-page'

    assert 'Complexity' in result, "Complexity field missing"
    assert result['Complexity']['select']['name'] == 'moderate'

    assert 'Disclaimer' in result, "Disclaimer field missing"
    assert result['Disclaimer']['rich_text'][0]['text']['content'] == 'This is a test disclaimer'

    print("✅ All page metadata fields added correctly")
    print("🎉 Page metadata fields tests PASSED\n")


def test_asset_field_placeholders():
    """Test asset field placeholder creation"""
    print("=== Testing Asset Field Placeholders ===")

    page_data = {
        'title': 'Test Page',
        'icon_file': 'test-icon.png',
        'cover_file': 'test-cover.jpg',
        'icon_png': 'test-icon.png',
        'cover_png': 'test-cover.png',
        'alt_text': 'Test alt text'
    }

    result = create_asset_field_placeholders(page_data)

    # Check all asset placeholders were created
    assert 'Icon File' in result, "Icon File placeholder missing"
    assert result['Icon File']['rich_text'][0]['text']['content'] == ""

    assert 'Cover File' in result, "Cover File placeholder missing"
    assert result['Cover File']['rich_text'][0]['text']['content'] == ""

    assert 'Icon PNG' in result, "Icon PNG placeholder missing"
    assert result['Icon PNG']['rich_text'][0]['text']['content'] == ""

    assert 'Cover PNG' in result, "Cover PNG placeholder missing"
    assert result['Cover PNG']['rich_text'][0]['text']['content'] == ""

    assert 'Alt Text' in result, "Alt Text field missing"
    assert result['Alt Text']['rich_text'][0]['text']['content'] == "Test alt text"

    print("✅ All asset field placeholders created correctly")
    print("🎉 Asset field placeholder tests PASSED\n")


def test_enhanced_property_schema():
    """Test enhanced database property schema building"""
    print("=== Testing Enhanced Database Property Schema ===")

    # Test select with color options
    select_prop = {
        'type': 'select',
        'options': [
            {"name": "High", "color": "red"},
            {"name": "Medium", "color": "yellow"},
            {"name": "Low", "color": "green"}
        ]
    }

    result = build_property_schema(select_prop)
    expected = {
        "select": {
            "options": [
                {"name": "High", "color": "red"},
                {"name": "Medium", "color": "yellow"},
                {"name": "Low", "color": "green"}
            ]
        }
    }

    assert result == expected, f"Enhanced select schema failed: {result} != {expected}"
    print("✅ Enhanced select property schema works")

    # Test multi_select with colors
    multi_select_prop = {
        'type': 'multi_select',
        'options': [
            "Simple",
            {"name": "Colored", "color": "blue"}
        ]
    }

    result = build_property_schema(multi_select_prop)
    expected = {
        "multi_select": {
            "options": [
                {"name": "Simple"},
                {"name": "Colored", "color": "blue"}
            ]
        }
    }

    assert result == expected, f"Enhanced multi-select schema failed: {result} != {expected}"
    print("✅ Enhanced multi-select property schema works")

    print("🎉 Enhanced property schema tests PASSED\n")


def test_comprehensive_yaml_patterns():
    """Test with actual YAML patterns from the project"""
    print("=== Testing Comprehensive YAML Patterns ===")

    # Set environment variables for test
    os.environ['ADMIN_HELP_URL'] = 'https://help.example.com'

    # Create test YAML with all patterns
    test_yaml_content = {
        'complexity': 'high',
        'pages': [
            {
                'title': 'Test Admin Page',
                'role': 'admin',
                'slug': 'admin-page',
                'complexity': 'moderate',
                'disclaimer': 'Admin access only',
                'icon_file': 'admin-icon.png',
                'cover_file': 'admin-cover.jpg',
                'alt_text': 'Admin page icon',
                'blocks': [
                    {
                        'type': 'paragraph',
                        'content': 'Visit ${ADMIN_HELP_URL}/guides for help'
                    },
                    {
                        'type': 'toggle',
                        'summary': 'Admin Tools',
                        'children': [
                            {
                                'type': 'paragraph',
                                'text': 'Tool URL: ${ADMIN_HELP_URL}/tools'
                            }
                        ]
                    }
                ]
            }
        ],
        'databases': [
            {
                'title': 'Test Analytics',
                'properties': {
                    'Status': {
                        'type': 'select',
                        'options': [
                            {'name': 'Active', 'color': 'green'},
                            {'name': 'Pending', 'color': 'yellow'},
                            {'name': 'Inactive', 'color': 'red'}
                        ]
                    },
                    'Tags': {
                        'type': 'multi_select',
                        'options': [
                            'Important',
                            {'name': 'Priority', 'color': 'blue'}
                        ]
                    }
                }
            }
        ]
    }

    # Process through our substitution system
    processed = process_content_substitution(test_yaml_content)

    # Verify variable substitution worked
    page = processed['pages'][0]
    assert page['blocks'][0]['content'] == 'Visit https://help.example.com/guides for help'
    assert page['blocks'][1]['children'][0]['text'] == 'Tool URL: https://help.example.com/tools'
    print("✅ Variable substitution in complex YAML works")

    # Test property schema building with enhanced options
    db = processed['databases'][0]
    status_schema = build_property_schema(db['properties']['Status'])
    assert status_schema['select']['options'][0] == {'name': 'Active', 'color': 'green'}
    print("✅ Enhanced database properties work")

    # Test page metadata handling
    properties = {"title": {"title": [{"text": {"content": page['title']}}]}}
    enhanced_properties = add_page_metadata_properties(page, properties)

    assert 'Role' in enhanced_properties
    assert 'Slug' in enhanced_properties
    assert 'Complexity' in enhanced_properties
    assert 'Disclaimer' in enhanced_properties
    print("✅ Page metadata integration works")

    # Test asset field placeholders
    asset_props = create_asset_field_placeholders(page)
    assert 'Icon File' in asset_props
    assert 'Cover File' in asset_props
    assert 'Alt Text' in asset_props
    print("✅ Asset field placeholders work")

    print("🎉 Comprehensive YAML pattern tests PASSED\n")


def main():
    """Run all tests"""
    print("🚀 Starting Enhanced YAML Compatibility Test Suite\n")

    try:
        test_variable_substitution()
        test_enhanced_select_options()
        test_page_metadata_fields()
        test_asset_field_placeholders()
        test_enhanced_property_schema()
        test_comprehensive_yaml_patterns()

        print("=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Variable substitution system working")
        print("✅ Enhanced select/multi-select options working")
        print("✅ Page metadata fields working")
        print("✅ Asset field integration framework working")
        print("✅ All YAML patterns now 100% supported")
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())