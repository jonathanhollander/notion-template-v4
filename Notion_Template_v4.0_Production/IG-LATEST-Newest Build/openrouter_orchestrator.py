#!/usr/bin/env python3
"""
OpenRouter AI Orchestrator for Competitive Prompt Generation
Orchestrates multiple AI models to generate competing prompts with quality scoring
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from websocket_broadcaster import get_broadcaster
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path
import re

@dataclass
class StructuredPrompt:
    """Structured prompt output from LLM"""
    system_message: str
    temperature: float
    role: str
    prompt: str
    raw_response: str
    
@dataclass
class PromptVariant:
    """Single prompt variant from a model"""
    model: str
    structured_prompt: StructuredPrompt
    style_elements: List[str]
    emotional_markers: List[str]
    luxury_indicators: List[str]
    confidence: float
    reasoning: str
    timestamp: str

@dataclass
class PromptCompetition:
    """Results from competitive prompt generation"""
    page_title: str
    page_category: str
    asset_type: str  # icon, cover, letter_header
    variants: List[PromptVariant]
    winner: Optional[PromptVariant] = None
    human_selected: Optional[PromptVariant] = None
    scores: Optional[Dict[str, float]] = None

class OpenRouterOrchestrator:
    """Orchestrates multiple AI models via OpenRouter for competitive prompt generation"""
    
    def __init__(self, api_key: str = None):
        """Initialize the orchestrator with OpenRouter API key"""
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        # Model configurations for different perspectives

        
        # Initialize WebSocket broadcaster for real-time visibility
        try:
            self.broadcaster = get_broadcaster()
            self.logger.info("✓ WebSocket broadcaster initialized in OpenRouter orchestrator")
        except Exception as e:
            self.broadcaster = None
            self.logger.warning(f"WebSocket broadcaster not available: {e}")
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
                'id': 'google/gemini-2.5-flash',
                'perspective': 'technical_precision',
                'strengths': ['precision', 'consistency', 'structure']
            }
        }
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.logger = self._setup_logger()
        # Master prompt is now loaded dynamically based on asset_type
        self.logs_dir = Path("logs/llm_generations")
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the orchestrator"""
        logger = logging.getLogger('OpenRouterOrchestrator')
        logger.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        fh = logging.FileHandler('openrouter_orchestration.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _load_master_prompt(self, asset_type: str = None) -> str:
        """Load the master prompt from file based on asset type
        
        Args:
            asset_type: Type of asset ('icons', 'covers', etc.)
                       If None, loads the default master_prompt.txt
        """
        # Determine which master prompt file to use
        if asset_type in ['icons', 'database_icons']:
            # Use icon-specific master prompt for icon assets
            master_prompt_file = "master_prompt_icons.txt"
        elif asset_type in ['covers', 'cover']:
            # Use cover-specific master prompt for cover assets
            master_prompt_file = "master_prompt_covers.txt"
        else:
            # Use default master prompt for other assets or when not specified
            master_prompt_file = "master_prompt.txt"
        
        master_prompt_path = Path("meta_prompts") / master_prompt_file
        
        # Try to load the specific master prompt, fall back to default if not found
        try:
            with open(master_prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.logger.info(f"Loaded master prompt from {master_prompt_path} for asset_type: {asset_type}")
            return content
        except FileNotFoundError:
            if master_prompt_file != "master_prompt.txt":
                # Try to fall back to default master prompt
                self.logger.warning(f"Master prompt file not found: {master_prompt_path}, trying default")
                default_path = Path("meta_prompts/master_prompt.txt")
                try:
                    with open(default_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.logger.info(f"Loaded default master prompt from {default_path}")
                    return content
                except FileNotFoundError:
                    self.logger.error(f"Default master prompt file not found: {default_path}")
                    raise ValueError(f"Neither specific nor default master prompt file found")
            else:
                self.logger.error(f"Master prompt file not found: {master_prompt_path}")
                raise ValueError(f"Master prompt file not found: {master_prompt_path}")
        except Exception as e:
            self.logger.error(f"Failed to load master prompt: {e}")
            raise
    
    def _parse_structured_response(self, raw_response: str) -> StructuredPrompt:
        """Parse structured response from LLM with SYSTEM/TEMPERATURE/ROLE/PROMPT format"""
        try:
            # Look for the structured format using regex
            system_match = re.search(r'SYSTEM:\s*(.*?)(?=\n\nTEMPERATURE:|$)', raw_response, re.DOTALL | re.IGNORECASE)
            temp_match = re.search(r'TEMPERATURE:\s*([\d.]+)', raw_response, re.IGNORECASE)
            role_match = re.search(r'ROLE:\s*(.*?)(?=\n\nPROMPT:|$)', raw_response, re.DOTALL | re.IGNORECASE)
            prompt_match = re.search(r'PROMPT:\s*(.*?)(?=\n\n---|\n\n[A-Z]+:|\Z)', raw_response, re.DOTALL | re.IGNORECASE)
            
            # Extract values with fallbacks
            system_message = system_match.group(1).strip() if system_match else "You are a luxury brand designer specializing in estate planning visuals."
            temperature = float(temp_match.group(1)) if temp_match else 0.5
            role = role_match.group(1).strip() if role_match else "luxury brand designer"
            prompt = prompt_match.group(1).strip() if prompt_match else raw_response.strip()
            
            # Validate temperature range
            temperature = max(0.1, min(1.0, temperature))
            
            return StructuredPrompt(
                system_message=system_message,
                temperature=temperature,
                role=role,
                prompt=prompt,
                raw_response=raw_response
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to parse structured response, using fallback: {e}")
            return StructuredPrompt(
                system_message="You are a luxury brand designer specializing in estate planning visuals.",
                temperature=0.5,
                role="luxury brand designer",
                prompt=raw_response.strip(),
                raw_response=raw_response
            )
    
    def _log_llm_interaction(self, model: str, context_data: Dict[str, Any], response: StructuredPrompt, timestamp: str):
        """Log comprehensive LLM interaction details"""
        log_entry = {
            'timestamp': timestamp,
            'model': model,
            'context_data': context_data,
            'structured_response': {
                'system_message': response.system_message,
                'temperature': response.temperature,
                'role': response.role,
                'prompt': response.prompt,
                'raw_response': response.raw_response
            }
        }
        
        # Save to individual log file
        log_filename = f"llm_generation_{model}_{timestamp.replace(':', '-').replace('.', '-')}.json"
        log_path = self.logs_dir / log_filename
        
        try:
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Logged LLM interaction to {log_path}")
        except Exception as e:
            self.logger.error(f"Failed to log LLM interaction: {e}")
        
        # Also append to master log
        master_log = self.logs_dir / "master_llm_log.jsonl"
        try:
            with open(master_log, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to append to master log: {e}")
    
    async def _call_openrouter_with_master_prompt(self, model_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make an async call to OpenRouter API using ONLY master prompt + context data"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://estate-planning-concierge.com",
            "X-Title": "Estate Planning Concierge v4.0"
        }
        
        # Load the appropriate master prompt based on asset type
        asset_type = context_data.get('asset_type', 'UNKNOWN')
        master_prompt = self._load_master_prompt(asset_type)
        
        # Build context section for the master prompt
        context_section = f"""
CONTEXT DATA:
- Visual Tier: {context_data.get('tier', 'UNKNOWN')}
- Emotional Context: {context_data.get('emotional_context', 'UNKNOWN')}
- Asset Type: {asset_type}
- Title: {context_data.get('title', 'UNKNOWN')}
- Category: {context_data.get('category', 'UNKNOWN')}
- Section: {context_data.get('section', 'general')}

"""
        
        # Combine master prompt with context data - NO system message, NO other parameters
        full_prompt = master_prompt + context_section
        
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            "temperature": 0.7,  # Fixed temperature for the meta-prompt call
            "max_tokens": 2000
        }
        
        timestamp = datetime.now().isoformat()
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        raw_response = result['choices'][0]['message']['content']
                        
                        # Parse structured response
                        structured_prompt = self._parse_structured_response(raw_response)
                        
                        # Log the interaction comprehensively
                        self._log_llm_interaction(model_id, context_data, structured_prompt, timestamp)
                        
                        return {
                            'success': True,
                            'structured_prompt': structured_prompt,
                            'model': model_id,
                            'usage': result.get('usage', {}),
                            'timestamp': timestamp
                        }
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f"API error: {response.status}",
                            'model': model_id
                        }
            except Exception as e:
                self.logger.error(f"OpenRouter request failed: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'model': model_id
                }
    
    def _prepare_context_data(self, page_info: Dict[str, Any], model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context data for the master prompt"""
        return {
            'title': page_info['title'],
            'category': page_info['category'],
            'asset_type': page_info['asset_type'],
            'section': page_info.get('section', 'general'),
            'tier': page_info.get('tier', 'standard'),
            'emotional_context': page_info.get('emotional_context', 'DIGNIFIED_PLANNING'),
            'model_perspective': model_config['perspective'],
            'model_strengths': model_config['strengths']
        }
    
    async def generate_competitive_prompts(self, page_info: Dict[str, Any]) -> PromptCompetition:
        """Generate competitive prompts using structured master prompt system"""
        self.logger.info(f"Generating competitive prompts for: {page_info['title']}")
        
        # Emit model competition start event
        if self.broadcaster:
            self.broadcaster.emit('model_competition_start', {
                'asset_name': page_info.get('title', 'Unknown'),
                'models': list(self.models.keys()),
                'timestamp': datetime.now().isoformat()
            })
        
        # Create tasks for parallel execution using new structured approach
        tasks = []
        for model_name, model_config in self.models.items():
            context_data = self._prepare_context_data(page_info, model_config)
            task = self._call_openrouter_with_master_prompt(model_config['id'], context_data)
            tasks.append((model_name, task))
        
        # Execute all tasks in parallel
        results = []
        for model_name, task in tasks:
            result = await task
            
            # Emit prompt generation event
            if self.broadcaster and result['success']:
                self.broadcaster.emit('prompt_generated', {
                    'model': model_name,
                    'asset_name': page_info.get('title', 'Unknown'),
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                })
            
            if result['success']:
                structured_prompt = result['structured_prompt']
                
                # Extract style elements, emotional markers, etc. from the generated prompt
                # This is a simplified extraction - could be enhanced with NLP analysis
                style_elements = self._extract_style_elements(structured_prompt.prompt)
                emotional_markers = self._extract_emotional_markers(structured_prompt.prompt)
                luxury_indicators = self._extract_luxury_indicators(structured_prompt.prompt)
                
                variant = PromptVariant(
                    model=model_name,
                    structured_prompt=structured_prompt,
                    style_elements=style_elements,
                    emotional_markers=emotional_markers,
                    luxury_indicators=luxury_indicators,
                    confidence=0.8,  # High confidence since using structured master prompt
                    reasoning=f"Generated using master prompt with {model_config['perspective']} perspective",
                    timestamp=result['timestamp']
                )
                results.append(variant)
                self.logger.info(f"Successfully generated structured prompt from {model_name}")
            else:
                self.logger.error(f"Failed to get response from {model_name}: {result.get('error')}")
        
        # Create competition results
        competition = PromptCompetition(
            page_title=page_info['title'],
            page_category=page_info['category'],
            asset_type=page_info['asset_type'],
            variants=results
        )
        
        return competition
    
    def _extract_style_elements(self, prompt: str) -> List[str]:
        """Extract style elements from generated prompt"""
        style_keywords = ['luxury', 'premium', 'elegant', 'sophisticated', 'warm', 'mahogany', 
                         'leather', 'gold', 'marble', 'crystal', 'silk', 'velvet', 'bronze']
        found_elements = [keyword for keyword in style_keywords if keyword.lower() in prompt.lower()]
        return found_elements[:5]  # Limit to top 5
    
    def _extract_emotional_markers(self, prompt: str) -> List[str]:
        """Extract emotional markers from generated prompt"""
        emotional_keywords = ['compassionate', 'warm', 'gentle', 'caring', 'family', 'legacy', 
                             'heritage', 'memories', 'comfort', 'trust', 'dignity', 'respect']
        found_markers = [keyword for keyword in emotional_keywords if keyword.lower() in prompt.lower()]
        return found_markers[:5]  # Limit to top 5
    
    def _extract_luxury_indicators(self, prompt: str) -> List[str]:
        """Extract luxury indicators from generated prompt"""
        luxury_keywords = ['private', 'exclusive', 'bespoke', 'handcrafted', 'artisanal', 
                          'executive', 'prestige', 'estate', 'mansion', 'penthouse', 'limousine']
        found_indicators = [keyword for keyword in luxury_keywords if keyword.lower() in prompt.lower()]
        return found_indicators[:5]  # Limit to top 5
    
    async def score_prompts(self, competition: PromptCompetition) -> PromptCompetition:
        """Score competing prompts using AI evaluation"""
        self.logger.info(f"Scoring prompts for: {competition.page_title}")
        
        # Build scoring prompt
        scoring_prompt = f"""
Evaluate these competing image generation prompts for an estate planning application.
Score each on these criteria (0-10):
1. Emotional Intelligence - warmth, compassion, human connection
2. Luxury Aesthetic - premium materials, sophisticated design
3. Technical Clarity - specificity, achievability, precision
4. Visual Consistency - style unity, brand coherence
5. Innovation - creative approach, unique perspective

Page Context:
- Title: {competition.page_title}
- Category: {competition.page_category}
- Asset Type: {competition.asset_type}

Prompts to evaluate:
"""
        
        for i, variant in enumerate(competition.variants, 1):
            scoring_prompt += f"""

Prompt {i} ({variant.model}):
{variant.prompt}
Style elements: {', '.join(variant.style_elements)}
Emotional markers: {', '.join(variant.emotional_markers)}
Luxury indicators: {', '.join(variant.luxury_indicators)}
"""
        
        scoring_prompt += """

Provide scores in JSON format:
{
    "scores": {
        "prompt_1": {
            "emotional_intelligence": 0-10,
            "luxury_aesthetic": 0-10,
            "technical_clarity": 0-10,
            "visual_consistency": 0-10,
            "innovation": 0-10,
            "total": sum,
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"]
        },
        ...
    },
    "recommended": 1-3,
    "reasoning": "explanation for recommendation"
}
"""
        
        # Use GPT-4 for scoring (tends to be most balanced)
        result = await self._call_openrouter(self.models['gpt4']['id'], scoring_prompt, temperature=0.3)
        
        if result['success']:
            try:
                scores = json.loads(result['content'])
                competition.scores = scores['scores']
                
                # Determine winner based on scores
                if scores.get('recommended'):
                    winner_idx = scores['recommended'] - 1
                    if 0 <= winner_idx < len(competition.variants):
                        competition.winner = competition.variants[winner_idx]
                
                self.logger.info(f"Successfully scored prompts, winner: {competition.winner.model if competition.winner else 'None'}")
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse scoring response: {e}")
        
        return competition
    
    async def orchestrate_competition(self, pages: List[Dict[str, Any]]) -> List[PromptCompetition]:
        """Orchestrate prompt competition for multiple pages"""
        competitions = []
        
        for page in pages:
            self.logger.info(f"Starting competition for: {page['title']}")
            
            # Generate competitive prompts
            competition = await self.generate_competitive_prompts(page)
            
            # Score the prompts
            competition = await self.score_prompts(competition)
            
            competitions.append(competition)
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        return competitions
    
    def save_competition_results(self, competitions: List[PromptCompetition], output_file: str = "prompt_competitions.json"):
        """Save competition results to file"""
        output_path = Path(output_file)
        
        # Convert to serializable format
        data = []
        for comp in competitions:
            # Handle new structured format
            variants_data = []
            for v in comp.variants:
                variant_dict = {
                    'model': v.model,
                    'structured_prompt': {
                        'system_message': v.structured_prompt.system_message,
                        'temperature': v.structured_prompt.temperature,
                        'role': v.structured_prompt.role,
                        'prompt': v.structured_prompt.prompt,
                        'raw_response': v.structured_prompt.raw_response
                    },
                    'style_elements': v.style_elements,
                    'emotional_markers': v.emotional_markers,
                    'luxury_indicators': v.luxury_indicators,
                    'confidence': v.confidence,
                    'reasoning': v.reasoning,
                    'timestamp': v.timestamp
                }
                variants_data.append(variant_dict)
            
            comp_dict = {
                'page_title': comp.page_title,
                'page_category': comp.page_category,
                'asset_type': comp.asset_type,
                'variants': variants_data,
                'winner': {
                    'model': comp.winner.model,
                    'structured_prompt': {
                        'system_message': comp.winner.structured_prompt.system_message,
                        'temperature': comp.winner.structured_prompt.temperature,
                        'role': comp.winner.structured_prompt.role,
                        'prompt': comp.winner.structured_prompt.prompt,
                        'raw_response': comp.winner.structured_prompt.raw_response
                    } if comp.winner else None
                } if comp.winner else None,
                'human_selected': {
                    'model': comp.human_selected.model,
                    'structured_prompt': {
                        'system_message': comp.human_selected.structured_prompt.system_message,
                        'temperature': comp.human_selected.structured_prompt.temperature,
                        'role': comp.human_selected.structured_prompt.role,
                        'prompt': comp.human_selected.structured_prompt.prompt,
                        'raw_response': comp.human_selected.structured_prompt.raw_response
                    } if comp.human_selected else None
                } if comp.human_selected else None,
                'scores': comp.scores
            }
            data.append(comp_dict)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        self.logger.info(f"Saved {len(competitions)} competition results to {output_path}")
        
        return output_path



    def emit_progress(self, message: str, level: str = "info"):
        """Emit progress update via WebSocket"""
        if self.broadcaster:
            self.broadcaster.emit_log(message, level)
    
    def emit_cost_update(self, model: str, cost: float):
        """Emit cost tracking update"""
        if self.broadcaster:
            self.broadcaster.emit('openrouter_cost', {
                'model': model,
                'cost': cost,
                'timestamp': datetime.now().isoformat()
            })
    
    def emit_model_decision(self, winner_model: str, reasons: List[str]):
        """Emit model decision reasoning"""
        if self.broadcaster:
            self.broadcaster.model_decision(winner_model, reasons)

async def test_orchestrator():
    """Test the orchestrator with sample pages"""
    orchestrator = OpenRouterOrchestrator()
    
    # Test pages representing different categories
    test_pages = [
        {
            'title': 'Executor Hub',
            'category': 'executor',
            'asset_type': 'icon',
            'section': 'executor',
            'tier': 'hub'
        },
        {
            'title': 'Family Messages',
            'category': 'family',
            'asset_type': 'cover',
            'section': 'family',
            'tier': 'section'
        }
    ]
    
    # Run competition
    competitions = await orchestrator.orchestrate_competition(test_pages)
    
    # Save results
    output_file = orchestrator.save_competition_results(competitions)
    
    print(f"Competition complete! Results saved to: {output_file}")
    
    # Display summary
    for comp in competitions:
        print(f"\n{comp.page_title}:")
        print(f"  Variants generated: {len(comp.variants)}")
        for variant in comp.variants:
            print(f"    {variant.model}: {variant.structured_prompt.prompt[:100]}...")
            print(f"      System: {variant.structured_prompt.system_message[:50]}...")
            print(f"      Temperature: {variant.structured_prompt.temperature}")
            print(f"      Role: {variant.structured_prompt.role}")
        if comp.winner:
            print(f"  Winner: {comp.winner.model} (confidence: {comp.winner.confidence:.2f})")
        print(f"  Scores: {comp.scores}")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_orchestrator())