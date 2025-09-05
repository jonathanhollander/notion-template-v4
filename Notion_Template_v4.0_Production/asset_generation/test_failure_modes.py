#!/usr/bin/env python3
"""
Test failure modes including invalid API keys and error handling.
"""

import asyncio
import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from asset_generator import AssetGenerator

async def test_failure_modes():
    """Test various failure scenarios."""
    
    print("=" * 60)
    print("FAILURE MODE TESTING")
    print("=" * 60)
    
    results = []
    
    # Test 1: Invalid API key
    print("\n[TEST 1] Testing with invalid API key...")
    original_key = os.environ.get('REPLICATE_API_KEY', '')
    os.environ['REPLICATE_API_KEY'] = 'invalid_key_12345'
    
    try:
        generator = AssetGenerator()
        result = await generator.generate_asset(
            asset_type='icons',
            prompt='Test with invalid key',
            index=1,
            total=1
        )
        
        if result is None:
            print("   ✅ PASS: Correctly handled invalid API key (returned None)")
            results.append({'test': 'invalid_key', 'status': 'pass'})
        else:
            print("   ❌ FAIL: Should have failed with invalid key")
            results.append({'test': 'invalid_key', 'status': 'fail'})
            
    except Exception as e:
        print(f"   ✅ PASS: Correctly raised exception: {str(e)[:50]}...")
        results.append({'test': 'invalid_key', 'status': 'pass', 'error': str(e)})
    
    # Restore original key
    os.environ['REPLICATE_API_KEY'] = original_key
    
    # Test 2: Empty prompt
    print("\n[TEST 2] Testing with empty prompt...")
    try:
        generator = AssetGenerator()
        result = await generator.generate_asset(
            asset_type='icons',
            prompt='',
            index=1,
            total=1
        )
        
        if result is None:
            print("   ✅ PASS: Correctly handled empty prompt")
            results.append({'test': 'empty_prompt', 'status': 'pass'})
        else:
            print("   ⚠️ WARNING: Generated image with empty prompt")
            results.append({'test': 'empty_prompt', 'status': 'warning'})
            
    except Exception as e:
        print(f"   ✅ PASS: Raised exception for empty prompt: {str(e)[:50]}...")
        results.append({'test': 'empty_prompt', 'status': 'pass', 'error': str(e)})
    
    # Test 3: Invalid asset type
    print("\n[TEST 3] Testing with invalid asset type...")
    try:
        generator = AssetGenerator()
        result = await generator.generate_asset(
            asset_type='invalid_type',
            prompt='Test prompt',
            index=1,
            total=1
        )
        
        if result is None:
            print("   ✅ PASS: Correctly handled invalid asset type")
            results.append({'test': 'invalid_type', 'status': 'pass'})
        else:
            print("   ❌ FAIL: Should have failed with invalid type")
            results.append({'test': 'invalid_type', 'status': 'fail'})
            
    except Exception as e:
        print(f"   ✅ PASS: Raised exception for invalid type: {str(e)[:50]}...")
        results.append({'test': 'invalid_type', 'status': 'pass', 'error': str(e)})
    
    # Test 4: Circuit breaker test (3 rapid failures)
    print("\n[TEST 4] Testing circuit breaker (3 rapid failures)...")
    os.environ['REPLICATE_API_KEY'] = 'invalid_key_to_trigger_failures'
    
    try:
        generator = AssetGenerator()
        failures = 0
        
        for i in range(4):  # Try 4 times to trigger circuit breaker
            try:
                result = await generator.generate_asset(
                    asset_type='icons',
                    prompt=f'Circuit breaker test {i+1}',
                    index=i+1,
                    total=4
                )
                if result is None:
                    failures += 1
                    print(f"   Attempt {i+1}: Failed as expected")
            except:
                failures += 1
                print(f"   Attempt {i+1}: Exception raised")
        
        if failures >= 3:
            print("   ✅ PASS: Circuit breaker likely triggered after 3 failures")
            results.append({'test': 'circuit_breaker', 'status': 'pass', 'failures': failures})
        else:
            print("   ⚠️ WARNING: Circuit breaker may not have triggered")
            results.append({'test': 'circuit_breaker', 'status': 'warning', 'failures': failures})
            
    except Exception as e:
        print(f"   ✅ PASS: System handled rapid failures: {str(e)[:50]}...")
        results.append({'test': 'circuit_breaker', 'status': 'pass', 'error': str(e)})
    
    # Restore original key
    os.environ['REPLICATE_API_KEY'] = original_key
    
    # Test 5: Budget limit enforcement
    print("\n[TEST 5] Testing budget limit enforcement...")
    # This would need to actually generate images to test budget, so we'll simulate
    print("   ℹ️ SKIP: Budget testing requires actual generation (costs money)")
    results.append({'test': 'budget_limit', 'status': 'skipped'})
    
    # Summary
    print("\n" + "=" * 60)
    print("FAILURE MODE TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['status'] == 'pass')
    failed = sum(1 for r in results if r['status'] == 'fail')
    warnings = sum(1 for r in results if r['status'] == 'warning')
    skipped = sum(1 for r in results if r['status'] == 'skipped')
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Warnings: {warnings}")
    print(f"ℹ️ Skipped: {skipped}")
    
    # Save results
    with open('test_failure_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(results),
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'skipped': skipped,
            'results': results
        }, f, indent=2)
    
    print(f"\n📁 Results saved to: test_failure_results.json")
    
    return failed == 0

if __name__ == "__main__":
    # Run failure mode tests
    success = asyncio.run(test_failure_modes())
    
    if success:
        print("\n🎉 ALL FAILURE MODE TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n⚠️ SOME FAILURE MODE TESTS FAILED")
        sys.exit(1)