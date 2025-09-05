#!/usr/bin/env python3
"""
Direct test of Replicate API image generation.
Tests exactly 3 images with proper model versions.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from asset_generator import AssetGenerator

async def test_image_generation():
    """Test generating 3 images directly."""
    
    print("=" * 60)
    print("DIRECT IMAGE GENERATION TEST")
    print("=" * 60)
    
    # Initialize generator
    generator = AssetGenerator()
    
    # Test pages - only 3
    test_pages = [
        {
            'title': 'Test Icon 1',
            'type': 'icons',
            'prompt': 'A simple test icon with geometric shapes'
        },
        {
            'title': 'Test Cover 1', 
            'type': 'covers',
            'prompt': 'A test cover image with abstract patterns'
        },
        {
            'title': 'Test Icon 2',
            'type': 'icons', 
            'prompt': 'Another test icon with circular design'
        }
    ]
    
    # Generate images
    results = []
    for i, page in enumerate(test_pages, 1):
        print(f"\n[{i}/3] Generating {page['type']} for: {page['title']}")
        print(f"   Prompt: {page['prompt']}")
        
        try:
            # Call the generate_asset method directly
            result = await generator.generate_asset(
                asset_type=page['type'],
                prompt=page['prompt'],
                index=i,
                total=3
            )
            
            if result:
                print(f"   ✅ SUCCESS: Generated image at {result}")
                results.append({
                    'title': page['title'],
                    'type': page['type'],
                    'file': str(result),
                    'status': 'success'
                })
            else:
                print(f"   ❌ FAILED: No image generated")
                results.append({
                    'title': page['title'],
                    'type': page['type'],
                    'file': None,
                    'status': 'failed'
                })
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({
                'title': page['title'],
                'type': page['type'],
                'file': None,
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] in ['failed', 'error'])
    
    print(f"✅ Successful: {successful}/3")
    print(f"❌ Failed: {failed}/3")
    
    # Save results
    results_file = Path('test_results.json')
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': 3,
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_file}")
    
    # Return success status
    return successful == 3

if __name__ == "__main__":
    # Check for API key
    if not os.environ.get('REPLICATE_API_TOKEN'):
        print("❌ ERROR: REPLICATE_API_TOKEN not set")
        sys.exit(1)
    
    # Set REPLICATE_API_KEY from TOKEN if needed
    if not os.environ.get('REPLICATE_API_KEY'):
        os.environ['REPLICATE_API_KEY'] = os.environ['REPLICATE_API_TOKEN']
    
    # Run test
    success = asyncio.run(test_image_generation())
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n⚠️ SOME TESTS FAILED")
        sys.exit(1)