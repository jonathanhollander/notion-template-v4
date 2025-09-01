#!/usr/bin/env python3
"""
Visual Hierarchy Manager for Ultra-Premium Estate Planning Interface
Manages 5-tier visual hierarchy with section-specific aesthetics and consistency
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
from pathlib import Path
import json

class VisualTier(Enum):
    """5-tier visual hierarchy for estate planning interface"""
    TIER_1_HUB = "tier_1_hub"  # Command centers (most elaborate)
    TIER_2_SECTION = "tier_2_section"  # Functional areas (inherit hub DNA)
    TIER_3_DOCUMENT = "tier_3_document"  # Legal/financial (professional trust)
    TIER_4_LETTER = "tier_4_letter"  # Correspondence (formal elegance)
    TIER_5_DIGITAL = "tier_5_digital"  # Digital legacy (hybrid luxury-tech)

class SectionType(Enum):
    """Estate planning section types"""
    ADMIN = "admin"  # Hidden administrative functions
    EXECUTOR = "executor"  # Executor responsibilities
    FAMILY = "family"  # Family communications
    FINANCIAL = "financial"  # Financial and insurance
    PROPERTY = "property"  # Property and assets
    DIGITAL = "digital"  # Digital legacy management
    LETTERS = "letters"  # Correspondence templates

@dataclass
class ComplexityProfile:
    """Visual complexity profile for different tiers"""
    layer_count: int  # Number of visual layers
    detail_density: float  # Amount of detail (0.0-1.0)
    metallic_intensity: float  # Metallic accent strength
    texture_layers: int  # Number of texture layers
    focal_elements: int  # Number of focal points
    lighting_complexity: str  # Lighting approach

@dataclass
class SectionAesthetic:
    """Complete aesthetic definition for a section"""
    name: str
    theme_description: str
    color_palette: List[str]
    primary_materials: List[str]
    secondary_materials: List[str]
    lighting_style: str
    architectural_elements: List[str]
    emotional_tone: str
    luxury_markers: List[str]

@dataclass
class HierarchyRule:
    """Rules for visual hierarchy relationships"""
    tier: VisualTier
    complexity_profile: ComplexityProfile
    inheritance_rules: Dict[str, Any]
    differentiation_requirements: List[str]

class VisualHierarchyManager:
    """Manages visual hierarchy and section consistency"""
    
    def __init__(self):
        """Initialize hierarchy manager with tier definitions"""
        self.tier_profiles = self._initialize_tier_profiles()
        self.section_aesthetics = self._initialize_section_aesthetics()
        self.hierarchy_rules = self._initialize_hierarchy_rules()
        self.hub_signatures = self._initialize_hub_signatures()
        
    def _initialize_tier_profiles(self) -> Dict[VisualTier, ComplexityProfile]:
        """Initialize complexity profiles for each tier"""
        return {
            VisualTier.TIER_1_HUB: ComplexityProfile(
                layer_count=7,
                detail_density=1.0,
                metallic_intensity=1.0,
                texture_layers=5,
                focal_elements=3,
                lighting_complexity="cinematic_multi_source"
            ),
            VisualTier.TIER_2_SECTION: ComplexityProfile(
                layer_count=5,
                detail_density=0.8,
                metallic_intensity=0.8,
                texture_layers=4,
                focal_elements=2,
                lighting_complexity="professional_two_source"
            ),
            VisualTier.TIER_3_DOCUMENT: ComplexityProfile(
                layer_count=4,
                detail_density=0.7,
                metallic_intensity=0.6,
                texture_layers=3,
                focal_elements=1,
                lighting_complexity="trusted_single_source"
            ),
            VisualTier.TIER_4_LETTER: ComplexityProfile(
                layer_count=3,
                detail_density=0.6,
                metallic_intensity=0.9,  # High for seals and accents
                texture_layers=4,  # Rich paper textures
                focal_elements=1,
                lighting_complexity="elegant_ambient"
            ),
            VisualTier.TIER_5_DIGITAL: ComplexityProfile(
                layer_count=5,
                detail_density=0.8,
                metallic_intensity=0.7,
                texture_layers=3,
                focal_elements=2,
                lighting_complexity="hybrid_tech_warm"
            )
        }
    
    def _initialize_section_aesthetics(self) -> Dict[SectionType, SectionAesthetic]:
        """Initialize complete aesthetic definitions for each section"""
        return {
            SectionType.ADMIN: SectionAesthetic(
                name="Executive Command Center",
                theme_description="Mission Control meets Executive Boardroom",
                color_palette=["charcoal (#2D3748)", "platinum (#E2E8F0)", "electric blue (#3B82F6)", "steel gray (#64748B)"],
                primary_materials=["brushed steel", "smoked glass", "carbon fiber"],
                secondary_materials=["matte black surfaces", "LED strips", "holographic displays"],
                lighting_style="cool focused LED with blue accent strips",
                architectural_elements=["geometric panels", "data visualization screens", "control interfaces"],
                emotional_tone="confident_authority",
                luxury_markers=["precision engineering", "aerospace materials", "cutting-edge technology"]
            ),
            
            SectionType.EXECUTOR: SectionAesthetic(
                name="Private Law Library",
                theme_description="Law Library meets Private Study",
                color_palette=["deep mahogany (#8B4513)", "forest green (#228B22)", "aged brass (#CD7F32)", "cream parchment (#F5F5DC)"],
                primary_materials=["rich mahogany wood", "leather-bound books", "aged brass fixtures"],
                secondary_materials=["parchment paper", "velvet curtains", "bronze hardware"],
                lighting_style="warm lamplight filtering through amber glass shades",
                architectural_elements=["wood paneling", "built-in bookshelves", "coffered ceilings"],
                emotional_tone="trusted_wisdom",
                luxury_markers=["hand-carved details", "leather binding", "traditional craftsmanship"]
            ),
            
            SectionType.FAMILY: SectionAesthetic(
                name="Heritage Estate Library",
                theme_description="Heritage Estate meets Memory Lane",
                color_palette=["warm oak (#DEB887)", "sage green (#9CAF88)", "antique gold (#CFB53B)", "cream silk (#FFF8DC)"],
                primary_materials=["heirloom oak wood", "vintage fabrics", "family silver"],
                secondary_materials=["photo albums", "handwritten letters", "quilted textiles"],
                lighting_style="soft golden hour sunlight through lace curtains",
                architectural_elements=["bay windows", "reading nooks", "display shelves"],
                emotional_tone="loving_heritage",
                luxury_markers=["generational pieces", "handmade textiles", "family treasures"]
            ),
            
            SectionType.FINANCIAL: SectionAesthetic(
                name="Private Banking Vault",
                theme_description="Private Bank meets Vault Room",
                color_palette=["navy blue (#191970)", "champagne gold (#F7E7CE)", "pearl white (#F8F8FF)", "platinum gray (#E5E4E2)"],
                primary_materials=["Italian marble", "polished brass", "security glass"],
                secondary_materials=["vault steel", "leather portfolios", "crystal accents"],
                lighting_style="precise clean confidence lighting with gold highlights",
                architectural_elements=["marble columns", "vault doors", "security panels"],
                emotional_tone="secure_prosperity",
                luxury_markers=["bank-grade materials", "precision engineering", "timeless elegance"]
            ),
            
            SectionType.PROPERTY: SectionAesthetic(
                name="Estate Architect's Office",
                theme_description="Architect's Office meets Estate Grounds",
                color_palette=["blueprint blue (#1E3A8A)", "surveyor green (#15803D)", "terra cotta (#E2725B)", "drafting white (#FAFAFA)"],
                primary_materials=["drafting paper", "copper accents", "natural stone"],
                secondary_materials=["surveyor tools", "architectural models", "estate maps"],
                lighting_style="natural daylight precision with architectural task lighting",
                architectural_elements=["drafting tables", "blueprint storage", "scale models"],
                emotional_tone="methodical_legacy",
                luxury_markers=["custom architectural details", "precision instruments", "estate craftsmanship"]
            ),
            
            SectionType.DIGITAL: SectionAesthetic(
                name="Tech-Heritage Bridge",
                theme_description="Traditional Luxury meets Modern Technology",
                color_palette=["mahogany with blue glow (#8B4513 + #3B82F6)", "circuit gold (#FFD700)", "screen silver (#C0C0C0)", "data green (#10B981)"],
                primary_materials=["mahogany desk surfaces", "brushed aluminum", "tempered glass"],
                secondary_materials=["fiber optic cables", "LED displays", "wireless chargers"],
                lighting_style="ambient screen glow reflecting on traditional surfaces",
                architectural_elements=["hidden cable management", "integrated displays", "wireless zones"],
                emotional_tone="connected_continuity",
                luxury_markers=["seamless integration", "premium tech materials", "invisible complexity"]
            ),
            
            SectionType.LETTERS: SectionAesthetic(
                name="Formal Correspondence Suite",
                theme_description="Formal Correspondence meets Personal Touch",
                color_palette=["cream parchment (#F5F5DC)", "midnight ink (#191970)", "wax seal red (#DC143C)", "gold leaf (#FFD700)"],
                primary_materials=["quality writing paper", "fountain pen metals", "sealing wax"],
                secondary_materials=["ribbon ties", "letter openers", "blotting paper"],
                lighting_style="soft desk lamp illumination on writing surface",
                architectural_elements=["writing desk", "letter storage", "correspondence tools"],
                emotional_tone="formal_intimacy",
                luxury_markers=["calligraphy quality", "premium stationery", "personal seals"]
            )
        }
    
    def _initialize_hierarchy_rules(self) -> Dict[VisualTier, HierarchyRule]:
        """Initialize hierarchy rules for tier relationships"""
        return {
            VisualTier.TIER_1_HUB: HierarchyRule(
                tier=VisualTier.TIER_1_HUB,
                complexity_profile=self.tier_profiles[VisualTier.TIER_1_HUB],
                inheritance_rules={
                    "establishes_section_dna": True,
                    "signature_elements_required": True,
                    "maximum_visual_impact": True,
                    "unique_focal_points": 3,
                    "metallic_gradients": "three_tier_gold_to_bronze"
                },
                differentiation_requirements=[
                    "unique_architectural_elements",
                    "signature_lighting_approach", 
                    "distinctive_metallic_accents",
                    "exclusive_texture_combinations"
                ]
            ),
            
            VisualTier.TIER_2_SECTION: HierarchyRule(
                tier=VisualTier.TIER_2_SECTION,
                complexity_profile=self.tier_profiles[VisualTier.TIER_2_SECTION],
                inheritance_rules={
                    "inherits_hub_base_layer": True,
                    "adds_functional_overlay": True,
                    "maintains_section_temperature": True,
                    "unique_focal_points": 2,
                    "metallic_gradients": "two_tier_primary_to_secondary"
                },
                differentiation_requirements=[
                    "functional_purpose_clear",
                    "hub_relationship_visible",
                    "individual_identity_maintained"
                ]
            ),
            
            VisualTier.TIER_3_DOCUMENT: HierarchyRule(
                tier=VisualTier.TIER_3_DOCUMENT,
                complexity_profile=self.tier_profiles[VisualTier.TIER_3_DOCUMENT],
                inheritance_rules={
                    "professional_trust_priority": True,
                    "security_elements_required": True,
                    "watermark_patterns": True,
                    "unique_focal_points": 1,
                    "metallic_gradients": "security_seal_emphasis"
                },
                differentiation_requirements=[
                    "document_type_identification",
                    "security_visual_markers",
                    "trustworthiness_indicators"
                ]
            ),
            
            VisualTier.TIER_4_LETTER: HierarchyRule(
                tier=VisualTier.TIER_4_LETTER,
                complexity_profile=self.tier_profiles[VisualTier.TIER_4_LETTER],
                inheritance_rules={
                    "letterhead_consistency": True,
                    "formal_elegance_required": True,
                    "wax_seal_elements": True,
                    "unique_focal_points": 1,
                    "metallic_gradients": "wax_seal_to_paper"
                },
                differentiation_requirements=[
                    "letter_type_distinction",
                    "formality_level_appropriate",
                    "personal_touch_balance"
                ]
            ),
            
            VisualTier.TIER_5_DIGITAL: HierarchyRule(
                tier=VisualTier.TIER_5_DIGITAL,
                complexity_profile=self.tier_profiles[VisualTier.TIER_5_DIGITAL],
                inheritance_rules={
                    "hybrid_aesthetic_required": True,
                    "platform_integration_subtle": True,
                    "tech_warmth_balance": True,
                    "unique_focal_points": 2,
                    "metallic_gradients": "circuit_to_traditional"
                },
                differentiation_requirements=[
                    "platform_specific_hints",
                    "technology_level_appropriate",
                    "traditional_luxury_maintained"
                ]
            )
        }
    
    def _initialize_hub_signatures(self) -> Dict[SectionType, Dict[str, Any]]:
        """Initialize signature elements that define each hub's visual DNA"""
        return {
            SectionType.EXECUTOR: {
                "signature_architectural": "coffered ceiling with warm wood tones",
                "signature_lighting": "banker's lamp with amber glass shade",
                "signature_metallic": "aged brass with patina highlights",
                "signature_texture": "leather book spines with gold lettering",
                "signature_focal": "scales of justice in warm bronze"
            },
            SectionType.FAMILY: {
                "signature_architectural": "bay window with window seat and cushions",
                "signature_lighting": "golden hour sunlight through lace curtains",
                "signature_metallic": "antique gold picture frame accents",
                "signature_texture": "heirloom quilt patterns in fabric textures",
                "signature_focal": "multi-generational family photo arrangement"
            },
            SectionType.FINANCIAL: {
                "signature_architectural": "marble columns with brass capital details",
                "signature_lighting": "precise LED strips with warm gold accents",
                "signature_metallic": "champagne gold vault hardware",
                "signature_texture": "Italian marble veining with security glass",
                "signature_focal": "vault door with family crest medallion"
            },
            SectionType.ADMIN: {
                "signature_architectural": "geometric control panels with data displays",
                "signature_lighting": "cool LED strips with electric blue accents",
                "signature_metallic": "brushed platinum with precision edges",
                "signature_texture": "carbon fiber weave with holographic elements",
                "signature_focal": "multi-screen command interface"
            }
        }
    
    def determine_visual_tier(self, title: str, category: str, asset_type: str) -> VisualTier:
        """Determine the appropriate visual tier for a page"""
        title_lower = title.lower()
        category_lower = category.lower()
        
        # Tier 1: Hub pages (command centers)
        hub_indicators = ['hub', 'dashboard', 'main', 'home', 'center', 'cockpit']
        if any(indicator in title_lower for indicator in hub_indicators):
            return VisualTier.TIER_1_HUB
        
        # Tier 4: Letters (formal correspondence)
        letter_indicators = ['letter', 'message', 'note', 'correspondence']
        if any(indicator in title_lower for indicator in letter_indicators) or 'letter' in category_lower:
            return VisualTier.TIER_4_LETTER
        
        # Tier 5: Digital legacy
        digital_indicators = ['google', 'apple', 'facebook', 'digital', 'online', 'cloud', 'account', 'social']
        if any(indicator in title_lower for indicator in digital_indicators):
            return VisualTier.TIER_5_DIGITAL
        
        # Tier 3: Documents (legal/financial)
        document_indicators = ['will', 'trust', 'insurance', 'policy', 'account', 'certificate', 'deed', 'contract']
        if any(indicator in title_lower for indicator in document_indicators):
            return VisualTier.TIER_3_DOCUMENT
        
        # Default: Tier 2 section pages
        return VisualTier.TIER_2_SECTION
    
    def determine_section_type(self, title: str, category: str) -> SectionType:
        """Determine the section type for aesthetic consistency"""
        title_lower = title.lower()
        category_lower = category.lower()
        
        # Admin section
        admin_indicators = ['admin', 'builder', 'setup', 'config', 'rollout', 'diagnostic']
        if any(indicator in title_lower or indicator in category_lower for indicator in admin_indicators):
            return SectionType.ADMIN
        
        # Executor section
        executor_indicators = ['executor', 'estate', 'legal', 'probate', 'will', 'trust']
        if any(indicator in title_lower or indicator in category_lower for indicator in executor_indicators):
            return SectionType.EXECUTOR
        
        # Family section
        family_indicators = ['family', 'spouse', 'children', 'beneficiary', 'heir', 'message', 'keepsake']
        if any(indicator in title_lower or indicator in category_lower for indicator in family_indicators):
            return SectionType.FAMILY
        
        # Financial section
        financial_indicators = ['financial', 'bank', 'account', 'insurance', 'investment', 'asset']
        if any(indicator in title_lower or indicator in category_lower for indicator in financial_indicators):
            return SectionType.FINANCIAL
        
        # Property section
        property_indicators = ['property', 'real estate', 'home', 'land', 'building', 'vehicle']
        if any(indicator in title_lower or indicator in category_lower for indicator in property_indicators):
            return SectionType.PROPERTY
        
        # Digital section
        digital_indicators = ['digital', 'online', 'google', 'apple', 'facebook', 'cloud', 'social']
        if any(indicator in title_lower or indicator in category_lower for indicator in digital_indicators):
            return SectionType.DIGITAL
        
        # Letters section
        if 'letter' in title_lower or 'letter' in category_lower:
            return SectionType.LETTERS
        
        # Default to family for warmth
        return SectionType.FAMILY
    
    def generate_tier_specific_elements(self, 
                                      visual_tier: VisualTier, 
                                      section_type: SectionType) -> Dict[str, Any]:
        """Generate tier-specific visual elements"""
        
        tier_profile = self.tier_profiles[visual_tier]
        section_aesthetic = self.section_aesthetics[section_type]
        hierarchy_rule = self.hierarchy_rules[visual_tier]
        
        elements = {
            # Complexity specifications
            "layer_count": tier_profile.layer_count,
            "detail_density": tier_profile.detail_density,
            "metallic_intensity": tier_profile.metallic_intensity,
            "texture_layers": tier_profile.texture_layers,
            "focal_elements": tier_profile.focal_elements,
            "lighting_complexity": tier_profile.lighting_complexity,
            
            # Section aesthetic elements
            "color_palette": section_aesthetic.color_palette,
            "primary_materials": section_aesthetic.primary_materials,
            "lighting_style": section_aesthetic.lighting_style,
            "architectural_elements": section_aesthetic.architectural_elements,
            "emotional_tone": section_aesthetic.emotional_tone,
            
            # Tier-specific requirements
            "inheritance_rules": hierarchy_rule.inheritance_rules,
            "differentiation_requirements": hierarchy_rule.differentiation_requirements
        }
        
        # Add hub signatures for hub-tier pages
        if visual_tier == VisualTier.TIER_1_HUB and section_type in self.hub_signatures:
            elements["hub_signatures"] = self.hub_signatures[section_type]
        
        return elements
    
    def create_hierarchical_prompt_elements(self, 
                                          title: str, 
                                          category: str, 
                                          asset_type: str) -> Dict[str, Any]:
        """Create complete hierarchical prompt elements for a page"""
        
        # Determine tier and section
        visual_tier = self.determine_visual_tier(title, category, asset_type)
        section_type = self.determine_section_type(title, category)
        
        # Generate tier-specific elements
        tier_elements = self.generate_tier_specific_elements(visual_tier, section_type)
        
        # Build hierarchical description
        tier_descriptions = {
            VisualTier.TIER_1_HUB: f"Ultra-luxury command center establishing the visual DNA for {section_type.value} section",
            VisualTier.TIER_2_SECTION: f"Premium functional interface inheriting {section_type.value} hub aesthetics with unique overlay",
            VisualTier.TIER_3_DOCUMENT: f"Professional trustworthy document with security elements and {section_type.value} undertones",
            VisualTier.TIER_4_LETTER: f"Elegant formal correspondence template with {section_type.value} personalization",
            VisualTier.TIER_5_DIGITAL: f"Hybrid luxury-tech interface blending {section_type.value} tradition with modern technology"
        }
        
        # Create visual consistency markers
        consistency_markers = []
        if visual_tier != VisualTier.TIER_1_HUB:
            # Non-hub pages should reference section DNA
            consistency_markers.append(f"maintaining {section_type.value} section visual DNA")
        
        if visual_tier == VisualTier.TIER_2_SECTION:
            consistency_markers.append("inheriting hub's base aesthetic with functional differentiation")
        
        return {
            "visual_tier": visual_tier.value,
            "section_type": section_type.value,
            "tier_description": tier_descriptions[visual_tier],
            "consistency_markers": consistency_markers,
            "tier_elements": tier_elements,
            "hierarchy_level": f"Tier {visual_tier.value.split('_')[1]} of 5"
        }
    
    def validate_visual_consistency(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate visual consistency across all pages"""
        
        validation_results = {
            "hub_pages": [],
            "section_consistency": {},
            "tier_distribution": {},
            "potential_conflicts": [],
            "recommendations": []
        }
        
        # Analyze each page
        for page in pages:
            hierarchy_info = self.create_hierarchical_prompt_elements(
                page.get('title', ''),
                page.get('category', ''),
                page.get('asset_type', 'icon')
            )
            
            page['hierarchy_info'] = hierarchy_info
            
            # Track hub pages
            if hierarchy_info['visual_tier'] == 'tier_1_hub':
                validation_results['hub_pages'].append(page)
            
            # Track section consistency
            section = hierarchy_info['section_type']
            if section not in validation_results['section_consistency']:
                validation_results['section_consistency'][section] = []
            validation_results['section_consistency'][section].append(page)
            
            # Track tier distribution
            tier = hierarchy_info['visual_tier']
            if tier not in validation_results['tier_distribution']:
                validation_results['tier_distribution'][tier] = 0
            validation_results['tier_distribution'][tier] += 1
        
        # Validate each section has a hub
        for section, section_pages in validation_results['section_consistency'].items():
            hub_count = sum(1 for p in section_pages if p['hierarchy_info']['visual_tier'] == 'tier_1_hub')
            if hub_count == 0:
                validation_results['potential_conflicts'].append(
                    f"Section '{section}' has no hub page to establish visual DNA"
                )
                validation_results['recommendations'].append(
                    f"Consider designating a primary page in '{section}' section as a hub"
                )
            elif hub_count > 1:
                validation_results['potential_conflicts'].append(
                    f"Section '{section}' has {hub_count} hub pages - may create visual confusion"
                )
        
        return validation_results
    
    def save_hierarchy_definitions(self, output_file: str = "visual_hierarchy.json"):
        """Save visual hierarchy definitions to file"""
        
        # Convert enums to strings for serialization
        data = {
            'tier_profiles': {
                tier.value: {
                    'layer_count': profile.layer_count,
                    'detail_density': profile.detail_density,
                    'metallic_intensity': profile.metallic_intensity,
                    'texture_layers': profile.texture_layers,
                    'focal_elements': profile.focal_elements,
                    'lighting_complexity': profile.lighting_complexity
                }
                for tier, profile in self.tier_profiles.items()
            },
            'section_aesthetics': {
                section.value: {
                    'name': aesthetic.name,
                    'theme_description': aesthetic.theme_description,
                    'color_palette': aesthetic.color_palette,
                    'primary_materials': aesthetic.primary_materials,
                    'secondary_materials': aesthetic.secondary_materials,
                    'lighting_style': aesthetic.lighting_style,
                    'architectural_elements': aesthetic.architectural_elements,
                    'emotional_tone': aesthetic.emotional_tone,
                    'luxury_markers': aesthetic.luxury_markers
                }
                for section, aesthetic in self.section_aesthetics.items()
            },
            'hub_signatures': {
                section.value: signatures
                for section, signatures in self.hub_signatures.items()
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_file


def test_visual_hierarchy():
    """Test the visual hierarchy system"""
    manager = VisualHierarchyManager()
    
    print("VISUAL HIERARCHY SYSTEM TEST")
    print("=" * 80)
    
    # Test pages representing different scenarios
    test_pages = [
        {'title': 'Executor Hub', 'category': 'executor', 'asset_type': 'icon'},
        {'title': 'Family Hub', 'category': 'family', 'asset_type': 'cover'},
        {'title': 'Bank Account Access', 'category': 'executor', 'asset_type': 'icon'},
        {'title': 'Messages for Family', 'category': 'family', 'asset_type': 'cover'},
        {'title': 'Last Will and Testament', 'category': 'financial', 'asset_type': 'icon'},
        {'title': 'Letter to Spouse', 'category': 'letters', 'asset_type': 'letter_header'},
        {'title': 'Google Account Recovery', 'category': 'digital', 'asset_type': 'icon'},
        {'title': 'Admin Rollout Setup', 'category': 'admin', 'asset_type': 'icon'}
    ]
    
    for page in test_pages:
        print(f"\n{page['title']}:")
        print("-" * 40)
        
        # Get hierarchy elements
        hierarchy = manager.create_hierarchical_prompt_elements(
            page['title'], page['category'], page['asset_type']
        )
        
        print(f"Visual Tier: {hierarchy['visual_tier']}")
        print(f"Section Type: {hierarchy['section_type']}")
        print(f"Description: {hierarchy['tier_description'][:80]}...")
        
        tier_elements = hierarchy['tier_elements']
        print(f"Layers: {tier_elements['layer_count']}, Focal Points: {tier_elements['focal_elements']}")
        print(f"Colors: {', '.join(tier_elements['color_palette'][:2])}...")
    
    # Test validation
    print(f"\n{'VALIDATION RESULTS':=^80}")
    validation = manager.validate_visual_consistency(test_pages)
    
    print(f"Hub Pages Found: {len(validation['hub_pages'])}")
    for hub in validation['hub_pages']:
        print(f"  • {hub['title']} ({hub['hierarchy_info']['section_type']})")
    
    print(f"\nTier Distribution:")
    for tier, count in validation['tier_distribution'].items():
        print(f"  • {tier}: {count} pages")
    
    if validation['potential_conflicts']:
        print(f"\nPotential Issues:")
        for issue in validation['potential_conflicts']:
            print(f"  ⚠️ {issue}")
    
    if validation['recommendations']:
        print(f"\nRecommendations:")
        for rec in validation['recommendations']:
            print(f"  💡 {rec}")
    
    # Save definitions
    output = manager.save_hierarchy_definitions()
    print(f"\nHierarchy definitions saved to: {output}")


if __name__ == "__main__":
    test_visual_hierarchy()