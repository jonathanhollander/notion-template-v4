#!/usr/bin/env python3
"""
Test to verify that variable substitution works in block content
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to sys.path to import deploy module
sys.path.insert(0, str(Path(__file__).parent))

try:
    from deploy import (
        process_variable_substitution,
        process_content_substitution,
        build_block
    )
except ImportError as e:
    print(f"❌ Failed to import deploy module: {e}")
    sys.exit(1)

def test_block_variable_substitution():
    """Test variable substitution in blocks"""
    print("=== Testing Variable Substitution in Blocks ===")

    # Set test environment variables
    os.environ['ADMIN_HELP_URL'] = 'https://admin.example.com'
    os.environ['SUPPORT_EMAIL'] = 'support@example.com'

    # Test 1: Simple paragraph block with variable
    print("\n1. Testing paragraph block with variable:")
    paragraph_block = {
        'type': 'paragraph',
        'content': 'Visit ${ADMIN_HELP_URL}/guides for help or email ${SUPPORT_EMAIL}'
    }

    # Process substitution
    processed = process_content_substitution(paragraph_block)

    assert processed['content'] == 'Visit https://admin.example.com/guides for help or email support@example.com'
    print("✅ Paragraph block variable substitution works")

    # Build the block to ensure it works end-to-end
    built = build_block(processed)
    assert built['paragraph']['rich_text'][0]['text']['content'] == 'Visit https://admin.example.com/guides for help or email support@example.com'
    print("✅ Built paragraph block contains substituted content")

    # Test 2: Heading block with variable
    print("\n2. Testing heading block with variable:")
    heading_block = {
        'type': 'heading_1',
        'content': 'Welcome to ${ADMIN_HELP_URL}'
    }

    processed = process_content_substitution(heading_block)
    assert processed['content'] == 'Welcome to https://admin.example.com'

    built = build_block(processed)
    assert built['heading_1']['rich_text'][0]['text']['content'] == 'Welcome to https://admin.example.com'
    print("✅ Heading block variable substitution works")

    # Test 3: Toggle block with nested children containing variables
    print("\n3. Testing toggle block with nested children:")
    toggle_block = {
        'type': 'toggle',
        'content': 'Admin Resources',
        'children': [
            {
                'type': 'paragraph',
                'content': 'Dashboard: ${ADMIN_HELP_URL}/dashboard'
            },
            {
                'type': 'bulleted_list_item',
                'content': 'Support: ${SUPPORT_EMAIL}'
            }
        ]
    }

    # Process the entire toggle block
    processed = process_content_substitution(toggle_block)

    # Check that nested children were processed
    assert processed['children'][0]['content'] == 'Dashboard: https://admin.example.com/dashboard'
    assert processed['children'][1]['content'] == 'Support: support@example.com'
    print("✅ Toggle block nested children variable substitution works")

    # Test 4: Callout block with variable
    print("\n4. Testing callout block with variable:")
    callout_block = {
        'type': 'callout',
        'content': 'Need help? Visit ${ADMIN_HELP_URL} or contact ${SUPPORT_EMAIL}',
        'icon': '💡',
        'color': 'gray_background'
    }

    processed = process_content_substitution(callout_block)
    assert processed['content'] == 'Need help? Visit https://admin.example.com or contact support@example.com'

    built = build_block(processed)
    assert built['callout']['rich_text'][0]['text']['content'] == 'Need help? Visit https://admin.example.com or contact support@example.com'
    print("✅ Callout block variable substitution works")

    # Test 5: Variable with default value in block
    print("\n5. Testing variable with default value:")
    block_with_default = {
        'type': 'paragraph',
        'content': 'API endpoint: ${API_URL:-https://api.default.com}/v1'
    }

    processed = process_content_substitution(block_with_default)
    assert processed['content'] == 'API endpoint: https://api.default.com/v1'
    print("✅ Default value substitution in blocks works")

    # Test 6: Code block with variable (should preserve content)
    print("\n6. Testing code block with variable:")
    code_block = {
        'type': 'code',
        'content': 'const url = "${ADMIN_HELP_URL}";',
        'language': 'javascript'
    }

    processed = process_content_substitution(code_block)
    assert processed['content'] == 'const url = "https://admin.example.com";'

    built = build_block(processed)
    assert built['code']['rich_text'][0]['text']['content'] == 'const url = "https://admin.example.com";'
    print("✅ Code block variable substitution works")

    # Test 7: Bulleted list with items containing variables
    print("\n7. Testing bulleted list with variable items:")
    list_block = {
        'type': 'bulleted_list',
        'items': [
            'Visit ${ADMIN_HELP_URL}/docs',
            'Email ${SUPPORT_EMAIL} for help',
            'API: ${API_URL:-https://api.default.com}'
        ]
    }

    processed = process_content_substitution(list_block)
    assert processed['items'][0] == 'Visit https://admin.example.com/docs'
    assert processed['items'][1] == 'Email support@example.com for help'
    assert processed['items'][2] == 'API: https://api.default.com'
    print("✅ Bulleted list items variable substitution works")

    print("\n🎉 All block variable substitution tests PASSED!")

    return True

def test_complex_nested_structure():
    """Test deeply nested structure with variables"""
    print("\n=== Testing Complex Nested Structure ===")

    os.environ['BASE_URL'] = 'https://example.com'
    os.environ['API_VERSION'] = 'v2'

    complex_structure = {
        'title': 'API Documentation',
        'blocks': [
            {
                'type': 'heading_1',
                'content': 'API Endpoint: ${BASE_URL}/api/${API_VERSION}'
            },
            {
                'type': 'toggle',
                'content': 'Authentication',
                'children': [
                    {
                        'type': 'paragraph',
                        'content': 'Use Bearer token from ${BASE_URL}/auth'
                    },
                    {
                        'type': 'code',
                        'content': 'curl ${BASE_URL}/api/${API_VERSION}/users',
                        'language': 'bash'
                    }
                ]
            },
            {
                'type': 'callout',
                'content': 'Default endpoint: ${DEFAULT_API:-https://default.api.com}',
                'icon': '🔔'
            }
        ]
    }

    # Process the entire structure
    processed = process_content_substitution(complex_structure)

    # Verify all substitutions
    assert processed['blocks'][0]['content'] == 'API Endpoint: https://example.com/api/v2'
    assert processed['blocks'][1]['children'][0]['content'] == 'Use Bearer token from https://example.com/auth'
    assert processed['blocks'][1]['children'][1]['content'] == 'curl https://example.com/api/v2/users'
    assert processed['blocks'][2]['content'] == 'Default endpoint: https://default.api.com'

    print("✅ Complex nested structure substitution works")
    print("✅ All nested levels properly processed")

    return True

def main():
    """Run all tests"""
    print("🚀 Testing Block Variable Substitution\n")

    try:
        # Run basic block tests
        if not test_block_variable_substitution():
            return 1

        # Run complex nested tests
        if not test_complex_nested_structure():
            return 1

        print("\n" + "="*50)
        print("✅ ALL TESTS PASSED!")
        print("✅ Variable substitution in blocks is working correctly")
        print("✅ Nested structures are properly processed")
        print("✅ Default values are handled properly")
        print("="*50)

        return 0

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())