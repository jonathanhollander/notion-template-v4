#!/usr/bin/env python3
"""
Prompt Template System for Ultra-Premium Image Generation
Manages structured prompt generation with emotional intelligence and luxury aesthetics
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

class AssetType(Enum):
    """Types of assets to generate"""
    ICON = "icon"
    COVER = "cover"
    LETTER_HEADER = "letter_header"
    DATABASE_ICON = "database_icon"
    TEXTURE = "texture"

class PageTier(Enum):
    """Visual hierarchy tiers"""
    HUB = "hub"  # Command centers
    SECTION = "section"  # Functional areas
    DOCUMENT = "document"  # Legal/financial
    LETTER = "letter"  # Correspondence
    DIGITAL = "digital"  # Digital legacy

class EmotionalTone(Enum):
    """Emotional tones for different contexts"""
    WARM_WELCOME = "warm_welcome"  # Entry points
    TRUSTED_GUIDE = "trusted_guide"  # Executor sections
    FAMILY_HERITAGE = "family_heritage"  # Family sections
    SECURE_PROTECTION = "secure_protection"  # Financial/legal
    PEACEFUL_TRANSITION = "peaceful_transition"  # Difficult topics
    LIVING_CONTINUITY = "living_continuity"  # Legacy sections
    TECH_BRIDGE = "tech_bridge"  # Digital sections

@dataclass
class StyleElements:
    """Visual style elements for consistency"""
    materials: List[str] = field(default_factory=list)
    lighting: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    textures: List[str] = field(default_factory=list)
    objects: List[str] = field(default_factory=list)
    composition: List[str] = field(default_factory=list)

@dataclass
class EmotionalElements:
    """Emotional intelligence elements"""
    comfort_symbols: List[str] = field(default_factory=list)
    human_touches: List[str] = field(default_factory=list)
    continuity_metaphors: List[str] = field(default_factory=list)
    warmth_markers: List[str] = field(default_factory=list)
    life_elements: List[str] = field(default_factory=list)

@dataclass
class PromptTemplate:
    """Complete prompt template with all elements"""
    asset_type: AssetType
    page_tier: PageTier
    emotional_tone: EmotionalTone
    base_description: str
    style_elements: StyleElements
    emotional_elements: EmotionalElements
    technical_specs: Dict[str, Any] = field(default_factory=dict)
    section_theme: Optional[str] = None
    unique_focal_point: Optional[str] = None

class PromptTemplateManager:
    """Manages prompt templates with emotional intelligence and luxury aesthetics"""
    
    def __init__(self):
        """Initialize template manager with predefined templates"""
        self.templates = {}
        self.section_themes = self._initialize_section_themes()
        self.emotional_mappings = self._initialize_emotional_mappings()
        self.style_library = self._initialize_style_library()
        
    def _initialize_section_themes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize section-specific visual themes"""
        return {
            'admin': {
                'aesthetic': 'Mission Control meets Executive Boardroom',
                'palette': ['charcoal', 'platinum', 'electric blue'],
                'materials': ['brushed steel', 'smoked glass', 'carbon fiber'],
                'lighting': 'cool focused LED',
                'emotional_tone': EmotionalTone.TRUSTED_GUIDE
            },
            'executor': {
                'aesthetic': 'Law Library meets Private Study',
                'palette': ['deep mahogany', 'forest green', 'aged brass'],
                'materials': ['leather-bound books', 'wood paneling', 'bronze fixtures'],
                'lighting': 'warm lamplight through amber glass',
                'emotional_tone': EmotionalTone.TRUSTED_GUIDE
            },
            'family': {
                'aesthetic': 'Heritage Estate meets Memory Lane',
                'palette': ['warm oak', 'sage green', 'antique gold'],
                'materials': ['heirloom wood', 'vintage fabrics', 'family silver'],
                'lighting': 'soft golden hour',
                'emotional_tone': EmotionalTone.FAMILY_HERITAGE
            },
            'financial': {
                'aesthetic': 'Private Bank meets Vault Room',
                'palette': ['navy blue', 'champagne gold', 'pearl white'],
                'materials': ['marble columns', 'brass fixtures', 'security glass'],
                'lighting': 'precise clean confidence',
                'emotional_tone': EmotionalTone.SECURE_PROTECTION
            },
            'property': {
                'aesthetic': 'Architect Office meets Estate Grounds',
                'palette': ['blueprint blue', 'surveyor green', 'terra cotta'],
                'materials': ['drafting paper', 'copper pipes', 'estate stone'],
                'lighting': 'natural daylight precision',
                'emotional_tone': EmotionalTone.LIVING_CONTINUITY
            },
            'digital': {
                'aesthetic': 'Traditional Luxury meets Modern Tech',
                'palette': ['mahogany with blue glow', 'gold circuits', 'screen light'],
                'materials': ['wood desk with devices', 'leather with aluminum', 'glass displays'],
                'lighting': 'ambient screen glow on traditional surfaces',
                'emotional_tone': EmotionalTone.TECH_BRIDGE
            },
            'letters': {
                'aesthetic': 'Formal Correspondence meets Personal Touch',
                'palette': ['cream parchment', 'midnight ink', 'wax seal colors'],
                'materials': ['quality paper', 'fountain pen', 'wax seals', 'ribbon'],
                'lighting': 'soft desk lamp on writing surface',
                'emotional_tone': EmotionalTone.PEACEFUL_TRANSITION
            }
        }
    
    def _initialize_emotional_mappings(self) -> Dict[EmotionalTone, EmotionalElements]:
        """Initialize emotional element mappings"""
        return {
            EmotionalTone.WARM_WELCOME: EmotionalElements(
                comfort_symbols=['open door', 'warm tea', 'soft blanket'],
                human_touches=['reading glasses', 'family photos visible'],
                continuity_metaphors=['sunrise', 'new leaves on tree'],
                warmth_markers=['golden light', 'amber tones', 'rose gold'],
                life_elements=['fresh flowers', 'open window', 'morning light']
            ),
            EmotionalTone.TRUSTED_GUIDE: EmotionalElements(
                comfort_symbols=['guiding light', 'steady hand', 'compass'],
                human_touches=['well-worn journal', 'coffee mug', 'personal notes'],
                continuity_metaphors=['lighthouse beam', 'path through garden'],
                warmth_markers=['desk lamp glow', 'leather patina', 'wood grain'],
                life_elements=['plant on desk', 'bookmark in book', 'pen with character']
            ),
            EmotionalTone.FAMILY_HERITAGE: EmotionalElements(
                comfort_symbols=['family tree', 'photo albums', 'heirloom quilt'],
                human_touches=['handwritten recipes', 'children drawings', 'worn edges'],
                continuity_metaphors=['generations in photos', 'oak tree rings', 'river flow'],
                warmth_markers=['fireplace glow', 'sunset colors', 'honey tones'],
                life_elements=['birthday candles', 'garden growth', 'seasonal decorations']
            ),
            EmotionalTone.SECURE_PROTECTION: EmotionalElements(
                comfort_symbols=['umbrella in storm', 'safe harbor', 'strong foundation'],
                human_touches=['family provision', 'protective embrace', 'careful planning'],
                continuity_metaphors=['seeds to garden', 'nest egg', 'bridge to future'],
                warmth_markers=['vault interior warmth', 'gold security', 'trust symbols'],
                life_elements=['growth charts', 'future plans', 'provision markers']
            ),
            EmotionalTone.PEACEFUL_TRANSITION: EmotionalElements(
                comfort_symbols=['gentle sunset', 'calm waters', 'soft twilight'],
                human_touches=['held hands', 'tissue box nearby', 'thoughtful pause'],
                continuity_metaphors=['passing torch', 'tide cycles', 'season change'],
                warmth_markers=['twilight purple', 'star emergence', 'moon glow'],
                life_elements=['candle passing flame', 'letter sealed with care', 'peaceful moment']
            ),
            EmotionalTone.LIVING_CONTINUITY: EmotionalElements(
                comfort_symbols=['eternal flame', 'evergreen', 'circle unbroken'],
                human_touches=['legacy items', 'inherited treasures', 'passed down'],
                continuity_metaphors=['river meeting sea', 'roots and branches', 'echo forward'],
                warmth_markers=['timeless gold', 'heritage bronze', 'lasting warmth'],
                life_elements=['perennial garden', 'family recipes', 'stories retold']
            ),
            EmotionalTone.TECH_BRIDGE: EmotionalElements(
                comfort_symbols=['connection maintained', 'digital embrace', 'cloud safety'],
                human_touches=['video call family', 'digital photos', 'online memories'],
                continuity_metaphors=['wifi as connection', 'cloud as eternal', 'digital legacy'],
                warmth_markers=['screen warmth on wood', 'device glow', 'pixel light'],
                life_elements=['active profiles', 'living documents', 'updated feeds']
            )
        }
    
    def _initialize_style_library(self) -> Dict[str, StyleElements]:
        """Initialize reusable style elements"""
        return {
            'luxury_base': StyleElements(
                materials=['mahogany', 'leather', 'brass', 'marble', 'silk'],
                lighting=['3-point lighting', 'rim light', 'golden hour', 'lamplight'],
                colors=['deep mahogany', 'warm amber', 'antique gold', 'aged brass'],
                textures=['wood grain', 'leather texture', 'paper fiber', 'fabric weave'],
                objects=['fountain pen', 'pocket watch', 'leather journal', 'crystal glass'],
                composition=['rule of thirds', 'golden ratio', 'layered depth', 'focal hierarchy']
            ),
            'emotional_warmth': StyleElements(
                materials=['worn leather', 'soft fabric', 'weathered wood', 'brushed metal'],
                lighting=['warm glow', 'soft shadows', 'filtered sunlight', 'candle light'],
                colors=['honey gold', 'sage green', 'warm cream', 'sunset orange'],
                textures=['soft edges', 'gentle grain', 'comfortable wear', 'lived patina'],
                objects=['family photos', 'tea cup', 'reading glasses', 'cozy blanket'],
                composition=['intimate framing', 'personal scale', 'approachable angle', 'welcoming space']
            ),
            'professional_trust': StyleElements(
                materials=['polished wood', 'quality paper', 'solid metal', 'clear glass'],
                lighting=['even illumination', 'professional', 'confidence lighting', 'clarity'],
                colors=['navy blue', 'forest green', 'charcoal', 'burgundy'],
                textures=['smooth finish', 'crisp edges', 'professional', 'refined'],
                objects=['legal documents', 'official seals', 'professional tools', 'certificates'],
                composition=['balanced', 'structured', 'organized', 'authoritative']
            )
        }
    
    def create_prompt(self, 
                     title: str,
                     category: str,
                     asset_type: str,
                     tier: str = None,
                     custom_elements: Dict[str, Any] = None) -> str:
        """Create a complete prompt with all elements"""
        
        # Determine asset type enum
        asset_enum = AssetType(asset_type.lower())
        
        # Determine page tier with mapping from VisualTier
        if tier:
            # Map VisualTier values to PageTier values
            tier_mapping = {
                'tier_1_hub': 'hub',
                'tier_2_section': 'section', 
                'tier_3_document': 'document',
                'tier_4_letter': 'letter',
                'tier_5_digital': 'digital'
            }
            tier_value = tier_mapping.get(tier.lower(), tier.lower())
            page_tier = PageTier(tier_value)
        else:
            # Auto-detect tier based on title
            if 'hub' in title.lower():
                page_tier = PageTier.HUB
            elif 'letter' in title.lower():
                page_tier = PageTier.LETTER
            elif any(term in title.lower() for term in ['google', 'apple', 'facebook', 'digital']):
                page_tier = PageTier.DIGITAL
            elif any(term in title.lower() for term in ['will', 'trust', 'insurance', 'account']):
                page_tier = PageTier.DOCUMENT
            else:
                page_tier = PageTier.SECTION
        
        # Get section theme
        section_theme = self.section_themes.get(category.lower(), self.section_themes['family'])
        emotional_tone = section_theme['emotional_tone']
        
        # Get emotional elements
        emotional_elements = self.emotional_mappings[emotional_tone]
        
        # Build base description based on tier
        base_descriptions = {
            PageTier.HUB: f"Ultra-luxury command center for {title}, the grand entrance and anchor point for {category} section",
            PageTier.SECTION: f"Premium functional interface for {title} within the {category} domain",
            PageTier.DOCUMENT: f"Professional trustworthy document interface for {title} with security elements",
            PageTier.LETTER: f"Elegant formal correspondence template for {title} with personal touches",
            PageTier.DIGITAL: f"Hybrid luxury-tech interface for {title} blending tradition with modern technology"
        }
        base_description = base_descriptions[page_tier]
        
        # Combine style elements
        style = self.style_library['luxury_base']
        emotional_style = self.style_library['emotional_warmth']
        
        # Build the complete prompt
        prompt_parts = [base_description]
        
        # Add aesthetic
        prompt_parts.append(f"{section_theme['aesthetic']} aesthetic")
        
        # Add materials
        materials = list(set(style.materials + section_theme['materials'][:3]))
        prompt_parts.append(f"featuring {', '.join(materials[:4])}")
        
        # Add lighting
        prompt_parts.append(f"illuminated by {section_theme['lighting']}")
        
        # Add emotional elements
        emotional_items = []
        if emotional_elements.comfort_symbols:
            emotional_items.append(emotional_elements.comfort_symbols[0])
        if emotional_elements.human_touches:
            emotional_items.append(emotional_elements.human_touches[0])
        if emotional_elements.continuity_metaphors:
            emotional_items.append(emotional_elements.continuity_metaphors[0])
        
        if emotional_items:
            prompt_parts.append(f"with {', '.join(emotional_items)} for emotional warmth")
        
        # Add color palette
        colors = section_theme['palette']
        prompt_parts.append(f"in {', '.join(colors)} color palette")
        
        # Add unique focal point based on title
        focal_points = {
            'executor': 'scales of justice in warm brass',
            'family': 'multi-generational photo arrangement',
            'financial': 'vault door with family crest',
            'property': 'architectural blueprints with heritage markers',
            'admin': 'control panel with data streams',
            'digital': 'tablet showing family photos',
            'letter': 'wax seal with personal emblem'
        }
        
        for key, focal in focal_points.items():
            if key in title.lower() or key in category.lower():
                prompt_parts.append(f"centered on {focal}")
                break
        
        # Add technical specifications based on asset type
        tech_specs = {
            AssetType.ICON: "SVG vector art optimized for 24px-256px display with metallic gradients and dimensional shadows",
            AssetType.COVER: "1500x400px cinematic panoramic composition with 5-7 parallax layers and negative space for content overlay",
            AssetType.LETTER_HEADER: "1920x400px elegant letterhead with watermark patterns at 5% opacity and foil stamp effects",
            AssetType.DATABASE_ICON: "structured data visualization icon with organized grid patterns",
            AssetType.TEXTURE: "512x512px seamless tiling texture with multiple detail levels"
        }
        
        prompt_parts.append(tech_specs[asset_enum])
        
        # Add quality markers
        prompt_parts.append("ultra-high-end luxury quality with emotional accessibility")
        
        # Join all parts
        complete_prompt = ", ".join(prompt_parts)
        
        # Add custom elements if provided
        if custom_elements:
            if custom_elements.get('additional_elements'):
                complete_prompt += f", {custom_elements['additional_elements']}"
        
        return complete_prompt
    
    def create_prompt_variants(self, base_info: Dict[str, Any], num_variants: int = 3) -> List[str]:
        """Create multiple variants of a prompt for comparison"""
        variants = []
        
        # Variant 1: Emphasis on emotional warmth
        variant1 = self.create_prompt(
            title=base_info['title'],
            category=base_info['category'],
            asset_type=base_info['asset_type'],
            tier=base_info.get('tier'),
            custom_elements={'additional_elements': 'emphasizing human warmth and personal connection'}
        )
        variants.append(variant1)
        
        # Variant 2: Emphasis on luxury aesthetics
        variant2 = self.create_prompt(
            title=base_info['title'],
            category=base_info['category'],
            asset_type=base_info['asset_type'],
            tier=base_info.get('tier'),
            custom_elements={'additional_elements': 'emphasizing ultra-premium materials and sophisticated luxury'}
        )
        variants.append(variant2)
        
        # Variant 3: Emphasis on technical precision
        variant3 = self.create_prompt(
            title=base_info['title'],
            category=base_info['category'],
            asset_type=base_info['asset_type'],
            tier=base_info.get('tier'),
            custom_elements={'additional_elements': 'emphasizing precise composition and visual consistency'}
        )
        variants.append(variant3)
        
        return variants[:num_variants]
    
    def save_templates(self, output_file: str = "prompt_templates.json"):
        """Save all templates to file"""
        data = {
            'section_themes': {k: {**v, 'emotional_tone': v['emotional_tone'].value} 
                             for k, v in self.section_themes.items()},
            'emotional_mappings': {
                tone.value: {
                    'comfort_symbols': elements.comfort_symbols,
                    'human_touches': elements.human_touches,
                    'continuity_metaphors': elements.continuity_metaphors,
                    'warmth_markers': elements.warmth_markers,
                    'life_elements': elements.life_elements
                }
                for tone, elements in self.emotional_mappings.items()
            },
            'style_library': {
                name: {
                    'materials': style.materials,
                    'lighting': style.lighting,
                    'colors': style.colors,
                    'textures': style.textures,
                    'objects': style.objects,
                    'composition': style.composition
                }
                for name, style in self.style_library.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_file


def test_prompt_templates():
    """Test the prompt template system"""
    manager = PromptTemplateManager()
    
    # Test different page types
    test_cases = [
        {'title': 'Executor Hub', 'category': 'executor', 'asset_type': 'icon', 'tier': 'hub'},
        {'title': 'Family Messages', 'category': 'family', 'asset_type': 'cover', 'tier': 'section'},
        {'title': 'Last Will', 'category': 'financial', 'asset_type': 'icon', 'tier': 'document'},
        {'title': 'Letter to Spouse', 'category': 'letters', 'asset_type': 'letter_header', 'tier': 'letter'},
        {'title': 'Google Account Recovery', 'category': 'digital', 'asset_type': 'icon', 'tier': 'digital'}
    ]
    
    print("PROMPT TEMPLATE TESTS")
    print("=" * 80)
    
    for test in test_cases:
        print(f"\n{test['title']}:")
        print("-" * 40)
        
        # Generate single prompt
        prompt = manager.create_prompt(
            title=test['title'],
            category=test['category'],
            asset_type=test['asset_type'],
            tier=test['tier']
        )
        print(f"Prompt: {prompt[:200]}...")
        
        # Generate variants
        variants = manager.create_prompt_variants(test, num_variants=3)
        print(f"Generated {len(variants)} variants")
    
    # Save templates
    output = manager.save_templates()
    print(f"\nTemplates saved to: {output}")


if __name__ == "__main__":
    test_prompt_templates()