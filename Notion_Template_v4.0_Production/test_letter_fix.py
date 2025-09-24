#!/usr/bin/env python3
"""
Test script to verify the Body field fix for letter templates
"""
import json
import yaml
from pathlib import Path

# Load the letter template YAML
yaml_file = Path("split_yaml/12_letters_content_patch.yaml")
with open(yaml_file, 'r') as f:
    data = yaml.safe_load(f)

# Find a letter template with Body field
letter_page = None
for page in data.get('pages', []):
    if page.get('title', '').startswith('Letter') and 'Body' in page:
        letter_page = page
        break

if letter_page:
    print(f"Testing letter: {letter_page['title']}")
    print(f"Body field type: {type(letter_page['Body'])}")
    print(f"Body content preview: {letter_page['Body'][:100]}...")
    
    # Simulate the fix logic
    blocks_data = letter_page.get('Body', [])
    
    print("\n--- Before fix (would iterate character by character) ---")
    if isinstance(blocks_data, str):
        print(f"Body is a string with {len(blocks_data)} characters")
        print(f"First 10 iterations would create blocks for: {list(blocks_data[:10])}")
    
    print("\n--- After fix (splits into paragraphs) ---")
    if isinstance(blocks_data, str):
        paragraphs = blocks_data.split('\n\n')
        print(f"Split into {len(paragraphs)} paragraph blocks:")
        for i, para in enumerate(paragraphs[:3], 1):  # Show first 3
            preview = para.strip()[:80] + "..." if len(para.strip()) > 80 else para.strip()
            print(f"  Block {i}: {preview}")
else:
    print("No letter template with Body field found")
