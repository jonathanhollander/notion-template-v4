#!/usr/bin/env python3
"""
Emotional Elements System for Estate Planning Visual Design
Manages emotional intelligence components for compassionate luxury design
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
from pathlib import Path
import json

class LifeStage(Enum):
    """Life stages for contextual emotional design"""
    YOUNG_FAMILY = "young_family"
    ESTABLISHED_FAMILY = "established_family"
    EMPTY_NESTERS = "empty_nesters"
    RETIREMENT = "retirement"
    ELDERLY = "elderly"

class EmotionalContext(Enum):
    """Emotional contexts for different planning scenarios"""
    PROACTIVE_PLANNING = "proactive_planning"  # Healthy, forward-thinking
    HEALTH_CONCERN = "health_concern"  # Medical diagnosis, urgency
    FAMILY_CRISIS = "family_crisis"  # Relationship issues, conflicts
    LOSS_PROCESSING = "loss_processing"  # Recent death, grief
    CELEBRATION = "celebration"  # New baby, marriage, achievement

class ComfortLevel(Enum):
    """User comfort levels with estate planning"""
    ANXIOUS = "anxious"  # First time, overwhelmed
    CAUTIOUS = "cautious"  # Some experience, careful
    CONFIDENT = "confident"  # Experienced, decisive
    EXPERT = "expert"  # Professional level knowledge

@dataclass
class EmotionalMarker:
    """Individual emotional design element"""
    element: str
    emotional_weight: float  # 0.0 to 1.0 intensity
    comfort_factor: float  # How comforting this element is
    universality: float  # How universally understood/appreciated
    description: str
    placement_hints: List[str] = field(default_factory=list)

@dataclass
class ContextualEmotions:
    """Emotional elements for specific contexts"""
    comfort_symbols: List[EmotionalMarker] = field(default_factory=list)
    human_touches: List[EmotionalMarker] = field(default_factory=list)
    continuity_metaphors: List[EmotionalMarker] = field(default_factory=list)
    warmth_markers: List[EmotionalMarker] = field(default_factory=list)
    life_elements: List[EmotionalMarker] = field(default_factory=list)
    protection_symbols: List[EmotionalMarker] = field(default_factory=list)

class EmotionalElementsManager:
    """Manages emotional intelligence in visual design"""
    
    def __init__(self):
        """Initialize with comprehensive emotional element database"""
        self.comfort_symbols = self._initialize_comfort_symbols()
        self.human_touches = self._initialize_human_touches()
        self.continuity_metaphors = self._initialize_continuity_metaphors()
        self.warmth_markers = self._initialize_warmth_markers()
        self.life_elements = self._initialize_life_elements()
        self.protection_symbols = self._initialize_protection_symbols()
        
        # Context-specific emotional mappings
        self.context_mappings = self._initialize_context_mappings()
        
        # Cultural sensitivity filters
        self.cultural_filters = self._initialize_cultural_filters()
        
    def _initialize_comfort_symbols(self) -> List[EmotionalMarker]:
        """Initialize comfort symbols that provide psychological safety"""
        return [
            EmotionalMarker(
                element="warm tea service on side table",
                emotional_weight=0.7,
                comfort_factor=0.9,
                universality=0.8,
                description="Universal comfort ritual, suggests patience and care",
                placement_hints=["desk corner", "beside seating", "background element"]
            ),
            EmotionalMarker(
                element="soft reading lamp with amber glow",
                emotional_weight=0.6,
                comfort_factor=0.8,
                universality=0.9,
                description="Gentle lighting suggests safety and focus",
                placement_hints=["desk lighting", "background warmth", "focal rim light"]
            ),
            EmotionalMarker(
                element="handknit blanket draped over chair",
                emotional_weight=0.8,
                comfort_factor=0.9,
                universality=0.7,
                description="Handmade items suggest care and human touch",
                placement_hints=["chair back", "reading nook", "family area"]
            ),
            EmotionalMarker(
                element="open book with bookmark ribbon",
                emotional_weight=0.5,
                comfort_factor=0.7,
                universality=0.8,
                description="Suggests ongoing learning and thoughtfulness",
                placement_hints=["desk surface", "side table", "background detail"]
            ),
            EmotionalMarker(
                element="fresh flowers in simple vase",
                emotional_weight=0.6,
                comfort_factor=0.8,
                universality=0.9,
                description="Life and beauty in planning context",
                placement_hints=["windowsill", "desk corner", "reception area"]
            ),
            EmotionalMarker(
                element="tissue box discretely placed",
                emotional_weight=0.9,
                comfort_factor=0.8,
                universality=0.7,
                description="Acknowledges emotional difficulty, shows preparation",
                placement_hints=["side table", "consultation area", "subtle placement"]
            ),
            EmotionalMarker(
                element="comfortable reading glasses nearby",
                emotional_weight=0.4,
                comfort_factor=0.6,
                universality=0.9,
                description="Practical tool suggests accessibility and care",
                placement_hints=["desk surface", "document area", "personal items"]
            ),
            EmotionalMarker(
                element="handwritten note with caring words",
                emotional_weight=0.8,
                comfort_factor=0.9,
                universality=0.8,
                description="Personal touch shows individual attention",
                placement_hints=["document margin", "sticky note", "personal message"]
            )
        ]
    
    def _initialize_human_touches(self) -> List[EmotionalMarker]:
        """Initialize human touches that show personal care"""
        return [
            EmotionalMarker(
                element="family photo in wooden frame",
                emotional_weight=0.9,
                comfort_factor=0.8,
                universality=0.9,
                description="Personal connection and motivation for planning",
                placement_hints=["desk corner", "bookshelf", "personal space"]
            ),
            EmotionalMarker(
                element="coffee ring stain on document edge",
                emotional_weight=0.3,
                comfort_factor=0.6,
                universality=0.7,
                description="Shows documents are worked with, not sterile",
                placement_hints=["paper edges", "work surfaces", "lived-in details"]
            ),
            EmotionalMarker(
                element="well-worn leather journal with ribbon",
                emotional_weight=0.7,
                comfort_factor=0.8,
                universality=0.8,
                description="Personal record-keeping, thoughtful process",
                placement_hints=["desk surface", "planning materials", "personal tools"]
            ),
            EmotionalMarker(
                element="child's artwork pinned to bulletin board",
                emotional_weight=0.8,
                comfort_factor=0.7,
                universality=0.8,
                description="Family motivation, future generations",
                placement_hints=["background wall", "family area", "motivation reminder"]
            ),
            EmotionalMarker(
                element="handwritten margin notes in documents",
                emotional_weight=0.6,
                comfort_factor=0.7,
                universality=0.8,
                description="Active engagement with planning process",
                placement_hints=["document margins", "planning notes", "personal annotations"]
            ),
            EmotionalMarker(
                element="personal pen with engraved initials",
                emotional_weight=0.5,
                comfort_factor=0.6,
                universality=0.7,
                description="Personal tools show individual touch",
                placement_hints=["document signing", "desk surface", "writing implements"]
            ),
            EmotionalMarker(
                element="wedding ring beside documents",
                emotional_weight=0.9,
                comfort_factor=0.7,
                universality=0.9,
                description="Symbol of commitment and love",
                placement_hints=["document area", "personal items", "commitment reminder"]
            ),
            EmotionalMarker(
                element="travel souvenir used as paperweight",
                emotional_weight=0.6,
                comfort_factor=0.8,
                universality=0.6,
                description="Life experiences and memories",
                placement_hints=["desk organizer", "memory keeper", "life celebration"]
            )
        ]
    
    def _initialize_continuity_metaphors(self) -> List[EmotionalMarker]:
        """Initialize metaphors that suggest continuity and legacy"""
        return [
            EmotionalMarker(
                element="oak tree with visible roots and branches",
                emotional_weight=0.9,
                comfort_factor=0.8,
                universality=0.9,
                description="Generational strength and growth",
                placement_hints=["window view", "artwork", "metaphorical element"]
            ),
            EmotionalMarker(
                element="river flowing toward horizon",
                emotional_weight=0.8,
                comfort_factor=0.8,
                universality=0.8,
                description="Life's journey continuing forward",
                placement_hints=["landscape view", "artwork", "background metaphor"]
            ),
            EmotionalMarker(
                element="lighthouse beam guiding ships",
                emotional_weight=0.7,
                comfort_factor=0.9,
                universality=0.8,
                description="Guidance and protection across time",
                placement_hints=["wall art", "metaphorical guidance", "protection symbol"]
            ),
            EmotionalMarker(
                element="candle flame passing to new candle",
                emotional_weight=0.9,
                comfort_factor=0.8,
                universality=0.9,
                description="Life passing from generation to generation",
                placement_hints=["ceremonial element", "legacy symbol", "gentle metaphor"]
            ),
            EmotionalMarker(
                element="vintage photo album with new photos added",
                emotional_weight=0.8,
                comfort_factor=0.9,
                universality=0.9,
                description="Continuing story, adding to family history",
                placement_hints=["family area", "memory collection", "ongoing story"]
            ),
            EmotionalMarker(
                element="garden with perennial flowers",
                emotional_weight=0.7,
                comfort_factor=0.9,
                universality=0.8,
                description="Life renewing itself each season",
                placement_hints=["window view", "outdoor metaphor", "renewal symbol"]
            ),
            EmotionalMarker(
                element="compass pointing toward future",
                emotional_weight=0.6,
                comfort_factor=0.7,
                universality=0.8,
                description="Direction and guidance for what's ahead",
                placement_hints=["navigation symbol", "planning tool", "direction marker"]
            ),
            EmotionalMarker(
                element="sunrise over familiar landscape",
                emotional_weight=0.8,
                comfort_factor=0.9,
                universality=0.9,
                description="New day, continuing beauty, hope",
                placement_hints=["window view", "hopeful element", "renewal symbol"]
            )
        ]
    
    def _initialize_warmth_markers(self) -> List[EmotionalMarker]:
        """Initialize visual elements that create emotional warmth"""
        return [
            EmotionalMarker(
                element="honey-gold lighting",
                emotional_weight=0.7,
                comfort_factor=0.9,
                universality=0.9,
                description="Warm lighting creates emotional safety",
                placement_hints=["general lighting", "accent lighting", "mood setting"]
            ),
            EmotionalMarker(
                element="amber glass lamp shade",
                emotional_weight=0.6,
                comfort_factor=0.8,
                universality=0.8,
                description="Filtered warm light, cozy atmosphere",
                placement_hints=["desk lamp", "reading light", "ambient lighting"]
            ),
            EmotionalMarker(
                element="burgundy leather chair with patina",
                emotional_weight=0.7,
                comfort_factor=0.8,
                universality=0.7,
                description="Aged materials suggest comfort and reliability",
                placement_hints=["seating area", "consultation space", "comfort zone"]
            ),
            EmotionalMarker(
                element="soft cashmere throw",
                emotional_weight=0.6,
                comfort_factor=0.9,
                universality=0.7,
                description="Luxury comfort, caring attention to comfort",
                placement_hints=["seating area", "comfort element", "luxury touch"]
            ),
            EmotionalMarker(
                element="fireplace with gentle flame",
                emotional_weight=0.8,
                comfort_factor=0.9,
                universality=0.8,
                description="Primal comfort, gathering place, warmth",
                placement_hints=["room centerpiece", "gathering area", "warmth source"]
            ),
            EmotionalMarker(
                element="copper accents with warm patina",
                emotional_weight=0.5,
                comfort_factor=0.7,
                universality=0.6,
                description="Warm metals suggest quality and age",
                placement_hints=["hardware", "accent details", "metallic warmth"]
            ),
            EmotionalMarker(
                element="sunset colors reflected in surfaces",
                emotional_weight=0.7,
                comfort_factor=0.8,
                universality=0.9,
                description="Natural warm colors, end-of-day peace",
                placement_hints=["color palette", "reflective surfaces", "ambient color"]
            ),
            EmotionalMarker(
                element="wood grain with visible character",
                emotional_weight=0.6,
                comfort_factor=0.8,
                universality=0.8,
                description="Natural materials with life history",
                placement_hints=["furniture", "surfaces", "natural elements"]
            )
        ]
    
    def _initialize_life_elements(self) -> List[EmotionalMarker]:
        """Initialize elements that celebrate ongoing life"""
        return [
            EmotionalMarker(
                element="birthday calendar with family dates",
                emotional_weight=0.7,
                comfort_factor=0.8,
                universality=0.9,
                description="Celebrating ongoing life and milestones",
                placement_hints=["wall calendar", "planning area", "family celebrations"]
            ),
            EmotionalMarker(
                element="growth chart marks on doorframe",
                emotional_weight=0.8,
                comfort_factor=0.7,
                universality=0.8,
                description="Children growing, life progressing",
                placement_hints=["doorway", "family area", "growth tracking"]
            ),
            EmotionalMarker(
                element="fresh bread cooling on kitchen counter",
                emotional_weight=0.6,
                comfort_factor=0.9,
                universality=0.8,
                description="Daily life continuing, nourishment, care",
                placement_hints=["kitchen area", "daily life", "nourishment symbol"]
            ),
            EmotionalMarker(
                element="homework papers on desk",
                emotional_weight=0.5,
                comfort_factor=0.6,
                universality=0.8,
                description="Education continuing, future preparation",
                placement_hints=["study area", "family life", "education focus"]
            ),
            EmotionalMarker(
                element="garden tools with soil still on them",
                emotional_weight=0.6,
                comfort_factor=0.7,
                universality=0.7,
                description="Active gardening, nurturing growth",
                placement_hints=["garden area", "growing metaphor", "nurturing activity"]
            ),
            EmotionalMarker(
                element="half-finished puzzle on table",
                emotional_weight=0.5,
                comfort_factor=0.8,
                universality=0.8,
                description="Ongoing projects, patience, family time",
                placement_hints=["family area", "activity table", "ongoing projects"]
            ),
            EmotionalMarker(
                element="pet sleeping peacefully nearby",
                emotional_weight=0.7,
                comfort_factor=0.9,
                universality=0.8,
                description="Companionship, peaceful presence, family",
                placement_hints=["comfort area", "peaceful element", "family member"]
            ),
            EmotionalMarker(
                element="seasonal decorations subtly placed",
                emotional_weight=0.4,
                comfort_factor=0.7,
                universality=0.7,
                description="Life cycles, celebration, ongoing traditions",
                placement_hints=["background details", "seasonal touches", "tradition markers"]
            )
        ]
    
    def _initialize_protection_symbols(self) -> List[EmotionalMarker]:
        """Initialize symbols that suggest protection and security"""
        return [
            EmotionalMarker(
                element="umbrella standing ready by door",
                emotional_weight=0.6,
                comfort_factor=0.8,
                universality=0.9,
                description="Protection from life's storms, preparedness",
                placement_hints=["entryway", "protection symbol", "preparedness"]
            ),
            EmotionalMarker(
                element="safe harbor artwork on wall",
                emotional_weight=0.7,
                comfort_factor=0.8,
                universality=0.8,
                description="Safety, refuge, protection metaphor",
                placement_hints=["wall art", "protection theme", "safety symbol"]
            ),
            EmotionalMarker(
                element="strong foundation visible in architecture",
                emotional_weight=0.8,
                comfort_factor=0.9,
                universality=0.8,
                description="Solid base, reliability, strength",
                placement_hints=["architectural element", "foundation metaphor", "strength"]
            ),
            EmotionalMarker(
                element="watchful guardian statue in garden",
                emotional_weight=0.7,
                comfort_factor=0.7,
                universality=0.6,
                description="Protective presence, watching over family",
                placement_hints=["garden element", "protective figure", "guardian symbol"]
            ),
            EmotionalMarker(
                element="nest with eggs in tree branch",
                emotional_weight=0.8,
                comfort_factor=0.8,
                universality=0.9,
                description="Protection of future generations, nurturing",
                placement_hints=["nature element", "protection metaphor", "future care"]
            ),
            EmotionalMarker(
                element="lighthouse in distance",
                emotional_weight=0.7,
                comfort_factor=0.8,
                universality=0.8,
                description="Guidance through difficult times, beacon",
                placement_hints=["distant view", "guidance symbol", "beacon of hope"]
            ),
            EmotionalMarker(
                element="security system panel (discrete)",
                emotional_weight=0.5,
                comfort_factor=0.7,
                universality=0.7,
                description="Modern protection, practical security",
                placement_hints=["background element", "modern security", "practical protection"]
            ),
            EmotionalMarker(
                element="insurance documents in protective sleeve",
                emotional_weight=0.6,
                comfort_factor=0.8,
                universality=0.8,
                description="Protection through planning, care for documents",
                placement_hints=["document area", "protection through planning", "careful organization"]
            )
        ]
    
    def _initialize_context_mappings(self) -> Dict[EmotionalContext, ContextualEmotions]:
        """Map emotional contexts to appropriate elements"""
        return {
            EmotionalContext.PROACTIVE_PLANNING: ContextualEmotions(
                comfort_symbols=self.comfort_symbols[:3],  # Less intense comfort needed
                human_touches=self.human_touches[:4],
                continuity_metaphors=self.continuity_metaphors[:3],
                warmth_markers=self.warmth_markers[:3],
                life_elements=self.life_elements[:4],  # Emphasize ongoing life
                protection_symbols=self.protection_symbols[:2]
            ),
            EmotionalContext.HEALTH_CONCERN: ContextualEmotions(
                comfort_symbols=self.comfort_symbols[:5],  # More comfort needed
                human_touches=self.human_touches[:3],
                continuity_metaphors=self.continuity_metaphors[3:6],  # Focus on legacy
                warmth_markers=self.warmth_markers[:4],
                life_elements=self.life_elements[2:5],  # Gentler life elements
                protection_symbols=self.protection_symbols[:4]  # Emphasis on protection
            ),
            EmotionalContext.FAMILY_CRISIS: ContextualEmotions(
                comfort_symbols=self.comfort_symbols[1:4],
                human_touches=self.human_touches[2:5],
                continuity_metaphors=self.continuity_metaphors[:4],  # Healing and connection
                warmth_markers=self.warmth_markers[:5],  # Extra warmth needed
                life_elements=self.life_elements[1:4],
                protection_symbols=self.protection_symbols[2:5]
            ),
            EmotionalContext.LOSS_PROCESSING: ContextualEmotions(
                comfort_symbols=self.comfort_symbols[:6],  # Maximum comfort
                human_touches=self.human_touches[1:5],  # Memory focus
                continuity_metaphors=self.continuity_metaphors[2:7],  # Strong continuity theme
                warmth_markers=self.warmth_markers[:6],  # Maximum warmth
                life_elements=self.life_elements[:3],  # Gentle life elements
                protection_symbols=self.protection_symbols[1:4]
            ),
            EmotionalContext.CELEBRATION: ContextualEmotions(
                comfort_symbols=self.comfort_symbols[2:5],  # Moderate comfort
                human_touches=self.human_touches[:5],  # Personal celebration
                continuity_metaphors=self.continuity_metaphors[:4],  # Future focus
                warmth_markers=self.warmth_markers[1:5],
                life_elements=self.life_elements[:6],  # Celebrate life
                protection_symbols=self.protection_symbols[:3]
            )
        }
    
    def _initialize_cultural_filters(self) -> Dict[str, List[str]]:
        """Initialize cultural sensitivity filters"""
        return {
            'universal_safe': [
                'natural elements', 'family photos', 'books', 'tea/coffee',
                'flowers', 'warm lighting', 'comfortable furniture',
                'handwritten notes', 'reading glasses'
            ],
            'avoid_assumptions': [
                'specific religious symbols', 'gender role assumptions',
                'family structure assumptions', 'cultural celebrations',
                'specific foods', 'particular traditions'
            ],
            'inclusive_elements': [
                'diverse family configurations', 'various ages together',
                'different ability levels', 'multiple generations',
                'various cultural backgrounds subtly included'
            ]
        }
    
    def get_contextual_elements(self, 
                              emotional_context: EmotionalContext,
                              comfort_level: ComfortLevel,
                              num_elements: int = 3) -> Dict[str, List[str]]:
        """Get appropriate emotional elements for context"""
        
        context_emotions = self.context_mappings[emotional_context]
        
        # Adjust element selection based on comfort level
        intensity_multiplier = {
            ComfortLevel.ANXIOUS: 1.2,  # More comfort elements
            ComfortLevel.CAUTIOUS: 1.0,  # Standard elements
            ComfortLevel.CONFIDENT: 0.8,  # Fewer comfort elements
            ComfortLevel.EXPERT: 0.6  # Minimal emotional elements
        }
        
        multiplier = intensity_multiplier[comfort_level]
        adjusted_num = max(1, int(num_elements * multiplier))
        
        # Select elements with highest comfort factors
        selected_elements = {
            'comfort_symbols': [
                elem.element for elem in 
                sorted(context_emotions.comfort_symbols, 
                      key=lambda x: x.comfort_factor, reverse=True)[:adjusted_num]
            ],
            'human_touches': [
                elem.element for elem in
                sorted(context_emotions.human_touches,
                      key=lambda x: x.comfort_factor, reverse=True)[:adjusted_num]
            ],
            'continuity_metaphors': [
                elem.element for elem in
                sorted(context_emotions.continuity_metaphors,
                      key=lambda x: x.emotional_weight, reverse=True)[:adjusted_num]
            ],
            'warmth_markers': [
                elem.element for elem in
                sorted(context_emotions.warmth_markers,
                      key=lambda x: x.comfort_factor, reverse=True)[:adjusted_num]
            ],
            'life_elements': [
                elem.element for elem in
                sorted(context_emotions.life_elements,
                      key=lambda x: x.universality, reverse=True)[:adjusted_num]
            ],
            'protection_symbols': [
                elem.element for elem in
                sorted(context_emotions.protection_symbols,
                      key=lambda x: (x.comfort_factor + x.universality)/2, reverse=True)[:adjusted_num]
            ]
        }
        
        return selected_elements
    
    def generate_emotional_prompt_additions(self,
                                          base_prompt: str,
                                          emotional_context: EmotionalContext = EmotionalContext.PROACTIVE_PLANNING,
                                          comfort_level: ComfortLevel = ComfortLevel.CAUTIOUS,
                                          emphasis: str = "balanced") -> str:
        """Add emotional elements to base prompt"""
        
        elements = self.get_contextual_elements(emotional_context, comfort_level, num_elements=2)
        
        # Choose elements based on emphasis
        if emphasis == "warmth":
            additions = elements['warmth_markers'] + elements['comfort_symbols']
        elif emphasis == "continuity":
            additions = elements['continuity_metaphors'] + elements['life_elements']
        elif emphasis == "protection":
            additions = elements['protection_symbols'] + elements['comfort_symbols']
        elif emphasis == "human":
            additions = elements['human_touches'] + elements['life_elements']
        else:  # balanced
            additions = (
                elements['comfort_symbols'][:1] +
                elements['human_touches'][:1] +
                elements['warmth_markers'][:1]
            )
        
        # Filter out empty selections
        additions = [add for add in additions if add.strip()]
        
        if additions:
            emotional_addition = f", featuring {', '.join(additions)} for emotional warmth and human connection"
            return base_prompt + emotional_addition
        
        return base_prompt
    
    def save_emotional_library(self, output_file: str = "emotional_elements.json"):
        """Save emotional element library to file"""
        def serialize_marker(marker: EmotionalMarker) -> Dict[str, Any]:
            return {
                'element': marker.element,
                'emotional_weight': marker.emotional_weight,
                'comfort_factor': marker.comfort_factor,
                'universality': marker.universality,
                'description': marker.description,
                'placement_hints': marker.placement_hints
            }
        
        data = {
            'comfort_symbols': [serialize_marker(m) for m in self.comfort_symbols],
            'human_touches': [serialize_marker(m) for m in self.human_touches],
            'continuity_metaphors': [serialize_marker(m) for m in self.continuity_metaphors],
            'warmth_markers': [serialize_marker(m) for m in self.warmth_markers],
            'life_elements': [serialize_marker(m) for m in self.life_elements],
            'protection_symbols': [serialize_marker(m) for m in self.protection_symbols],
            'cultural_filters': self.cultural_filters
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return output_file


def test_emotional_elements():
    """Test the emotional elements system"""
    manager = EmotionalElementsManager()
    
    print("EMOTIONAL ELEMENTS SYSTEM TEST")
    print("=" * 80)
    
    # Test different contexts
    test_contexts = [
        (EmotionalContext.PROACTIVE_PLANNING, ComfortLevel.CONFIDENT),
        (EmotionalContext.HEALTH_CONCERN, ComfortLevel.ANXIOUS),
        (EmotionalContext.LOSS_PROCESSING, ComfortLevel.CAUTIOUS),
        (EmotionalContext.CELEBRATION, ComfortLevel.CONFIDENT)
    ]
    
    for context, comfort in test_contexts:
        print(f"\nContext: {context.value}, Comfort Level: {comfort.value}")
        print("-" * 60)
        
        elements = manager.get_contextual_elements(context, comfort, num_elements=3)
        
        for category, items in elements.items():
            if items:
                print(f"{category}: {', '.join(items[:2])}")
        
        # Test prompt enhancement
        base_prompt = "Ultra-luxury icon for Estate Planning Dashboard: mahogany desk with legal documents"
        enhanced = manager.generate_emotional_prompt_additions(
            base_prompt, context, comfort, emphasis="warmth"
        )
        print(f"\nEnhanced prompt: {enhanced[:100]}...")
    
    # Save library
    output = manager.save_emotional_library()
    print(f"\nEmotional library saved to: {output}")


if __name__ == "__main__":
    test_emotional_elements()