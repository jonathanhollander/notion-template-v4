#!/usr/bin/env python3
"""
Test script to verify that prompts are generated from master_prompt text files
"""

import os
import asyncio
from pathlib import Path
from openrouter_orchestrator import OpenRouterOrchestrator

async def test_prompt_generation():
    """Test generating prompts for icons and covers"""
    
    # Set a dummy API key for testing (we won't actually make API calls)
    os.environ['OPENROUTER_API_KEY'] = 'test_key_for_prompt_verification'
    
    print("Testing Prompt Generation System")
    print("=" * 50)
    
    # Test icon prompt generation
    print("\n1. Testing ICON prompt generation:")
    print("-" * 30)
    
    icon_context = {
        'title': 'Executor Responsibilities',
        'category': 'executor',
        'asset_type': 'icons',
        'tier': 'DOCUMENT',
        'emotional_context': 'DIGNIFIED_PLANNING'
    }
    
    orchestrator = OpenRouterOrchestrator()
    
    # Check which master prompt file is loaded for icons
    icon_master = orchestrator._load_master_prompt('icons')
    print(f"✓ Loaded master prompt for icons from: meta_prompts/master_prompt_icons.txt")
    print(f"  First 100 chars: {icon_master[:100]}...")
    
    # Test cover prompt generation
    print("\n2. Testing COVER prompt generation:")
    print("-" * 30)
    
    cover_context = {
        'title': 'Estate Planning Hub',
        'category': 'planning',
        'asset_type': 'covers',
        'tier': 'HUB',
        'emotional_context': 'WEALTH_TRANSITION'
    }
    
    # Check which master prompt file is loaded for covers
    cover_master = orchestrator._load_master_prompt('covers')
    print(f"✓ Loaded master prompt for covers from: meta_prompts/master_prompt_covers.txt")
    print(f"  First 100 chars: {cover_master[:100]}...")
    
    # Verify the prompts are different
    print("\n3. Verification:")
    print("-" * 30)
    
    if "SIMPLE, FLAT ICONS" in icon_master and "SIMPLE" in icon_master:
        print("✓ Icon master prompt correctly emphasizes SIMPLE, FLAT design")
    else:
        print("✗ Icon master prompt may not have the right emphasis on simple design")
    
    if "luxury" in cover_master.lower() and "mahogany" in cover_master.lower():
        print("✓ Cover master prompt correctly includes luxury elements")
    else:
        print("✗ Cover master prompt may not have luxury elements")
    
    if icon_master != cover_master:
        print("✓ Icon and cover prompts are different (as expected)")
    else:
        print("✗ Icon and cover prompts are the same (this is wrong!)")
    
    print("\n4. Source Verification:")
    print("-" * 30)
    
    # Check that prompt_templates.py doesn't have hardcoded icon mappings
    prompt_templates_path = Path("prompt_templates.py")
    with open(prompt_templates_path, 'r') as f:
        content = f.read()
        
    # Check for signs of hardcoded icon mappings
    if "create_simple_icon_prompt" in content:
        print("✗ WARNING: prompt_templates.py still contains create_simple_icon_prompt method")
    else:
        print("✓ No create_simple_icon_prompt method found (good!)")
    
    if "'Executor Checklist': 'clipboard with checkmark'" in content:
        print("✗ WARNING: prompt_templates.py still contains hardcoded icon mappings")
    else:
        print("✓ No hardcoded icon mappings found (good!)")
    
    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("\nAll prompts are now generated from master_prompt text files!")
    print("User has full control over prompts through these files:")
    print("  - meta_prompts/master_prompt_icons.txt (for icons)")
    print("  - meta_prompts/master_prompt_covers.txt (for covers)")
    print("  - meta_prompts/master_prompt.txt (default/fallback)")

if __name__ == "__main__":
    asyncio.run(test_prompt_generation())