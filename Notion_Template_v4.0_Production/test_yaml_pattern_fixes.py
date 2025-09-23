#!/usr/bin/env python3
"""
Test to verify all YAML pattern fixes work correctly
Tests the 7 critical issues found in the 36 YAML files
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to sys.path to import deploy module
sys.path.insert(0, str(Path(__file__).parent))

try:
    from deploy import (
        process_formula_placeholder,
        process_formula_substitution,
        convert_legacy_block_format,
        build_block,
        build_property_schema
    )
except ImportError as e:
    print(f"❌ Failed to import deploy module: {e}")
    sys.exit(1)


def test_formula_placeholders():
    """Test {{formula:}} placeholder processing"""
    print("\n1. Testing {{formula:}} placeholder processing:")

    # Test simple formula
    text = "Response Time: {{formula:avg(response_times)}}ms"
    result = process_formula_placeholder(text)
    assert result == "Response Time: [Formula: avg(response_times)]ms"
    print("✅ Simple formula placeholder works")

    # Test complex nested structure with formulas
    data = {
        'blocks': [
            {
                'type': 'callout',
                'content': 'Score: {{formula:calculate_score()}} | Target: {{formula:target_value}}'
            }
        ]
    }
    processed = process_formula_substitution(data)
    assert processed['blocks'][0]['content'] == 'Score: [Formula: calculate_score()] | Target: [Formula: target_value]'
    print("✅ Nested formula substitution works")

    return True


def test_embed_blocks():
    """Test proper embed block support"""
    print("\n2. Testing embed blocks:")

    # Test valid embed
    block = {
        'type': 'embed',
        'url': 'https://placeholder-performance-dashboard.com'
    }
    built = build_block(block)
    assert 'embed' in built
    assert built['embed']['url'] == 'https://placeholder-performance-dashboard.com'
    print("✅ Valid embed block works")

    # Test embed without URL
    block = {
        'type': 'embed',
        'content': 'some-non-url-content'
    }
    built = build_block(block)
    assert 'paragraph' in built  # Should fallback
    assert '[EMBED: No valid URL provided]' in built['paragraph']['rich_text'][0]['text']['content']
    print("✅ Invalid embed fallback works")

    return True


def test_table_blocks():
    """Test proper table block support"""
    print("\n3. Testing table blocks:")

    # Test valid table
    block = {
        'type': 'table',
        'rows': [
            {'cells': ['Metric', 'Current', 'Target', 'Status']},
            {'cells': ['Response Time', '250ms', '<500ms', 'Good']},
            {'cells': ['Memory Usage', '45%', '<80%', 'Good']}
        ],
        'has_header': True
    }
    built = build_block(block)
    assert 'table' in built
    assert built['table']['table_width'] == 4
    assert built['table']['has_column_header'] == True
    assert len(built['table']['children']) == 3
    assert built['table']['children'][0]['cells'][0][0]['text']['content'] == 'Metric'
    print("✅ Table block with rows works")

    # Test empty table
    block = {
        'type': 'table',
        'rows': []
    }
    built = build_block(block)
    assert 'paragraph' in built  # Should fallback for empty table
    print("✅ Empty table fallback works")

    return True


def test_rollup_property():
    """Test rollup property type support"""
    print("\n4. Testing rollup property type:")

    prop_def = {
        'type': 'rollup',
        'relation_property_name': 'Projects',
        'rollup_property_name': 'Status',
        'function': 'count'
    }

    built = build_property_schema(prop_def)
    assert 'rollup' in built
    assert built['rollup']['relation_property_name'] == 'Projects'
    assert built['rollup']['rollup_property_name'] == 'Status'
    assert built['rollup']['function'] == 'count'
    print("✅ Rollup property type works")

    return True


def test_people_property():
    """Test people property type support"""
    print("\n5. Testing people property type:")

    prop_def = {
        'type': 'people'
    }

    built = build_property_schema(prop_def)
    assert 'people' in built
    print("✅ People property type works")

    return True


def test_last_edited_time_property():
    """Test last_edited_time property type support"""
    print("\n6. Testing last_edited_time property type:")

    prop_def = {
        'type': 'last_edited_time'
    }

    built = build_property_schema(prop_def)
    assert 'last_edited_time' in built
    print("✅ Last edited time property type works")

    return True


def test_legacy_heading_format():
    """Test conversion of old heading format"""
    print("\n7. Testing legacy heading format conversion:")

    # Test H2 conversion
    block = {
        'heading': 'Diagnostics Overview',
        'type': 'H2'
    }
    converted = convert_legacy_block_format(block)
    assert converted['type'] == 'heading_2'
    assert converted['content'] == 'Diagnostics Overview'
    assert 'heading' not in converted
    print("✅ H2 -> heading_2 conversion works")

    # Test H1 conversion
    block = {'type': 'H1', 'heading': 'Main Title'}
    converted = convert_legacy_block_format(block)
    assert converted['type'] == 'heading_1'
    assert converted['content'] == 'Main Title'
    print("✅ H1 -> heading_1 conversion works")

    # Test H3 conversion
    block = {'type': 'H3', 'content': 'Already has content'}
    converted = convert_legacy_block_format(block)
    assert converted['type'] == 'heading_3'
    assert converted['content'] == 'Already has content'
    print("✅ H3 -> heading_3 conversion works")

    # Test that it's integrated in build_block
    block = {'type': 'H2', 'heading': 'Test Heading'}
    built = build_block(block)
    assert 'heading_2' in built
    assert built['heading_2']['rich_text'][0]['text']['content'] == 'Test Heading'
    print("✅ Legacy format works through build_block")

    return True


def test_all_fixes_together():
    """Test that all fixes work together in a complex scenario"""
    print("\n8. Testing all fixes working together:")

    # Complex page with multiple patterns
    page_data = {
        'title': 'Test Page',
        'blocks': [
            {
                'type': 'H1',
                'heading': 'Performance Report'
            },
            {
                'type': 'callout',
                'content': 'Score: {{formula:performance_score}} | Average: {{formula:avg(metrics)}}'
            },
            {
                'type': 'embed',
                'url': 'https://dashboard.example.com'
            },
            {
                'type': 'table',
                'rows': [
                    {'cells': ['Test', 'Result']},
                    {'cells': ['Speed', '{{formula:speed_calc}}']}
                ]
            }
        ]
    }

    # Process formulas
    page_data = process_formula_substitution(page_data)

    # Build blocks
    built_blocks = []
    for block in page_data['blocks']:
        built_blocks.append(build_block(block))

    # Check H1 was converted
    assert 'heading_1' in built_blocks[0]
    assert built_blocks[0]['heading_1']['rich_text'][0]['text']['content'] == 'Performance Report'

    # Check formulas were processed
    assert '[Formula: performance_score]' in built_blocks[1]['callout']['rich_text'][0]['text']['content']

    # Check embed
    assert 'embed' in built_blocks[2]

    # Check table with formula in cell
    assert 'table' in built_blocks[3]
    assert '[Formula: speed_calc]' in built_blocks[3]['table']['children'][1]['cells'][1][0]['text']['content']

    print("✅ All fixes work together correctly!")

    return True


def main():
    """Run all tests"""
    print("🚀 Testing All YAML Pattern Fixes\n")
    print("=" * 50)

    try:
        # Run all tests
        tests = [
            test_formula_placeholders,
            test_embed_blocks,
            test_table_blocks,
            test_rollup_property,
            test_people_property,
            test_last_edited_time_property,
            test_legacy_heading_format,
            test_all_fixes_together
        ]

        for test in tests:
            if not test():
                print(f"\n❌ Test {test.__name__} failed!")
                return 1

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Formula placeholders working")
        print("✅ Embed blocks properly supported")
        print("✅ Table blocks properly supported")
        print("✅ Rollup property type supported")
        print("✅ People property type supported")
        print("✅ Last edited time property supported")
        print("✅ Legacy heading format converted")
        print("✅ All 7 critical issues FIXED!")
        print("=" * 50)

        return 0

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())