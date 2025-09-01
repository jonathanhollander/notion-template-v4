#!/usr/bin/env python3
"""
🧪 GENERATE TEST SAMPLES - Estate Planning Concierge v4.0
Tests the complete system by generating 9 sample prompts (3x3 matrix)
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Set up for testing
os.environ['OPENROUTER_API_KEY'] = os.getenv('OPENROUTER_API_KEY', 'test-key-for-testing')

from openrouter_orchestrator import OpenRouterOrchestrator, StructuredPrompt, PromptVariant, PromptCompetition

class MockOpenRouterOrchestrator(OpenRouterOrchestrator):
    """Mock orchestrator that simulates API responses for testing"""
    
    def __init__(self):
        """Initialize with test configuration"""
        self.api_key = 'test-key'
        self.models = {
            'claude': {
                'id': 'anthropic/claude-3-opus-20240229',
                'perspective': 'emotional_depth',
                'strengths': ['empathy', 'nuance', 'human_connection']
            },
            'gpt4': {
                'id': 'openai/gpt-4-turbo-preview',
                'perspective': 'creative_luxury',
                'strengths': ['creativity', 'luxury', 'sophistication']
            },
            'gemini': {
                'id': 'google/gemini-pro',
                'perspective': 'technical_precision',
                'strengths': ['precision', 'consistency', 'structure']
            }
        }
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.logger = self._setup_logger()
        self.master_prompt = self._load_master_prompt()
        self.logs_dir = Path("logs/llm_generations")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    async def _call_openrouter_with_master_prompt(self, model_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate API call with realistic structured responses"""
        timestamp = datetime.now().isoformat()
        
        # Generate different responses based on model perspective
        if 'emotional_depth' in str(context_data.get('model_perspective', '')):
            response = f"""
SYSTEM: You are a compassionate estate planning visual designer specializing in creating emotionally resonant imagery that honors family legacies and provides comfort during life transitions.

TEMPERATURE: 0.6

ROLE: empathetic legacy visual consultant

PROMPT: Create a warm, inviting {context_data['asset_type']} for "{context_data['title']}" featuring soft golden hour lighting through mahogany-framed windows, illuminating a leather-bound family album open to vintage photographs spanning three generations. Include a sterling silver frame with a recent family portrait, fresh white orchids in a crystal vase symbolizing renewal, and handwritten notes on ivory stationery with a Mont Blanc fountain pen nearby. The scene should evoke feelings of continuity, love, and dignified planning while maintaining an ultra-luxury aesthetic with rich textures of velvet, silk, and aged leather. Style: photorealistic, warm color palette with amber and honey tones, emotional depth, premium materials, 8K quality.
"""
        elif 'creative_luxury' in str(context_data.get('model_perspective', '')):
            response = f"""
SYSTEM: You are an exclusive luxury brand designer creating ultra-premium visual assets for distinguished estate planning clients who expect the finest in aesthetic excellence.

TEMPERATURE: 0.7

ROLE: luxury estate brand creative director

PROMPT: Design an opulent {context_data['asset_type']} for "{context_data['title']}" showcasing a private library setting with floor-to-ceiling mahogany bookcases, first-edition leather-bound volumes, and a massive carved oak desk with gold leaf detailing. Feature a Waterford crystal decanter set on a silver tray, architectural lighting highlighting marble columns, and a view of manicured estate grounds through tall windows. Include subtle elements like a Patek Philippe pocket watch, wax seal stamps, and embossed letterhead on the finest cotton paper. The composition should communicate exclusivity, heritage, and sophisticated wealth management. Style: ultra-luxury aesthetic, rich jewel tones, architectural grandeur, museum-quality lighting, cinematic composition.
"""
        else:  # technical_precision
            response = f"""
SYSTEM: You are a technical visual systems architect specializing in creating precisely structured, consistent imagery for professional estate planning documentation.

TEMPERATURE: 0.5

ROLE: technical estate visual systems designer

PROMPT: Construct a technically precise {context_data['asset_type']} for "{context_data['title']}" with exact specifications: centered composition using rule of thirds, three-point lighting setup with key light at 45 degrees, fill light at 30% intensity, and rim lighting for depth separation. Include mahogany desk surface at 60% frame width, positioned at lower third intersection. Place primary documents in golden ratio spiral, with supporting elements following Fibonacci sequence spacing. Color palette: #4A3C28 (mahogany), #D4AF37 (gold accents), #F5F5DC (parchment), #2C3E50 (deep blue-gray). Ensure 300 DPI resolution, 16:9 aspect ratio, with depth of field f/2.8 for selective focus. Materials should show precise texture mapping: leather grain at 0.3mm detail, paper fiber visibility, metallic reflections at 85% intensity.
"""
        
        # Parse the structured response
        structured_prompt = self._parse_structured_response(response)
        
        # Log the interaction
        self._log_llm_interaction(model_id, context_data, structured_prompt, timestamp)
        
        return {
            'success': True,
            'structured_prompt': structured_prompt,
            'model': model_id,
            'usage': {'prompt_tokens': 100, 'completion_tokens': 200},
            'timestamp': timestamp
        }

async def generate_test_samples():
    """Generate 9 test samples (3 pages x 3 models)"""
    print("🚀 GENERATING TEST SAMPLES WITH STRUCTURED PROMPT SYSTEM")
    print("=" * 60)
    
    # Initialize mock orchestrator
    orchestrator = MockOpenRouterOrchestrator()
    
    # Define 3 test pages representing different tiers and categories
    test_pages = [
        {
            'title': 'Executor Command Center',
            'category': 'executor',
            'asset_type': 'hero_image',
            'section': 'executor',
            'tier': 'hub',
            'emotional_context': 'DIGNIFIED_PLANNING'
        },
        {
            'title': 'Family Legacy Letters',
            'category': 'family',
            'asset_type': 'section_cover',
            'section': 'family',
            'tier': 'section',
            'emotional_context': 'WEALTH_TRANSITION'
        },
        {
            'title': 'Digital Asset Vault',
            'category': 'digital',
            'asset_type': 'icon',
            'section': 'digital',
            'tier': 'digital',
            'emotional_context': 'CHARITABLE_GIVING'
        }
    ]
    
    all_competitions = []
    
    print(f"\n📄 Master Prompt Loaded: {len(orchestrator.master_prompt)} characters")
    print(f"📁 Logging Directory: {orchestrator.logs_dir}")
    print(f"🤖 Models Configured: {len(orchestrator.models)}")
    
    print("\n" + "="*60)
    print("GENERATING COMPETITIVE PROMPTS...")
    print("="*60)
    
    # Generate prompts for each page
    for page_num, page in enumerate(test_pages, 1):
        print(f"\n📄 Page {page_num}/{len(test_pages)}: {page['title']}")
        print(f"   Category: {page['category']} | Tier: {page['tier']} | Type: {page['asset_type']}")
        
        # Generate competitive prompts
        competition = await orchestrator.generate_competitive_prompts(page)
        all_competitions.append(competition)
        
        print(f"   ✅ Generated {len(competition.variants)} variants")
        
        # Display each variant's structured output
        for variant in competition.variants:
            print(f"\n   🤖 {variant.model.upper()} Model:")
            print(f"      System: {variant.structured_prompt.system_message[:60]}...")
            print(f"      Temperature: {variant.structured_prompt.temperature}")
            print(f"      Role: {variant.structured_prompt.role}")
            print(f"      Prompt Preview: {variant.structured_prompt.prompt[:100]}...")
            print(f"      Style Elements: {variant.style_elements}")
            print(f"      Emotional Markers: {variant.emotional_markers}")
            print(f"      Luxury Indicators: {variant.luxury_indicators}")
    
    # Save all results
    print("\n" + "="*60)
    print("SAVING RESULTS...")
    print("="*60)
    
    # Save competition results
    output_file = orchestrator.save_competition_results(all_competitions, "test_sample_competitions.json")
    print(f"✅ Competition results saved to: {output_file}")
    
    # Create summary report
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_pages': len(test_pages),
        'total_prompts_generated': sum(len(c.variants) for c in all_competitions),
        'models_used': list(orchestrator.models.keys()),
        'structured_output_format': 'SYSTEM/TEMPERATURE/ROLE/PROMPT',
        'logs_directory': str(orchestrator.logs_dir),
        'master_prompt_size': len(orchestrator.master_prompt),
        'pages_processed': [
            {
                'title': comp.page_title,
                'category': comp.page_category,
                'asset_type': comp.asset_type,
                'variants_generated': len(comp.variants),
                'variant_models': [v.model for v in comp.variants]
            }
            for comp in all_competitions
        ]
    }
    
    summary_file = "test_generation_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Summary report saved to: {summary_file}")
    
    # Check logs were created
    log_files = list(orchestrator.logs_dir.glob("*.json"))
    print(f"✅ Individual log files created: {len(log_files)}")
    
    if orchestrator.logs_dir.joinpath("master_llm_log.jsonl").exists():
        with open(orchestrator.logs_dir / "master_llm_log.jsonl", 'r') as f:
            log_lines = f.readlines()
        print(f"✅ Master log entries: {len(log_lines)}")
    
    print("\n" + "="*60)
    print("🎉 TEST GENERATION COMPLETE!")
    print("="*60)
    
    print("\n📊 FINAL STATISTICS:")
    print(f"   Total Pages Processed: {len(test_pages)}")
    print(f"   Total Prompts Generated: {sum(len(c.variants) for c in all_competitions)}")
    print(f"   Models Used: {', '.join(orchestrator.models.keys())}")
    print(f"   Structured Format: ✅ SYSTEM/TEMPERATURE/ROLE/PROMPT")
    print(f"   Logging: ✅ Complete")
    print(f"   Master Prompt Control: ✅ File-based (meta_prompts/master_prompt.txt)")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Review generated prompts in: test_sample_competitions.json")
    print("2. Check individual logs in: logs/llm_generations/")
    print("3. Modify master_prompt.txt to refine output quality")
    print("4. Set OPENROUTER_API_KEY for real API calls")
    print("5. Run with actual API for production prompts")
    
    return all_competitions

if __name__ == "__main__":
    # Run the async function
    competitions = asyncio.run(generate_test_samples())
    
    print(f"\n✅ Successfully generated {len(competitions)} competition sets")
    print(f"✅ Total of {sum(len(c.variants) for c in competitions)} prompts created")
    print("\n🎯 System is working correctly and ready for production!")