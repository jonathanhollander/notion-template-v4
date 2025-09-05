#!/usr/bin/env python3
"""
Full Integration Test for WebSocket Visibility System
Tests the complete integration with actual asset generation
"""

import sys
import time
import asyncio
import subprocess
from pathlib import Path


def start_web_server():
    """Start the review dashboard server in the background"""
    print("Starting web server...")
    process = subprocess.Popen(
        [sys.executable, "review_dashboard.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Give server time to start
    print("✅ Web server started on http://localhost:4500/enhanced")
    return process


def test_websocket_integration():
    """Test that WebSocket events are being emitted"""
    print("\n" + "="*60)
    print("Testing WebSocket Integration")
    print("="*60)
    
    # Run the test script
    result = subprocess.run(
        [sys.executable, "test_websocket_connection.py"],
        input="1\n",  # Choose option 1
        text=True,
        capture_output=True
    )
    
    if "ALL TESTS PASSED" in result.stdout:
        print("✅ WebSocket integration test passed")
        return True
    else:
        print("❌ WebSocket integration test failed")
        print(result.stdout)
        return False


async def test_sample_generation():
    """Test sample generation with visibility"""
    print("\n" + "="*60)
    print("Testing Sample Generation with Visibility")
    print("="*60)
    
    # Run asset generator in test mode
    process = await asyncio.create_subprocess_exec(
        sys.executable, "asset_generator.py", 
        "--test", "--test-type", "icons",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    output = stdout.decode()
    
    # Check for visibility indicators
    checks = {
        "WebSocket broadcaster initialized": False,
        "TEST COMPLETE": False,
        "Generated": False
    }
    
    for line in output.split('\n'):
        for check in checks:
            if check in line:
                checks[check] = True
    
    print("\nVisibility Integration Checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    
    if all(checks.values()):
        print("\n✅ Sample generation with visibility successful")
        return True
    else:
        print("\n❌ Some visibility features not working")
        print("\nFull output:")
        print(output[:1000])  # First 1000 chars
        return False


def check_files_exist():
    """Check that all necessary files exist"""
    print("\n" + "="*60)
    print("Checking File Integrity")
    print("="*60)
    
    required_files = [
        "asset_generator.py",
        "review_dashboard.py",
        "websocket_broadcaster.py",
        "templates/dashboard_enhanced.html",
        "test_enhanced_visibility.py",
        "test_websocket_connection.py"
    ]
    
    all_exist = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - NOT FOUND")
            all_exist = False
    
    return all_exist


def check_integration_points():
    """Check that key integration points are present in the code"""
    print("\n" + "="*60)
    print("Checking Integration Points")
    print("="*60)
    
    # Read asset_generator.py
    with open("asset_generator.py", 'r') as f:
        content = f.read()
    
    integration_points = {
        "from websocket_broadcaster import get_broadcaster": "Import statement",
        "self.broadcaster = get_broadcaster()": "Broadcaster initialization",
        "self.broadcaster.start_generation": "Session start",
        "self.broadcaster.update_pipeline_stage": "Pipeline updates",
        "self.broadcaster.prompt_created": "Prompt visibility",
        "self.broadcaster.update_cost": "Cost tracking",
        "self.broadcaster.complete_generation": "Session completion",
        "check_control_flags": "Control handling"
    }
    
    all_present = True
    for code, description in integration_points.items():
        if code in content:
            print(f"✅ {description}: Found")
        else:
            print(f"❌ {description}: NOT FOUND")
            all_present = False
    
    return all_present


async def main():
    """Run all integration tests"""
    print("="*70)
    print("FULL VISIBILITY INTEGRATION TEST")
    print("="*70)
    print("\nThis test will verify that all visibility features are properly")
    print("integrated into the asset generation system.")
    print("\n⚠️ NOTE: For full effect, open http://localhost:4500/enhanced")
    print("in your browser to see real-time updates during the test.")
    
    # Change to asset_generation directory
    import os
    os.chdir("/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation")
    
    # Run tests
    results = {}
    
    # 1. Check files exist
    print("\n[1/5] Checking files...")
    results['files'] = check_files_exist()
    
    # 2. Check integration points
    print("\n[2/5] Checking code integration...")
    results['integration'] = check_integration_points()
    
    # 3. Start web server
    print("\n[3/5] Starting web server...")
    server_process = None
    try:
        server_process = start_web_server()
        results['server'] = True
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        results['server'] = False
    
    # 4. Test WebSocket
    if results['server']:
        print("\n[4/5] Testing WebSocket...")
        results['websocket'] = test_websocket_integration()
    else:
        results['websocket'] = False
    
    # 5. Test sample generation
    print("\n[5/5] Testing sample generation...")
    results['generation'] = await test_sample_generation()
    
    # Final summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    
    test_names = {
        'files': 'File Integrity',
        'integration': 'Code Integration',
        'server': 'Web Server',
        'websocket': 'WebSocket Events',
        'generation': 'Sample Generation'
    }
    
    all_passed = True
    for key, name in test_names.items():
        status = "✅ PASS" if results.get(key, False) else "❌ FAIL"
        print(f"{name:20} {status}")
        if not results.get(key, False):
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nThe visibility system is fully integrated and working.")
        print("\nNext steps:")
        print("1. Keep the web server running: python review_dashboard.py")
        print("2. Open http://localhost:4500/enhanced in your browser")
        print("3. Run actual generation: python asset_generator.py --test")
        print("4. Watch real-time updates in the dashboard!")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("\nPlease review the failures above and fix any issues.")
        print("You may need to:")
        print("- Restore from backup if integration failed")
        print("- Install missing dependencies")
        print("- Check file permissions")
    
    # Clean up
    if server_process:
        print("\nShutting down web server...")
        server_process.terminate()
        time.sleep(1)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)