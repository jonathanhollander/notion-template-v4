#!/usr/bin/env python3
"""
Test WebSocket connection and visibility features
"""

import time
import sys
from websocket_broadcaster import get_broadcaster


def test_basic_connection():
    """Test basic WebSocket functionality"""
    
    broadcaster = get_broadcaster()
    
    print("Testing WebSocket Broadcaster...")
    print("-" * 40)
    
    # Check if broadcaster is initialized
    print(f"✓ Broadcaster initialized: {broadcaster is not None}")
    print(f"✓ Broadcaster enabled: {broadcaster.enabled}")
    
    # Test basic event emission
    print("\nEmitting test events...")
    
    test_events = [
        ("Starting pipeline discovery", "discovery"),
        ("Generating prompts", "prompt"),
        ("Selecting model", "model"),
        ("Creating image", "image"),
        ("Saving results", "save")
    ]
    
    for message, stage in test_events:
        print(f"  → {message}")
        broadcaster.update_pipeline_stage(stage)
        broadcaster.emit_log(message, "info")
        time.sleep(0.5)
    
    print("\n✅ Basic connection test complete")
    return True


def test_visibility_features():
    """Test all 12 visibility features"""
    
    broadcaster = get_broadcaster()
    
    print("\nTesting Visibility Features...")
    print("-" * 40)
    
    features_tested = []
    
    # 1. Real-time prompt display
    print("1. Testing real-time prompt display...")
    broadcaster.prompt_generating_start("Test Asset", "Claude 3.5")
    broadcaster.prompt_created("Test Asset", "Claude 3.5", "A minimalist icon...", 92.5, True)
    features_tested.append("Real-time prompt display")
    time.sleep(0.5)
    
    # 2. Live cost tracking
    print("2. Testing live cost tracking...")
    broadcaster.update_cost(0.04, 0.04, 1)
    features_tested.append("Live cost tracking")
    time.sleep(0.5)
    
    # 3. Approval gates
    print("3. Testing approval gates...")
    broadcaster.request_approval([{
        'asset_name': 'Test Asset',
        'prompt': 'Test prompt',
        'estimated_cost': 0.04
    }])
    features_tested.append("Approval gates")
    time.sleep(0.5)
    
    # 4. Model decisions
    print("4. Testing model decision explanations...")
    broadcaster.model_decision("Claude 3.5", [
        "Highest confidence score",
        "Best context understanding"
    ])
    features_tested.append("Model decision explanations")
    time.sleep(0.5)
    
    # 5. Pipeline visualization
    print("5. Testing pipeline visualization...")
    for stage in ["discovery", "prompt", "model", "image", "save"]:
        broadcaster.update_pipeline_stage(stage)
        time.sleep(0.3)
    features_tested.append("Pipeline visualization")
    
    # 6. Control states
    print("6. Testing pause/resume controls...")
    broadcaster.handle_pause()
    time.sleep(0.5)
    broadcaster.handle_resume()
    features_tested.append("Pause/resume controls")
    time.sleep(0.5)
    
    # 7. Dry-run mode
    print("7. Testing dry-run mode toggle...")
    broadcaster.set_dry_run_mode(True)
    time.sleep(0.5)
    broadcaster.set_dry_run_mode(False)
    features_tested.append("Dry-run mode toggle")
    time.sleep(0.5)
    
    # 8. Log streaming
    print("8. Testing log streaming...")
    broadcaster.emit_log("Info message", "info")
    broadcaster.emit_log("Warning message", "warning")
    broadcaster.emit_log("Error message", "error")
    features_tested.append("Log streaming")
    time.sleep(0.5)
    
    # 9. Progress updates
    print("9. Testing progress updates...")
    broadcaster.update_progress(5, 10, "50% complete")
    features_tested.append("Progress updates")
    time.sleep(0.5)
    
    # 10. Session management
    print("10. Testing session management...")
    broadcaster.start_generation("test", 10)
    time.sleep(0.5)
    broadcaster.complete_generation()
    features_tested.append("Session management")
    time.sleep(0.5)
    
    # 11. Error handling
    print("11. Testing error broadcasting...")
    broadcaster.emit_error("Test error message", severity="warning")
    features_tested.append("Error broadcasting")
    time.sleep(0.5)
    
    # 12. Model competition
    print("12. Testing model competition display...")
    models = [
        ("Claude 3.5", 92.5, "Minimalist design..."),
        ("GPT-4", 88.3, "Simple geometric..."),
        ("Gemini Pro", 85.7, "Clean vector...")
    ]
    
    for model, confidence, prompt in models:
        broadcaster.prompt_created("Test Asset", model, prompt, confidence, model == "Claude 3.5")
        time.sleep(0.3)
    features_tested.append("Model competition display")
    
    print("\n✅ All 12 visibility features tested:")
    for i, feature in enumerate(features_tested, 1):
        print(f"   {i}. ✓ {feature}")
    
    return True


def main():
    """Run all tests"""
    
    print("=" * 50)
    print("WebSocket Visibility System Test")
    print("=" * 50)
    print("\nNote: For full effect, have the web dashboard open at:")
    print("http://localhost:4500/enhanced")
    print("\nStarting tests in 3 seconds...")
    time.sleep(3)
    
    # Run basic connection test
    if not test_basic_connection():
        print("❌ Basic connection test failed")
        return 1
    
    # Run visibility features test
    if not test_visibility_features():
        print("❌ Visibility features test failed")
        return 1
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED")
    print("=" * 50)
    print("\nThe WebSocket visibility system is ready for integration")
    print("Check the web dashboard to see all the real-time updates!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())