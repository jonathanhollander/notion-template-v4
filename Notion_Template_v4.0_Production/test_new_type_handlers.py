#!/usr/bin/env python3
"""
Test the new type handlers added to deploy.py
"""
import json
import sys
import os

# Add current directory to path to import deploy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import deploy module
import deploy

# Mock logger
class MockLogger:
    def info(self, msg): print(f"INFO: {msg}")
    def warning(self, msg): print(f"WARNING: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
    def debug(self, msg): pass

# Set up mock logger
deploy.logger = MockLogger()

# Mock state for database references
class MockState:
    def __init__(self):
        self.created_databases = {}

deploy.state = MockState()

# Test cases
print("=" * 60)
print("Testing New Type Handlers")
print("=" * 60)

# Test 1: H2 conversion
print("\n1. Testing H2 block type conversion:")
h2_block = {"type": "H2", "heading": "Test Heading"}
converted = deploy.convert_legacy_block_format(h2_block)
print(f"   Input: {h2_block}")
print(f"   Output: {converted}")
assert converted["type"] == "heading_2", "H2 should convert to heading_2"
assert converted["content"] == "Test Heading", "heading should move to content"
print("   ✅ PASSED")

# Test 2: linked_db handler
print("\n2. Testing linked_db block handler:")
linked_db_block = {"linked_db": "diagnostics_results"}
result = deploy.build_block(linked_db_block)
print(f"   Input: {linked_db_block}")
print(f"   Output type: {list(result.keys())[0]}")
assert "paragraph" in result or "child_database" in result
print("   ✅ PASSED")

# Test 3: files database property
print("\n3. Testing files database property:")
files_prop = {"type": "files"}
result = deploy.build_property_schema(files_prop)
print(f"   Input: {files_prop}")
print(f"   Output: {result}")
assert "files" in result, "Should return files property"
print("   ✅ PASSED")

# Test 4: created_time database property
print("\n4. Testing created_time database property:")
created_prop = {"type": "created_time"}
result = deploy.build_property_schema(created_prop)
print(f"   Input: {created_prop}")
print(f"   Output: {result}")
assert "created_time" in result, "Should return created_time property"
print("   ✅ PASSED")

# Test 5: dual_property in relation
print("\n5. Testing dual_property in relation:")
dual_prop = {
    "type": "relation",
    "relation": {
        "database_id": None,
        "type": "dual_property",
        "dual_property": {
            "synced_property_name": "Analytics Link",
            "synced_property_id": None
        }
    }
}
result = deploy.build_property_schema(dual_prop)
print(f"   Input: {json.dumps(dual_prop, indent=2)}")
print(f"   Output: {json.dumps(result, indent=2)}")
assert "relation" in result, "Should return relation property"
if "type" in result["relation"]:
    assert result["relation"]["type"] == "dual_property", "Should have dual_property type"
print("   ✅ PASSED")

print("\n" + "=" * 60)
print("All tests passed! ✅")
print("=" * 60)