#!/usr/bin/env python3
"""
Test script to demonstrate enhanced visibility features
Shows real-time updates during generation process
"""

import time
import asyncio
from websocket_broadcaster import get_broadcaster


def simulate_generation_with_visibility():
    """Simulate a generation process with full visibility"""
    
    # Get the broadcaster instance
    broadcaster = get_broadcaster()
    
    print("Starting simulated generation with enhanced visibility...")
    print("Open http://localhost:4500/enhanced to see real-time updates")
    print("-" * 60)
    
    # Start session
    broadcaster.session_started("test-session-001", total_assets=10)
    time.sleep(1)
    
    # Simulate generation of 3 test assets
    test_assets = [
        {"name": "Executive Summary Icon", "type": "icon"},
        {"name": "Family Trust Cover", "type": "cover"},
        {"name": "Legal Documents Icon", "type": "icon"}
    ]
    
    total_cost = 0.0
    
    for i, asset in enumerate(test_assets):
        print(f"\n[{i+1}/{len(test_assets)}] Generating: {asset['name']}")
        
        # Update pipeline stage
        broadcaster.update_pipeline_stage("discovery")
        time.sleep(0.5)
        
        broadcaster.update_pipeline_stage("prompt")
        
        # Notify prompt generation start
        broadcaster.prompt_generating_start(asset['name'], 'Claude 3.5')
        time.sleep(1)
        
        # Simulate model competition
        models = [
            ("Claude 3.5", 92.5, "A minimalist flat icon representing..."),
            ("GPT-4", 88.3, "Simple geometric shapes forming..."),
            ("Gemini Pro", 85.7, "Clean vector design showing...")
        ]
        
        broadcaster.update_pipeline_stage("model")
        
        for model_name, confidence, prompt in models:
            broadcaster.prompt_created(
                asset['name'], 
                model_name, 
                prompt, 
                confidence,
                selected=(model_name == "Claude 3.5")
            )
            time.sleep(0.5)
        
        # Explain decision
        broadcaster.model_decision(
            "Claude 3.5",
            [
                "Highest confidence score (92.5%)",
                "Best understanding of minimalist design requirements",
                "Consistent with estate planning context"
            ]
        )
        
        # Request approval (optional)
        if i == 0:  # Only for first item
            broadcaster.request_approval([{
                'asset_name': asset['name'],
                'prompt': models[0][2],
                'estimated_cost': 0.04
            }])
            time.sleep(2)
        
        # Update pipeline to image generation
        broadcaster.update_pipeline_stage("image")
        
        # Simulate image generation
        broadcaster.emit('image_generating', {
            'asset_name': asset['name'],
            'status': 'generating',
            'model': 'stability-ai/sdxl'
        })
        time.sleep(2)
        
        # Update cost
        item_cost = 0.04
        total_cost += item_cost
        broadcaster.update_cost(item_cost, total_cost, i + 1)
        
        # Complete item
        broadcaster.update_pipeline_stage("save")
        broadcaster.emit('image_completed', {
            'asset_name': asset['name'],
            'file_path': f"output/samples/{asset['type']}_{i+1}.png",
            'generation_time': 2.3,
            'cost': item_cost
        })
        
        # Progress update
        broadcaster.update_progress(i + 1, len(test_assets), f"Completed {asset['name']}")
        time.sleep(1)
    
    # Complete session
    broadcaster.session_completed(
        total_generated=len(test_assets),
        total_cost=total_cost,
        duration=15.0,
        success_rate=100.0
    )
    
    print("\n" + "=" * 60)
    print("Simulation complete!")
    print(f"Total cost: ${total_cost:.2f}")
    print("Check the web dashboard for the complete visibility log")


def test_control_features():
    """Test pause/resume/abort control features"""
    broadcaster = get_broadcaster()
    
    print("\nTesting control features...")
    
    # Test pause
    print("- Testing pause...")
    broadcaster.handle_pause()
    time.sleep(1)
    
    # Test resume
    print("- Testing resume...")
    broadcaster.handle_resume()
    time.sleep(1)
    
    # Test speed change
    print("- Testing speed change...")
    broadcaster.emit('speed_changed', {'speed': 'fast'})
    time.sleep(1)
    
    # Test dry-run mode
    print("- Testing dry-run mode...")
    broadcaster.set_dry_run_mode(True)
    time.sleep(1)
    broadcaster.set_dry_run_mode(False)
    
    print("Control features test complete!")


if __name__ == "__main__":
    import sys
    
    print("Enhanced Visibility Test Script")
    print("================================")
    print("\nThis script simulates the generation process with full visibility")
    print("Make sure the web server is running: python review_dashboard.py")
    print("\nOptions:")
    print("1. Run full simulation")
    print("2. Test control features only")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        simulate_generation_with_visibility()
    elif choice == "2":
        test_control_features()
    else:
        print("Exiting...")
        sys.exit(0)