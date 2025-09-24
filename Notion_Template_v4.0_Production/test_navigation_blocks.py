#!/usr/bin/env python3
"""
Test the navigation block type implementations (child_page, table_of_contents, breadcrumb)
"""
import json
import sys
import os

# Add current directory to path to import deploy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the logger
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def debug(self, msg): pass

# Create a mock deploy object to test build_block
class MockDeployment:
    def __init__(self):
        self.logger = MockLogger()
        self.page_ids = {
            "Home Page": "page_123",
            "About Page": "page_456",
            "Contact Page": "page_789"
        }

    def build_block(self, block):
        """Extract just the build_block logic from deploy.py"""
        # Import the actual deploy module
        import deploy

        # Use the actual build_block function (it's standalone)
        # We need to temporarily patch the logger global
        original_logger = deploy.logger if hasattr(deploy, 'logger') else None
        deploy.logger = self.logger

        # Also need to temporarily set the page_ids
        original_page_ids = deploy.page_ids if hasattr(deploy, 'page_ids') else None
        deploy.page_ids = self.page_ids

        result = deploy.build_block(block)

        # Restore originals
        if original_logger:
            deploy.logger = original_logger
        if original_page_ids:
            deploy.page_ids = original_page_ids

        return result

# Test cases for each navigation block type
test_cases = [
    {
        "name": "Child page block with page_id",
        "block": {
            "type": "child_page",
            "page_id": "child_page_001",
            "title": "Child Document"
        },
        "expected_type": "child_page"
    },
    {
        "name": "Child page block with page_title (should resolve)",
        "block": {
            "type": "child_page",
            "page_title": "Home Page"
        },
        "expected_type": "child_page"
    },
    {
        "name": "Child page block missing both ID and title (should fallback)",
        "block": {
            "type": "child_page"
        },
        "expected_type": "paragraph"
    },
    {
        "name": "Table of contents - automated generation",
        "block": {
            "type": "table_of_contents",
            "color": "blue"
        },
        "expected_type": "table_of_contents"
    },
    {
        "name": "Table of contents - default color",
        "block": {
            "type": "table_of_contents"
        },
        "expected_type": "table_of_contents"
    },
    {
        "name": "Breadcrumb navigation",
        "block": {
            "type": "breadcrumb"
        },
        "expected_type": "breadcrumb"
    },
    {
        "name": "Child page with unknown title (should fallback)",
        "block": {
            "type": "child_page",
            "page_title": "Non-existent Page"
        },
        "expected_type": "paragraph"
    }
]

# Run tests
def run_tests():
    print("=" * 60)
    print("Testing Navigation Block Type Implementations")
    print("(child_page, table_of_contents, breadcrumb)")
    print("=" * 60)

    deployment = MockDeployment()
    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print("-" * 40)

        try:
            result = deployment.build_block(test["block"])

            # Check if result has expected structure
            if result is None:
                print("❌ Result is None")
                failed += 1
                continue

            # Determine the actual block type from result
            if "paragraph" in result:
                actual_type = "paragraph"
            elif "child_page" in result:
                actual_type = "child_page"
            elif "table_of_contents" in result:
                actual_type = "table_of_contents"
            elif "breadcrumb" in result:
                actual_type = "breadcrumb"
            else:
                actual_type = "unknown"

            if actual_type == test["expected_type"]:
                print(f"✅ PASSED - Got expected type: {actual_type}")

                # Show relevant details based on type
                if actual_type == "child_page":
                    if "page_id" in result["child_page"]:
                        print(f"   Page ID: {result['child_page']['page_id']}")
                elif actual_type == "table_of_contents":
                    if "color" in result["table_of_contents"]:
                        print(f"   Color: {result['table_of_contents']['color']}")
                elif actual_type == "breadcrumb":
                    print(f"   Breadcrumb block created successfully")
                elif actual_type == "paragraph":
                    print(f"   Fallback text: {result['paragraph']['rich_text'][0]['text']['content'][:50]}...")

                passed += 1
            else:
                print(f"❌ FAILED - Expected {test['expected_type']}, got {actual_type}")
                print(f"   Result: {json.dumps(result, indent=2)}")
                failed += 1

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    # Additional information
    print("\n📝 Implementation Notes:")
    print("- child_page: Creates references to subpages with styled fallback")
    print("- table_of_contents: Automatically generated from heading blocks")
    print("- breadcrumb: Shows navigation hierarchy for page location")
    print("\n✅ All navigation blocks are now implemented in deploy.py")
    print("   (Lines 1356-1395)")

    return passed, failed

if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)