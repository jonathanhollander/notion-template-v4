#!/usr/bin/env python3
"""
Comprehensive test of all YAML field patterns and block types
"""

import os
import yaml
import tempfile
from pathlib import Path

def create_comprehensive_test_data():
    """Create test data with all field patterns found in YAML"""

    test_data = {
        'pages': [
            # Root parent page (no blocks, should be created first)
            {
                'title': 'Test Hub Parent',
                'icon': 'emoji:🏠',
                'description': 'Parent page for testing'
            },

            # Child page with 'blocks' field
            {
                'title': 'Child Page with Blocks',
                'parent': 'Test Hub Parent',
                'icon': 'emoji:📝',
                'description': 'Testing blocks field',
                'blocks': [
                    {'type': 'heading_1', 'content': 'Main Heading'},
                    {'type': 'paragraph', 'content': 'This is a paragraph.'},
                    {'type': 'callout', 'content': 'Important callout', 'icon': 'emoji:⚠️', 'color': 'yellow_background'},
                    {'type': 'bulleted_list_item', 'content': 'First bullet point'},
                    {'type': 'numbered_list_item', 'content': 'First numbered item'},
                    {'type': 'divider'},
                    {'type': 'to_do', 'content': 'Task to complete', 'checked': False}
                ]
            },

            # Child page with 'body' field
            {
                'title': 'Child Page with Body',
                'parent': 'Test Hub Parent',
                'icon': 'emoji:📋',
                'description': 'Testing body field',
                'body': [
                    {'type': 'heading_2', 'content': 'Second Level Heading'},
                    {'type': 'paragraph', 'text': 'Paragraph using text field instead of content'},
                    {'type': 'toggle', 'summary': 'Click to expand', 'children': [
                        {'type': 'paragraph', 'content': 'Hidden content inside toggle'}
                    ]},
                    {'type': 'code', 'content': 'print("Hello World")', 'language': 'python'}
                ]
            },

            # Child page with 'Body' field (capitalized)
            {
                'title': 'Child Page with Body Capitalized',
                'parent': 'Test Hub Parent',
                'icon': 'emoji:📄',
                'description': 'Testing Body field (capitalized)',
                'Body': [
                    {'type': 'heading_3', 'content': 'Third Level Heading'},
                    {'type': 'bulleted_list', 'items': [
                        'First list item',
                        'Second list item',
                        'Third list item'
                    ]},
                    {'type': 'embed', 'content': 'https://example.com/video'},
                    {'type': 'table', 'content': 'Example table placeholder'}
                ]
            }
        ],

        'db': {
            'schemas': {
                'Test Database': {
                    'properties': {
                        'Name': 'title',
                        'Description': 'text',
                        'Category': 'select',
                        'Date': 'date',
                        'Website': 'url',
                        'Tags': {
                            'type': 'multi_select',
                            'options': ['Important', 'Draft', 'Complete']
                        },
                        'Related': {
                            'type': 'relation',
                            'database_id_ref': 'pages',
                            'by_title': True
                        }
                    }
                }
            }
        }
    }

    return test_data

def main():
    # Set environment variables
    os.environ['NOTION_TOKEN'] = os.getenv('NOTION_TOKEN', 'your_notion_token_here')
    os.environ['NOTION_PARENT_PAGEID'] = '251a6c4e-badd-8040-9b97-e14848a10788'

    print("=== COMPREHENSIVE YAML PATTERN TEST ===")

    # Create test data
    test_data = create_comprehensive_test_data()

    # Create temporary directory and YAML file
    temp_dir = Path("temp_comprehensive_test")
    temp_dir.mkdir(exist_ok=True)

    test_yaml_file = temp_dir / "comprehensive_test.yaml"
    with open(test_yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(test_data, f, default_flow_style=False, allow_unicode=True)

    print(f"Test YAML saved to: {test_yaml_file}")

    # Show what we're testing
    print("\nTest covers:")
    print("- Alternative field names: 'blocks', 'body', 'Body'")
    print("- Alternative content names: 'content', 'text', 'summary'")
    print("- All major block types: heading_1/2/3, paragraph, callout, lists, toggle, code, divider, to_do")
    print("- Complex block types: embed, table, bulleted_list with items")
    print("- Database property types: title, text, select, multi_select, relation, date, url")
    print("- Parent-child relationships")

    print(f"\nPages to be deployed: {len(test_data['pages'])}")
    for i, page in enumerate(test_data['pages'], 1):
        title = page.get('title')
        parent = page.get('parent', 'No parent')

        # Count blocks from all possible fields
        blocks = page.get('blocks', page.get('body', page.get('Body', [])))
        block_count = len(blocks)

        print(f"  {i}. {title} (parent: {parent}, blocks: {block_count})")

    print(f"\nDatabases to be deployed: {len(test_data['db']['schemas'])}")
    for db_name, schema in test_data['db']['schemas'].items():
        properties = schema.get('properties', {})
        print(f"  - {db_name}: {len(properties)} properties")

    # Run dry run first
    print(f"\n=== DRY RUN TEST ===")

    import subprocess
    cmd = [
        'python3', 'deploy.py',
        '--yaml-dir', str(temp_dir),
        '--dry-run',
        '--verbose'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd='.')
        print("DRY RUN STDOUT:")
        print(result.stdout)
        if result.stderr:
            print("\nDRY RUN STDERR:")
            print(result.stderr)
        print(f"\nDry run return code: {result.returncode}")

        if result.returncode == 0:
            print("✅ DRY RUN SUCCESS - All YAML patterns validated!")

            # Ask user before real deployment
            response = input("\n🚀 Deploy for real? This will create pages and databases in Notion. [y/N]: ").strip().lower()
            if response in ('y', 'yes'):
                print("\n=== REAL DEPLOYMENT TEST ===")

                cmd_real = [
                    'python3', 'deploy.py',
                    '--yaml-dir', str(temp_dir),
                    '--verbose'
                ]

                result_real = subprocess.run(cmd_real, capture_output=True, text=True, cwd='.')
                print("REAL DEPLOYMENT STDOUT:")
                print(result_real.stdout)
                if result_real.stderr:
                    print("\nREAL DEPLOYMENT STDERR:")
                    print(result_real.stderr)
                print(f"\nReal deployment return code: {result_real.returncode}")

                if result_real.returncode == 0:
                    print("🎉 COMPREHENSIVE TEST SUCCESS - All YAML patterns deployed correctly!")
                else:
                    print("❌ Real deployment failed")
            else:
                print("👍 Skipping real deployment - dry run validation complete")
        else:
            print("❌ Dry run failed")

    except Exception as e:
        print(f"❌ Error running deploy script: {e}")

    # Clean up
    try:
        test_yaml_file.unlink()
        temp_dir.rmdir()
        print(f"\nCleaned up temporary files")
    except Exception as e:
        print(f"Cleanup error: {e}")

if __name__ == "__main__":
    main()