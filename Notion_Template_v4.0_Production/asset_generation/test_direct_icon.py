#!/usr/bin/env python3
"""
Direct test of Replicate API with simple icon prompt
Tests if the model can generate simple flat icons when given the right prompt
"""

import os
import replicate
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Test prompts - from simple to explicit
test_prompts = [
    {
        "name": "simple_document",
        "prompt": "Simple flat icon of a document, minimalist design, single color, no background, vector style, UI icon"
    },
    {
        "name": "explicit_simple",
        "prompt": "SIMPLE FLAT ICON ONLY: document symbol, NO SCENE, NO BACKGROUND, NO DECORATIONS, just a simple document shape, flat design, single color icon, minimalist UI style, vector icon, 64x64px icon design"
    },
    {
        "name": "negative_prompt",
        "prompt": "Flat document icon, simple geometric shape, solid color || NOT: complex scene, NOT: realistic, NOT: 3D, NOT: background, NOT: decorative, NOT: detailed"
    }
]

def test_icon_generation():
    """Test different prompt styles for simple icon generation"""
    
    # Get model from config
    model_id = "stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc"
    
    print("=" * 80)
    print("TESTING REPLICATE API DIRECTLY FOR SIMPLE ICON GENERATION")
    print("=" * 80)
    print(f"Model: {model_id}")
    print()
    
    for test in test_prompts:
        print(f"\nTest: {test['name']}")
        print(f"Prompt: {test['prompt']}")
        print("Generating...")
        
        try:
            # Call Replicate API
            output = replicate.run(
                model_id,
                input={
                    "prompt": test['prompt'],
                    "negative_prompt": "complex scene, realistic photo, 3D rendering, detailed background, luxury, ornate, decorative",
                    "width": 512,
                    "height": 512,
                    "num_outputs": 1,
                    "guidance_scale": 7.5,
                    "num_inference_steps": 30
                }
            )
            
            if output:
                print(f"✓ Generated successfully!")
                print(f"  Output URL: {output[0]}")
                
                # Save the URL for manual inspection
                with open(f"test_icon_{test['name']}_url.txt", "w") as f:
                    f.write(f"Test: {test['name']}\n")
                    f.write(f"Prompt: {test['prompt']}\n")
                    f.write(f"URL: {output[0]}\n")
            else:
                print("✗ No output received")
                
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("Check the generated URLs to see if simple icons were produced")
    print("=" * 80)

if __name__ == "__main__":
    test_icon_generation()