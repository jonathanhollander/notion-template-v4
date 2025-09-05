#!/usr/bin/env python3
"""
Test icon generation with updated master_prompt_icons.txt
"""

import asyncio
import sys
from pathlib import Path
from asset_generator import AssetGenerator

async def test_icon_generation():
    """Test generating a few icons with the updated master prompt"""
    
    # Initialize generator
    generator = AssetGenerator()
    
    print("=" * 80)
    print("TESTING ICON GENERATION WITH UPDATED MASTER PROMPT")
    print("=" * 80)
    
    # Test pages for icon generation
    test_pages = [
        {
            'title': 'Legal Documents',
            'icon_file': 'legal_documents_icon.png',
            'prompt': 'Legal document management system'
        },
        {
            'title': 'Family Tree',
            'icon_file': 'family_tree_icon.png', 
            'prompt': 'Family genealogy tracker'
        },
        {
            'title': 'Bank Accounts',
            'icon_file': 'bank_accounts_icon.png',
            'prompt': 'Financial account management'
        }
    ]
    
    # Generate test icons
    generator.discovered_pages = test_pages
    
    print(f"\nGenerating {len(test_pages)} test icons...")
    print("This will use the updated master_prompt_icons.txt\n")
    
    # Generate icons using the normal flow
    await generator.generate_assets_from_pages(
        generator.discovered_pages,
        mode='icons_only',
        limit=3
    )
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("Check output/samples/ for generated icons")
    print("Icons should now be simple, flat UI icons")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_icon_generation())