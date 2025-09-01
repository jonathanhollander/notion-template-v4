#!/usr/bin/env python3
"""
AI-Powered Quality Scorer for Estate Planning Concierge v4.0
Evaluates prompt quality using multiple AI models for objective scoring
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path
from enum import Enum

class ScoringCriterion(Enum):
    """Quality scoring criteria for estate planning prompts"""
    EMOTIONAL_INTELLIGENCE = "emotional_intelligence"
    LUXURY_AESTHETIC = "luxury_aesthetic" 
    TECHNICAL_CLARITY = "technical_clarity"
    VISUAL_CONSISTENCY = "visual_consistency"
    INNOVATION = "innovation"
    ESTATE_PLANNING_RELEVANCE = "estate_planning_relevance"
    BRAND_COHERENCE = "brand_coherence"

@dataclass
class QualityScore:
    """Individual quality score for a specific criterion"""
    criterion: ScoringCriterion
    score: float  # 0-10
    reasoning: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]

@dataclass
class PromptEvaluation:
    """Complete evaluation of a single prompt"""
    prompt_id: str
    prompt_text: str
    model_source: str
    category: str
    asset_type: str
    individual_scores: List[QualityScore]
    overall_score: float
    weighted_score: float
    evaluation_timestamp: str
    evaluator_model: str
    
    @property
    def score_breakdown(self) -> Dict[str, float]:
        """Get scores by criterion"""
        return {score.criterion.value: score.score for score in self.individual_scores}

@dataclass
class CompetitiveEvaluation:
    """Evaluation results for competing prompts"""
    page_title: str
    page_category: str
    asset_type: str
    prompt_evaluations: List[PromptEvaluation]
    winner: Optional[PromptEvaluation] = None
    consensus_scores: Optional[Dict[str, float]] = None
    evaluation_summary: Optional[str] = None

class QualityScorer:
    """AI-powered quality scoring system for estate planning prompts"""
    
    def __init__(self, openrouter_api_key: str = None):
        """Initialize the quality scorer"""
        self.api_key = openrouter_api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
            
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.logger = self._setup_logger()
        
        # Scoring criteria weights (sum to 1.0)
        self.scoring_weights = {
            ScoringCriterion.EMOTIONAL_INTELLIGENCE: 0.25,  # Critical for estate planning
            ScoringCriterion.LUXURY_AESTHETIC: 0.20,        # Brand positioning
            ScoringCriterion.TECHNICAL_CLARITY: 0.15,       # Generation quality
            ScoringCriterion.VISUAL_CONSISTENCY: 0.15,      # Brand coherence
            ScoringCriterion.INNOVATION: 0.10,              # Creative differentiation
            ScoringCriterion.ESTATE_PLANNING_RELEVANCE: 0.10, # Domain expertise
            ScoringCriterion.BRAND_COHERENCE: 0.05         # Overall fit
        }
        
        # Evaluator models (different perspectives)
        self.evaluator_models = {
            'detailed_analyzer': {
                'id': 'anthropic/claude-3-opus-20240229',
                'perspective': 'detailed_analysis',
                'strengths': ['thorough_evaluation', 'nuanced_feedback', 'estate_planning_expertise']
            },
            'luxury_expert': {
                'id': 'openai/gpt-4-turbo-preview', 
                'perspective': 'luxury_assessment',
                'strengths': ['luxury_brand_expertise', 'visual_aesthetics', 'premium_positioning']
            },
            'technical_validator': {
                'id': 'google/gemini-pro',
                'perspective': 'technical_validation',
                'strengths': ['technical_precision', 'consistency_checking', 'implementation_feasibility']
            }
        }
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the quality scorer"""
        logger = logging.getLogger('QualityScorer')
        logger.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler  
        fh = logging.FileHandler('quality_scoring.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    async def _call_evaluator_model(self, model_id: str, prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """Make an async call to an evaluator model"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://estate-planning-concierge.com",
            "X-Title": "Estate Planning Concierge v4.0 - Quality Evaluation"
        }
        
        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in luxury brand design and estate planning user experience. Provide detailed, objective evaluations with specific reasoning."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": 2000
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'content': result['choices'][0]['message']['content'],
                            'model': model_id,
                            'usage': result.get('usage', {})
                        }
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Evaluator API error: {response.status} - {error_text}")
                        return {
                            'success': False,
                            'error': f"API error: {response.status}",
                            'model': model_id
                        }
            except Exception as e:
                self.logger.error(f"Evaluator request failed: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'model': model_id
                }
    
    def _build_evaluation_prompt(self, prompt_to_evaluate: str, context: Dict[str, Any], 
                                evaluator_perspective: str) -> str:
        """Build evaluation prompt for a specific evaluator perspective"""
        
        base_context = f"""
Evaluate this image generation prompt for an estate planning application.

CONTEXT:
- Page: {context['page_title']}
- Category: {context['page_category']} 
- Asset Type: {context['asset_type']}
- Target User: Families planning estates, executors managing estates
- Brand Position: Ultra-premium, luxury estate planning service
- Emotional Sensitivity: High (dealing with end-of-life planning)

PROMPT TO EVALUATE:
{prompt_to_evaluate}

EVALUATION CRITERIA (Score 0-10 for each):

1. EMOTIONAL INTELLIGENCE (0-10)
   - Warmth, compassion, human connection
   - Sensitivity to estate planning emotional context
   - Comfort and reassurance elements
   - Avoidance of cold, clinical, or frightening imagery

2. LUXURY AESTHETIC (0-10)  
   - Premium materials (mahogany, leather, gold, marble)
   - Sophisticated lighting and composition
   - High-end brand aesthetic (private bank, law firm quality)
   - Exclusivity and craftsmanship indicators

3. TECHNICAL CLARITY (0-10)
   - Specificity and achievability for AI image generation
   - Clear visual descriptions and technical parameters
   - Consistent style language and terminology
   - Practical implementation feasibility

4. VISUAL CONSISTENCY (0-10)
   - Brand coherence with estate planning theme
   - Style unity within the luxury aesthetic
   - Appropriate visual hierarchy for asset type
   - Consistency with stated visual tier and section

5. INNOVATION (0-10)
   - Creative approach beyond generic templates
   - Unique perspective or visual metaphors
   - Fresh take on traditional estate planning imagery
   - Memorable and distinctive visual concepts

6. ESTATE PLANNING RELEVANCE (0-10)
   - Appropriate for the specific estate planning context
   - Understanding of user needs and emotional state
   - Relevance to page function and user goals
   - Professional expertise indicators

7. BRAND COHERENCE (0-10)
   - Fits with luxury estate planning service positioning
   - Maintains dignity and gravitas appropriate to context
   - Consistent with high-end professional service branding
   - Appropriate tone for target demographic
"""

        if evaluator_perspective == 'detailed_analysis':
            specific_focus = """
Your evaluation should be COMPREHENSIVE and DETAILED. Focus on:
- Deep analysis of emotional intelligence and user psychology
- Thorough assessment of estate planning domain expertise
- Detailed breakdown of strengths and weaknesses
- Specific, actionable improvement suggestions
- Nuanced understanding of grief, responsibility, and family dynamics
"""
        elif evaluator_perspective == 'luxury_assessment':
            specific_focus = """
Your evaluation should focus on LUXURY BRAND EXPERTISE. Focus on:
- Premium material references and craftsmanship indicators
- Sophisticated visual composition and lighting
- High-end brand positioning and exclusivity markers
- Comparison to luxury service standards (private banking, high-end law firms)
- Visual differentiation from mass-market alternatives
"""
        else:  # technical_validation
            specific_focus = """
Your evaluation should focus on TECHNICAL PRECISION. Focus on:
- AI image generation feasibility and specificity
- Consistent terminology and style language
- Technical clarity of visual descriptions
- Implementation practicality and resource requirements
- Consistency validation against stated parameters
"""
        
        full_prompt = base_context + specific_focus + """

REQUIRED JSON FORMAT:
{
    "scores": {
        "emotional_intelligence": 0-10,
        "luxury_aesthetic": 0-10, 
        "technical_clarity": 0-10,
        "visual_consistency": 0-10,
        "innovation": 0-10,
        "estate_planning_relevance": 0-10,
        "brand_coherence": 0-10
    },
    "detailed_analysis": {
        "emotional_intelligence": {
            "score": 0-10,
            "reasoning": "detailed explanation",
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1", "weakness2"],
            "suggestions": ["suggestion1", "suggestion2"]
        },
        // ... repeat for all criteria
    },
    "overall_assessment": {
        "overall_score": 0-10,
        "key_strengths": ["strength1", "strength2", "strength3"],
        "key_weaknesses": ["weakness1", "weakness2", "weakness3"], 
        "improvement_priority": "highest_priority_area",
        "summary": "brief overall assessment"
    }
}

Provide thorough, objective evaluation with specific evidence from the prompt.
"""
        
        return full_prompt
    
    async def evaluate_single_prompt(self, prompt_text: str, context: Dict[str, Any], 
                                   evaluator_model: str = 'detailed_analyzer') -> PromptEvaluation:
        """Evaluate a single prompt using specified evaluator model"""
        
        model_config = self.evaluator_models[evaluator_model]
        evaluation_prompt = self._build_evaluation_prompt(
            prompt_text, context, model_config['perspective']
        )
        
        # Call the evaluator model
        result = await self._call_evaluator_model(model_config['id'], evaluation_prompt)
        
        if not result['success']:
            self.logger.error(f"Failed to evaluate prompt with {evaluator_model}: {result.get('error')}")
            raise Exception(f"Evaluation failed: {result.get('error')}")
        
        try:
            # Parse the JSON response
            evaluation_data = json.loads(result['content'])
            
            # Extract individual scores
            individual_scores = []
            for criterion_name, criterion_data in evaluation_data.get('detailed_analysis', {}).items():
                if criterion_name in [c.value for c in ScoringCriterion]:
                    criterion_enum = ScoringCriterion(criterion_name)
                    quality_score = QualityScore(
                        criterion=criterion_enum,
                        score=criterion_data.get('score', 0),
                        reasoning=criterion_data.get('reasoning', ''),
                        strengths=criterion_data.get('strengths', []),
                        weaknesses=criterion_data.get('weaknesses', []),
                        suggestions=criterion_data.get('suggestions', [])
                    )
                    individual_scores.append(quality_score)
            
            # Calculate weighted score
            weighted_score = sum(
                score.score * self.scoring_weights.get(score.criterion, 0)
                for score in individual_scores
            )
            
            prompt_evaluation = PromptEvaluation(
                prompt_id=f"{context['page_title']}_{context['asset_type']}_{evaluator_model}",
                prompt_text=prompt_text,
                model_source=context.get('model_source', 'unknown'),
                category=context['page_category'],
                asset_type=context['asset_type'],
                individual_scores=individual_scores,
                overall_score=evaluation_data.get('overall_assessment', {}).get('overall_score', 0),
                weighted_score=weighted_score,
                evaluation_timestamp=datetime.now().isoformat(),
                evaluator_model=evaluator_model
            )
            
            self.logger.info(f"Successfully evaluated prompt: {prompt_evaluation.prompt_id} (Score: {weighted_score:.2f})")
            
            return prompt_evaluation
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse evaluation response: {e}")
            raise Exception(f"Invalid evaluation response format: {e}")
    
    async def evaluate_competitive_prompts(self, prompts: List[Dict[str, Any]], 
                                         context: Dict[str, Any]) -> CompetitiveEvaluation:
        """Evaluate multiple competing prompts and determine winner"""
        
        self.logger.info(f"Evaluating {len(prompts)} competitive prompts for {context['page_title']}")
        
        # Evaluate each prompt with multiple evaluators
        all_evaluations = []
        
        for i, prompt_data in enumerate(prompts):
            prompt_context = {
                **context,
                'model_source': prompt_data.get('model_source', f'prompt_{i+1}')
            }
            
            # Evaluate with primary detailed analyzer
            try:
                evaluation = await self.evaluate_single_prompt(
                    prompt_data['prompt'], prompt_context, 'detailed_analyzer'
                )
                all_evaluations.append(evaluation)
                
                # Small delay between evaluations
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Failed to evaluate prompt {i+1}: {e}")
                continue
        
        if not all_evaluations:
            raise Exception("No prompts could be evaluated successfully")
        
        # Determine winner (highest weighted score)
        winner = max(all_evaluations, key=lambda x: x.weighted_score)
        
        # Calculate consensus scores (averages across evaluations)
        consensus_scores = {}
        for criterion in ScoringCriterion:
            criterion_scores = []
            for evaluation in all_evaluations:
                for score in evaluation.individual_scores:
                    if score.criterion == criterion:
                        criterion_scores.append(score.score)
            if criterion_scores:
                consensus_scores[criterion.value] = sum(criterion_scores) / len(criterion_scores)
        
        # Generate evaluation summary
        evaluation_summary = self._generate_evaluation_summary(all_evaluations, winner, consensus_scores)
        
        competitive_evaluation = CompetitiveEvaluation(
            page_title=context['page_title'],
            page_category=context['page_category'],
            asset_type=context['asset_type'],
            prompt_evaluations=all_evaluations,
            winner=winner,
            consensus_scores=consensus_scores,
            evaluation_summary=evaluation_summary
        )
        
        self.logger.info(f"Competitive evaluation complete. Winner: {winner.model_source} (Score: {winner.weighted_score:.2f})")
        
        return competitive_evaluation
    
    def _generate_evaluation_summary(self, evaluations: List[PromptEvaluation], 
                                   winner: PromptEvaluation, 
                                   consensus_scores: Dict[str, float]) -> str:
        """Generate a summary of the competitive evaluation"""
        
        summary_parts = [
            f"COMPETITIVE EVALUATION SUMMARY",
            f"Total Prompts Evaluated: {len(evaluations)}",
            f"Winner: {winner.model_source} (Weighted Score: {winner.weighted_score:.2f})",
            f"",
            f"CONSENSUS SCORES (Average across all prompts):"
        ]
        
        for criterion, score in consensus_scores.items():
            summary_parts.append(f"  {criterion.replace('_', ' ').title()}: {score:.2f}/10")
        
        summary_parts.extend([
            f"",
            f"TOP PERFORMING AREAS:",
            f"  Best: {max(consensus_scores.items(), key=lambda x: x[1])[0].replace('_', ' ').title()} ({max(consensus_scores.values()):.2f}/10)",
            f"",
            f"IMPROVEMENT OPPORTUNITIES:",
            f"  Focus: {min(consensus_scores.items(), key=lambda x: x[1])[0].replace('_', ' ').title()} ({min(consensus_scores.values()):.2f}/10)",
            f"",
            f"WINNER ANALYSIS:",
            f"  Model: {winner.model_source}",
            f"  Overall Score: {winner.overall_score:.2f}/10",
            f"  Weighted Score: {winner.weighted_score:.2f}/10"
        ])
        
        return "\n".join(summary_parts)
    
    def save_evaluation_results(self, competitive_evaluations: List[CompetitiveEvaluation], 
                              output_file: str = "quality_evaluation_results.json") -> Path:
        """Save evaluation results to file"""
        output_path = Path(output_file)
        
        # Convert to serializable format
        data = {
            'evaluation_metadata': {
                'total_evaluations': len(competitive_evaluations),
                'scoring_criteria': [c.value for c in ScoringCriterion],
                'scoring_weights': {k.value: v for k, v in self.scoring_weights.items()},
                'evaluator_models': self.evaluator_models,
                'evaluation_timestamp': datetime.now().isoformat()
            },
            'competitive_evaluations': [],
            'summary_statistics': self._generate_overall_statistics(competitive_evaluations)
        }
        
        for comp_eval in competitive_evaluations:
            eval_data = {
                'page_title': comp_eval.page_title,
                'page_category': comp_eval.page_category,
                'asset_type': comp_eval.asset_type,
                'prompt_evaluations': [asdict(pe) for pe in comp_eval.prompt_evaluations],
                'winner': asdict(comp_eval.winner) if comp_eval.winner else None,
                'consensus_scores': comp_eval.consensus_scores,
                'evaluation_summary': comp_eval.evaluation_summary
            }
            data['competitive_evaluations'].append(eval_data)
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Evaluation results saved to {output_path}")
        return output_path
    
    def _generate_overall_statistics(self, competitive_evaluations: List[CompetitiveEvaluation]) -> Dict[str, Any]:
        """Generate overall statistics across all evaluations"""
        
        all_scores = []
        winner_models = []
        criterion_averages = {c.value: [] for c in ScoringCriterion}
        
        for comp_eval in competitive_evaluations:
            if comp_eval.winner:
                all_scores.append(comp_eval.winner.weighted_score)
                winner_models.append(comp_eval.winner.model_source)
            
            if comp_eval.consensus_scores:
                for criterion, score in comp_eval.consensus_scores.items():
                    if criterion in criterion_averages:
                        criterion_averages[criterion].append(score)
        
        # Calculate statistics
        stats = {
            'overall_quality_metrics': {
                'average_winner_score': sum(all_scores) / len(all_scores) if all_scores else 0,
                'highest_score': max(all_scores) if all_scores else 0,
                'lowest_score': min(all_scores) if all_scores else 0,
                'score_distribution': {
                    'excellent_8_10': sum(1 for s in all_scores if s >= 8),
                    'good_6_8': sum(1 for s in all_scores if 6 <= s < 8),
                    'needs_improvement_0_6': sum(1 for s in all_scores if s < 6)
                }
            },
            'model_performance': {},
            'criterion_analysis': {}
        }
        
        # Model performance analysis
        from collections import Counter
        model_counts = Counter(winner_models)
        stats['model_performance'] = {
            'winner_frequency': dict(model_counts),
            'top_performing_model': model_counts.most_common(1)[0][0] if model_counts else None
        }
        
        # Criterion analysis
        for criterion, scores in criterion_averages.items():
            if scores:
                stats['criterion_analysis'][criterion] = {
                    'average_score': sum(scores) / len(scores),
                    'highest_score': max(scores),
                    'lowest_score': min(scores),
                    'consistency': max(scores) - min(scores)  # Lower is more consistent
                }
        
        return stats


async def test_quality_scorer():
    """Test the quality scorer with sample prompts"""
    scorer = QualityScorer()
    
    # Sample competitive prompts for testing
    test_prompts = [
        {
            'prompt': "Ultra-luxury icon for 'Executor Hub': mahogany law library aesthetic, scales of justice in polished brass, leather-bound book spine texture, three-tier gradient from amber to bronze, floating shadow with gold rim light, ornate serif details, SVG vector art optimized for 24px-256px display",
            'model_source': 'claude_emotional'
        },
        {
            'prompt': "Premium executor hub icon with sophisticated materials: dark mahogany wood paneling, brass legal scales, rich leather textures, golden ambient lighting, executive office atmosphere, professional gravitas, high-end law firm aesthetic, vector art format",
            'model_source': 'gpt4_luxury'
        },
        {
            'prompt': "Technical precision executor icon: mahogany material properties with 15% gloss, brass scales at 45-degree angle, leather texture with 2px embossed grain, 3-point lighting setup, golden ratio composition, SVG vector format optimized for responsive display",
            'model_source': 'gemini_technical'
        }
    ]
    
    test_context = {
        'page_title': 'Executor Hub',
        'page_category': 'executor',
        'asset_type': 'icon'
    }
    
    print("🎯 Testing Quality Scorer with Estate Planning prompts...")
    
    # Evaluate competitive prompts
    competitive_eval = await scorer.evaluate_competitive_prompts(test_prompts, test_context)
    
    # Save results
    output_file = scorer.save_evaluation_results([competitive_eval])
    
    print(f"\n✅ Quality scoring complete!")
    print(f"📊 Evaluated {len(test_prompts)} prompts")
    print(f"🏆 Winner: {competitive_eval.winner.model_source} (Score: {competitive_eval.winner.weighted_score:.2f})")
    print(f"📁 Results saved to: {output_file}")
    
    print(f"\n📋 Evaluation Summary:")
    print(competitive_eval.evaluation_summary)
    
    return output_file


if __name__ == "__main__":
    # Run test
    asyncio.run(test_quality_scorer())