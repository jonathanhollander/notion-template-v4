#!/usr/bin/env python3
"""
Test the new structured prompt system without requiring API calls
"""

import os
import sys
from pathlib import Path
from openrouter_orchestrator import OpenRouterOrchestrator, StructuredPrompt

def test_structured_system():
    """Test the structured prompt system"""
    print("🧪 TESTING STRUCTURED PROMPT SYSTEM")
    print("=" * 50)
    
    # Test 1: Master prompt loading
    print("\n1. Testing master prompt loading...")
    try:
        # Mock the API key for testing
        os.environ['OPENROUTER_API_KEY'] = 'test-key-for-testing'
        orchestrator = OpenRouterOrchestrator()
        print(f"✅ Master prompt loaded: {len(orchestrator.master_prompt)} characters")
        print(f"📁 Logs directory created: {orchestrator.logs_dir}")
    except Exception as e:
        print(f"❌ Failed to load master prompt: {e}")
        return False
    
    # Test 2: Structured response parsing
    print("\n2. Testing structured response parsing...")
    test_response = """
SYSTEM: You are a luxury estate planning visual designer with expertise in creating emotionally sensitive imagery for high-net-worth families.

TEMPERATURE: 0.6

ROLE: luxury estate planning visual consultant  

PROMPT: Create an elegant estate planning consultation scene featuring a mahogany desk with leather-bound documents, golden fountain pen, warm lamplight casting soft shadows, family photos in silver frames, representing generational legacy and trust. Style: photorealistic, warm color temperature, luxury aesthetic, emotional warmth.
"""
    
    try:
        structured = orchestrator._parse_structured_response(test_response)
        print("✅ Structured parsing successful:")
        print(f"  📋 System: {structured.system_message[:60]}...")
        print(f"  🌡️  Temperature: {structured.temperature}")
        print(f"  👤 Role: {structured.role}")
        print(f"  🎨 Prompt: {structured.prompt[:80]}...")
    except Exception as e:
        print(f"❌ Failed to parse structured response: {e}")
        return False
    
    # Test 3: Context data preparation
    print("\n3. Testing context data preparation...")
    try:
        test_page_info = {
            'title': 'Executor Hub',
            'category': 'executor',
            'asset_type': 'icon',
            'section': 'executor',
            'tier': 'hub',
            'emotional_context': 'DIGNIFIED_PLANNING'
        }
        
        test_model_config = {
            'perspective': 'emotional_depth',
            'strengths': ['empathy', 'nuance', 'human_connection']
        }
        
        context_data = orchestrator._prepare_context_data(test_page_info, test_model_config)
        print("✅ Context data preparation successful:")
        print(f"  📝 Title: {context_data['title']}")
        print(f"  🎯 Category: {context_data['category']}")
        print(f"  🎨 Asset Type: {context_data['asset_type']}")
        print(f"  📊 Tier: {context_data['tier']}")
        print(f"  💝 Emotional Context: {context_data['emotional_context']}")
    except Exception as e:
        print(f"❌ Failed to prepare context data: {e}")
        return False
    
    # Test 4: Style/emotion/luxury extraction
    print("\n4. Testing element extraction...")
    try:
        test_prompt = "Create a luxury mahogany estate planning scene with warm family photos showing compassionate care and exclusive prestige for executive clients"
        
        style_elements = orchestrator._extract_style_elements(test_prompt)
        emotional_markers = orchestrator._extract_emotional_markers(test_prompt)
        luxury_indicators = orchestrator._extract_luxury_indicators(test_prompt)
        
        print("✅ Element extraction successful:")
        print(f"  🎨 Style: {style_elements}")
        print(f"  💝 Emotional: {emotional_markers}")
        print(f"  💎 Luxury: {luxury_indicators}")
    except Exception as e:
        print(f"❌ Failed to extract elements: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS PASSED - STRUCTURED SYSTEM READY!")
    print("=" * 50)
    
    print("\n📋 SYSTEM SUMMARY:")
    print(f"📄 Master Prompt: {len(orchestrator.master_prompt):,} characters")
    print(f"📁 Logging Directory: {orchestrator.logs_dir}")
    print(f"🔧 Models Configured: {len(orchestrator.models)}")
    print(f"🎯 Ready for production with OpenRouter API key")
    
    return True

if __name__ == "__main__":
    success = test_structured_system()
    sys.exit(0 if success else 1)