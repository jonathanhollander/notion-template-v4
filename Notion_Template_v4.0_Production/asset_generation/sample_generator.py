#!/usr/bin/env python3
"""
Sample Generator for Estate Planning Concierge v4.0
Generates 3x3 matrix samples for testing prompt quality across different categories
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path
import random

from openrouter_orchestrator import OpenRouterOrchestrator, PromptCompetition
from sync_yaml_comprehensive import YAMLSyncComprehensive
from visual_hierarchy import VisualTier, SectionType
from emotional_elements import EmotionalContext, ComfortLevel

@dataclass
class SampleCategory:
    """Represents a category for sample generation"""
    name: str
    visual_tier: VisualTier
    section_theme: SectionType
    emotional_context: EmotionalContext
    comfort_level: ComfortLevel
    sample_titles: List[str]

@dataclass
class SampleMatrix:
    """3x3 matrix sample configuration"""
    categories: List[SampleCategory]
    asset_types: List[str]  # icon, cover, letter_header
    total_samples: int
    generation_timestamp: str

@dataclass
class GeneratedSample:
    """Individual generated sample with metadata"""
    category: str
    asset_type: str
    title: str
    base_prompt: str
    enhanced_prompts: List[str]  # From different models
    emotional_markers: List[str]
    luxury_indicators: List[str]
    visual_tier: str
    section_theme: str
    quality_scores: Optional[Dict[str, float]] = None
    generation_time: Optional[float] = None

class SampleGenerator:
    """Generates representative samples for testing the prompt generation system"""
    
    def __init__(self, yaml_dir: str = "../split_yaml"):
        """Initialize the sample generator"""
        self.yaml_system = YAMLSyncComprehensive(yaml_dir)
        self.orchestrator = OpenRouterOrchestrator()
        self.logger = self._setup_logger()
        
        # Define our 3x3 sample matrix
        self.sample_categories = self._define_sample_categories()
        self.asset_types = ['icon', 'cover', 'letter_header']
        
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the sample generator"""
        logger = logging.getLogger('SampleGenerator')
        logger.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler
        fh = logging.FileHandler('sample_generation.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        return logger
    
    def _define_sample_categories(self) -> List[SampleCategory]:
        """Define the core categories for our 3x3 matrix"""
        return [
            # Row 1: Hub Pages (Tier 1 - Highest luxury)
            SampleCategory(
                name="Preparation Hub",
                visual_tier=VisualTier.TIER_1_HUB,
                section_theme=SectionType.ADMIN,
                emotional_context=EmotionalContext.PROACTIVE_PLANNING,
                comfort_level=ComfortLevel.CONFIDENT,
                sample_titles=["Preparation Hub", "Getting Started Guide", "Estate Planning Overview"]
            ),
            SampleCategory(
                name="Executor Hub", 
                visual_tier=VisualTier.TIER_1_HUB,
                section_theme=SectionType.EXECUTOR,
                emotional_context=EmotionalContext.PROACTIVE_PLANNING,
                comfort_level=ComfortLevel.EXPERT,
                sample_titles=["Executor Hub", "Executor Responsibilities", "Estate Administration"]
            ),
            SampleCategory(
                name="Family Hub",
                visual_tier=VisualTier.TIER_1_HUB, 
                section_theme=SectionType.FAMILY,
                emotional_context=EmotionalContext.CELEBRATION,
                comfort_level=ComfortLevel.CAUTIOUS,
                sample_titles=["Family Hub", "Messages for Loved Ones", "Legacy Preservation"]
            ),
            
            # Row 2: Section Pages (Tier 2 - High luxury with function)
            SampleCategory(
                name="Financial Accounts",
                visual_tier=VisualTier.TIER_2_SECTION,
                section_theme=SectionType.FINANCIAL,
                emotional_context=EmotionalContext.PROACTIVE_PLANNING,
                comfort_level=ComfortLevel.EXPERT,
                sample_titles=["Bank Accounts", "Investment Portfolio", "Financial Assets"]
            ),
            SampleCategory(
                name="Legal Documents",
                visual_tier=VisualTier.TIER_3_DOCUMENT,
                section_theme=SectionType.EXECUTOR,
                emotional_context=EmotionalContext.PROACTIVE_PLANNING,
                comfort_level=ComfortLevel.EXPERT,
                sample_titles=["Last Will & Testament", "Power of Attorney", "Trust Documents"]
            ),
            SampleCategory(
                name="Digital Legacy",
                visual_tier=VisualTier.TIER_2_SECTION,
                section_theme=SectionType.DIGITAL,
                emotional_context=EmotionalContext.PROACTIVE_PLANNING,
                comfort_level=ComfortLevel.CONFIDENT,
                sample_titles=["Google Account Access", "Social Media Accounts", "Digital Assets"]
            ),
            
            # Row 3: Sensitive Context (Emotional intelligence testing)
            SampleCategory(
                name="Funeral Planning",
                visual_tier=VisualTier.TIER_2_SECTION,
                section_theme=SectionType.FAMILY,
                emotional_context=EmotionalContext.LOSS_PROCESSING,
                comfort_level=ComfortLevel.CAUTIOUS,
                sample_titles=["Funeral Preferences", "Memorial Service", "Final Arrangements"]
            ),
            SampleCategory(
                name="Medical Directives", 
                visual_tier=VisualTier.TIER_3_DOCUMENT,
                section_theme=SectionType.FAMILY,
                emotional_context=EmotionalContext.HEALTH_CONCERN,
                comfort_level=ComfortLevel.CONFIDENT,
                sample_titles=["Living Will", "Healthcare Proxy", "Medical Preferences"]
            ),
            SampleCategory(
                name="Letter Templates",
                visual_tier=VisualTier.TIER_4_LETTER,
                section_theme=SectionType.FAMILY,
                emotional_context=EmotionalContext.CELEBRATION,
                comfort_level=ComfortLevel.ANXIOUS,
                sample_titles=["Letter to Spouse", "Letter to Children", "Final Messages"]
            )
        ]
    
    async def generate_sample_matrix(self) -> SampleMatrix:
        """Generate the complete 3x3 sample matrix"""
        self.logger.info("Generating 3x3 sample matrix for Estate Planning Concierge v4.0")
        
        samples = []
        total_start_time = datetime.now()
        
        for category in self.sample_categories:
            for asset_type in self.asset_types:
                # Select a representative title for this category
                title = random.choice(category.sample_titles)
                
                # Generate sample for this category/asset combination
                sample = await self._generate_single_sample(category, asset_type, title)
                samples.append(sample)
                
                self.logger.info(f"Generated sample: {category.name} - {asset_type} - {title}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
        
        total_time = (datetime.now() - total_start_time).total_seconds()
        
        matrix = SampleMatrix(
            categories=self.sample_categories,
            asset_types=self.asset_types,
            total_samples=len(samples),
            generation_timestamp=datetime.now().isoformat()
        )
        
        self.logger.info(f"Sample matrix generation complete: {len(samples)} samples in {total_time:.1f}s")
        
        return matrix, samples
    
    async def _generate_single_sample(self, category: SampleCategory, asset_type: str, title: str) -> GeneratedSample:
        """Generate a single sample with competitive prompts"""
        start_time = datetime.now()
        
        # Create page info for the orchestrator
        page_info = {
            'title': title,
            'category': category.name.lower().replace(' ', '_'),
            'asset_type': asset_type,
            'section': category.section_theme.value,
            'tier': category.visual_tier.value
        }
        
        # Generate competitive prompts
        competition = await self.orchestrator.generate_competitive_prompts(page_info)
        
        # Extract base prompt from our YAML system
        base_prompt = self.yaml_system._generate_enhanced_prompt(
            title, asset_type, category.section_theme.value
        )
        
        # Collect enhanced prompts from competition
        enhanced_prompts = [variant.prompt for variant in competition.variants]
        
        # Aggregate emotional markers and luxury indicators
        emotional_markers = []
        luxury_indicators = []
        
        for variant in competition.variants:
            emotional_markers.extend(variant.emotional_markers)
            luxury_indicators.extend(variant.luxury_indicators)
        
        # Remove duplicates while preserving order
        emotional_markers = list(dict.fromkeys(emotional_markers))
        luxury_indicators = list(dict.fromkeys(luxury_indicators))
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        sample = GeneratedSample(
            category=category.name,
            asset_type=asset_type,
            title=title,
            base_prompt=base_prompt,
            enhanced_prompts=enhanced_prompts,
            emotional_markers=emotional_markers,
            luxury_indicators=luxury_indicators,
            visual_tier=category.visual_tier.value,
            section_theme=category.section_theme.value,
            generation_time=generation_time
        )
        
        return sample
    
    def save_sample_matrix(self, matrix: SampleMatrix, samples: List[GeneratedSample], 
                          output_file: str = "sample_matrix_results.json") -> Path:
        """Save the sample matrix results to file"""
        output_path = Path(output_file)
        
        # Convert to serializable format
        data = {
            'matrix_config': {
                'categories': [
                    {
                        'name': cat.name,
                        'visual_tier': cat.visual_tier.value,
                        'section_theme': cat.section_theme.value,
                        'emotional_context': cat.emotional_context.value,
                        'comfort_level': cat.comfort_level.value,
                        'sample_titles': cat.sample_titles
                    }
                    for cat in matrix.categories
                ],
                'asset_types': matrix.asset_types,
                'total_samples': matrix.total_samples,
                'generation_timestamp': matrix.generation_timestamp
            },
            'samples': [asdict(sample) for sample in samples],
            'summary': self._generate_summary(samples)
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        self.logger.info(f"Sample matrix saved to {output_path}")
        return output_path
    
    def _generate_summary(self, samples: List[GeneratedSample]) -> Dict[str, Any]:
        """Generate summary statistics for the sample matrix"""
        total_samples = len(samples)
        
        # Count by category
        category_counts = {}
        for sample in samples:
            category_counts[sample.category] = category_counts.get(sample.category, 0) + 1
        
        # Count by asset type
        asset_type_counts = {}
        for sample in samples:
            asset_type_counts[sample.asset_type] = asset_type_counts.get(sample.asset_type, 0) + 1
        
        # Average generation time
        generation_times = [s.generation_time for s in samples if s.generation_time]
        avg_generation_time = sum(generation_times) / len(generation_times) if generation_times else 0
        
        # Count unique elements
        all_emotional_markers = set()
        all_luxury_indicators = set()
        
        for sample in samples:
            all_emotional_markers.update(sample.emotional_markers)
            all_luxury_indicators.update(sample.luxury_indicators)
        
        return {
            'total_samples': total_samples,
            'category_distribution': category_counts,
            'asset_type_distribution': asset_type_counts,
            'average_generation_time_seconds': round(avg_generation_time, 2),
            'unique_emotional_markers': len(all_emotional_markers),
            'unique_luxury_indicators': len(all_luxury_indicators),
            'emotional_markers_list': sorted(list(all_emotional_markers)),
            'luxury_indicators_list': sorted(list(all_luxury_indicators))
        }
    
    def generate_quality_report(self, samples: List[GeneratedSample]) -> Dict[str, Any]:
        """Generate a quality analysis report for the samples"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_samples_analyzed': len(samples),
            'quality_metrics': {}
        }
        
        # Analyze emotional intelligence coverage
        emotional_contexts = set()
        comfort_levels = set()
        
        for sample in samples:
            # Count emotional markers per sample
            emotional_marker_count = len(sample.emotional_markers)
            luxury_indicator_count = len(sample.luxury_indicators)
            
            # Track variety
            emotional_contexts.add(sample.category)  # Using category as proxy for emotional context
        
        # Calculate coverage metrics
        report['quality_metrics'] = {
            'emotional_marker_coverage': {
                'average_markers_per_sample': sum(len(s.emotional_markers) for s in samples) / len(samples),
                'samples_with_emotional_markers': sum(1 for s in samples if s.emotional_markers),
                'unique_emotional_contexts_covered': len(emotional_contexts)
            },
            'luxury_aesthetic_coverage': {
                'average_luxury_indicators_per_sample': sum(len(s.luxury_indicators) for s in samples) / len(samples),
                'samples_with_luxury_indicators': sum(1 for s in samples if s.luxury_indicators),
                'luxury_coverage_percentage': (sum(1 for s in samples if s.luxury_indicators) / len(samples)) * 100
            },
            'prompt_quality': {
                'average_enhanced_prompts_per_sample': sum(len(s.enhanced_prompts) for s in samples) / len(samples),
                'samples_with_multiple_model_variants': sum(1 for s in samples if len(s.enhanced_prompts) > 1)
            }
        }
        
        return report


async def test_sample_generator():
    """Test the sample generator with the 3x3 matrix"""
    generator = SampleGenerator()
    
    # Generate the sample matrix
    print("🎨 Generating 3x3 sample matrix for Estate Planning Concierge v4.0...")
    matrix, samples = await generator.generate_sample_matrix()
    
    # Save results
    output_file = generator.save_sample_matrix(matrix, samples)
    
    # Generate quality report
    quality_report = generator.generate_quality_report(samples)
    
    # Save quality report
    quality_file = Path("sample_quality_report.json")
    with open(quality_file, 'w') as f:
        json.dump(quality_report, f, indent=2)
    
    print(f"\n✅ Sample generation complete!")
    print(f"📊 Generated {len(samples)} samples across 3x3 matrix")
    print(f"📁 Results saved to: {output_file}")
    print(f"📈 Quality report: {quality_file}")
    
    # Display summary
    summary = generator._generate_summary(samples)
    print(f"\n📋 Summary:")
    print(f"  Categories: {len(summary['category_distribution'])}")
    print(f"  Asset types: {len(summary['asset_type_distribution'])}")
    print(f"  Avg generation time: {summary['average_generation_time_seconds']}s")
    print(f"  Emotional markers: {summary['unique_emotional_markers']}")
    print(f"  Luxury indicators: {summary['unique_luxury_indicators']}")
    
    return output_file, quality_file


if __name__ == "__main__":
    # Run test
    asyncio.run(test_sample_generator())