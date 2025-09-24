#!/usr/bin/env python3
"""
Test the new block type implementations added to deploy.py
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
        self.page_ids = {"Home Page": "page_123", "About Page": "page_456"}

    def build_block(self, block):
        """Extract just the build_block logic from deploy.py"""
        # Import the actual deploy module
        import deploy

        # Use the actual build_block function (it's standalone)
        # We need to temporarily patch the logger global
        original_logger = deploy.logger if hasattr(deploy, 'logger') else None
        deploy.logger = self.logger

        result = deploy.build_block(block)

        # Restore original logger
        if original_logger:
            deploy.logger = original_logger

        return result

# Test cases for each new block type
test_cases = [
    {
        "name": "Image block with URL and caption",
        "block": {
            "type": "image",
            "url": "https://example.com/image.jpg",
            "caption": "Test image caption"
        },
        "expected_type": "image"
    },
    {
        "name": "File block with external URL",
        "block": {
            "type": "file",
            "file_url": "https://example.com/document.pdf",
            "name": "Important Document.pdf"
        },
        "expected_type": "file"
    },
    {
        "name": "PDF block with URL",
        "block": {
            "type": "pdf",
            "pdf_url": "https://example.com/estate-plan.pdf",
            "title": "Estate Planning Guide"
        },
        "expected_type": "pdf"
    },
    {
        "name": "Bookmark block with URL and title",
        "block": {
            "type": "bookmark",
            "url": "https://www.irs.gov/forms",
            "title": "IRS Forms and Publications"
        },
        "expected_type": "bookmark"
    },
    {
        "name": "Quote block with author",
        "block": {
            "type": "quote",
            "text": "The best time to plant a tree was 20 years ago. The second best time is now.",
            "author": "Chinese Proverb"
        },
        "expected_type": "quote"
    },
    {
        "name": "Link to page by ID",
        "block": {
            "type": "link_to_page",
            "page_id": "page_789",
            "title": "Related Document"
        },
        "expected_type": "link_to_page"
    },
    {
        "name": "Link to page by title (should resolve)",
        "block": {
            "type": "link_to_page",
            "page_title": "Home Page"
        },
        "expected_type": "link_to_page"
    },
    {
        "name": "Column list (placeholder for now)",
        "block": {
            "type": "column_list",
            "columns": [
                {"children": [{"type": "paragraph", "content": "Column 1"}]},
                {"children": [{"type": "paragraph", "content": "Column 2"}]}
            ]
        },
        "expected_type": "paragraph"  # Falls back to paragraph for now
    },
    {
        "name": "Image block missing URL (should fallback)",
        "block": {
            "type": "image",
            "caption": "Missing image"
        },
        "expected_type": "paragraph"
    },
    {
        "name": "File block missing URL (should fallback)",
        "block": {
            "type": "file",
            "name": "Missing file.doc"
        },
        "expected_type": "paragraph"
    }
]

# Run tests
def run_tests():
    print("=" * 60)
    print("Testing New Block Type Implementations")
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
            elif "image" in result:
                actual_type = "image"
            elif "file" in result:
                actual_type = "file"
            elif "pdf" in result:
                actual_type = "pdf"
            elif "bookmark" in result:
                actual_type = "bookmark"
            elif "quote" in result:
                actual_type = "quote"
            elif "link_to_page" in result:
                actual_type = "link_to_page"
            else:
                actual_type = "unknown"

            if actual_type == test["expected_type"]:
                print(f"✅ PASSED - Got expected type: {actual_type}")
                print(f"   Result structure: {json.dumps(result, indent=2)[:200]}...")
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

    return passed, failed

if __name__ == "__main__":
    passed, failed = run_tests()
    sys.exit(0 if failed == 0 else 1)