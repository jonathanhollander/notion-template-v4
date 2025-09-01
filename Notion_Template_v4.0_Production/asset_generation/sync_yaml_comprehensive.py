#!/usr/bin/env python3
"""
Comprehensive YAML synchronization module for asset generation.
Dynamically discovers ALL pages from YAML files with ultra-premium prompt generation.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Set
import logging
from datetime import datetime

# Import our enhanced prompt generation system
from prompt_templates import PromptTemplateManager, PageTier, AssetType
from visual_hierarchy import VisualHierarchyManager, VisualTier
from emotional_elements import EmotionalElementsManager, EmotionalContext, ComfortLevel

class YAMLSyncComprehensive:
    """Dynamic YAML page discovery for ultra-premium asset generation"""
    
    def __init__(self, yaml_dir: str = "../split_yaml"):
        self.yaml_dir = Path(yaml_dir)
        self.logger = logging.getLogger('YAMLSync')
        
        # Initialize enhanced prompt generation system
        self.prompt_manager = PromptTemplateManager()
        self.hierarchy_manager = VisualHierarchyManager()
        self.emotional_manager = EmotionalElementsManager()
        
        self.logger.info("Initialized ultra-premium prompt generation system")
    
    def discover_pages(self) -> List[Dict]:
        """Public interface to discover all pages from YAML files"""
        return self._discover_all_pages()
        
    def sync_with_yaml(self) -> Dict[str, List[Dict]]:
        """Comprehensively discover ALL pages from YAML files"""
        
        # First collect all unique pages
        all_pages = self._discover_all_pages()
        
        # Now organize them into asset categories
        pages_by_type = {
            'icons': [],
            'covers': [],
            'textures': [],
            'letter_headers': [],
            'database_icons': []
        }
        
        # Process each discovered page with enhanced prompt generation
        for page_info in all_pages:
            title = page_info['title']
            category = page_info.get('category', 'general')
            page_type = page_info.get('type', 'page')
            
            # Generate appropriate slug
            slug = title.lower().replace(' ', '-').replace('–', '-')
            slug = ''.join(c for c in slug if c.isalnum() or c == '-')
            
            # Determine visual tier and emotional context
            visual_tier = self.hierarchy_manager.determine_visual_tier(title, category, 'icon')
            emotional_context = self._determine_emotional_context(title, category)
            
            # All pages need icons and covers with enhanced prompts
            if page_type != 'letter':  # Letters don't need icons
                enhanced_icon_prompt = self._generate_enhanced_icon_prompt(title, category, page_type, visual_tier, emotional_context)
                pages_by_type['icons'].append({
                    'title': title,
                    'slug': slug,
                    'category': category,
                    'visual_tier': visual_tier.value,
                    'emotional_context': emotional_context.value,
                    'prompt': enhanced_icon_prompt
                })
            
            if page_type != 'letter':  # Regular pages need covers
                enhanced_cover_prompt = self._generate_enhanced_cover_prompt(title, category, page_type, visual_tier, emotional_context)
                pages_by_type['covers'].append({
                    'title': title,
                    'slug': slug, 
                    'category': category,
                    'visual_tier': visual_tier.value,
                    'emotional_context': emotional_context.value,
                    'prompt': enhanced_cover_prompt
                })
            elif page_type == 'letter':  # Letters need enhanced headers
                enhanced_header_prompt = self._generate_enhanced_letter_header_prompt(title, emotional_context)
                pages_by_type['letter_headers'].append({
                    'title': title,
                    'slug': slug,
                    'emotional_context': emotional_context.value,
                    'prompt': enhanced_header_prompt
                })
        
        # Add enhanced standard textures and database icons
        pages_by_type['textures'] = self._get_enhanced_textures()
        pages_by_type['database_icons'] = self._get_enhanced_database_icons()
        
        # Log enhanced summary with luxury metrics
        total_assets = sum(len(v) for v in pages_by_type.values())
        self.logger.info(f"\n🏆 ULTRA-PREMIUM ASSET DISCOVERY COMPLETE 🏆")
        self.logger.info(f"Discovered {len(all_pages)} unique pages with luxury enhancements")
        self.logger.info(f"  Icons: {len(pages_by_type['icons'])} (with emotional intelligence)")
        self.logger.info(f"  Covers: {len(pages_by_type['covers'])} (with 5-tier hierarchy)")
        self.logger.info(f"  Letter headers: {len(pages_by_type['letter_headers'])} (with premium aesthetics)")
        self.logger.info(f"  Database icons: {len(pages_by_type['database_icons'])} (with enhanced styling)")
        self.logger.info(f"  Textures: {len(pages_by_type['textures'])} (with luxury materials)")
        self.logger.info(f"\n📊 Total ultra-premium assets: {total_assets}")
        self.logger.info(f"💎 All prompts enhanced with emotional intelligence & luxury aesthetics")
        
        # Log tier distribution
        tier_counts = {}
        for asset_list in [pages_by_type['icons'], pages_by_type['covers']]:
            for asset in asset_list:
                tier = asset.get('visual_tier', 'unknown')
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        if tier_counts:
            self.logger.info(f"\n🎯 Visual Tier Distribution:")
            for tier, count in sorted(tier_counts.items()):
                self.logger.info(f"  {tier}: {count} assets")
        
        return pages_by_type
    
    def _discover_all_pages(self) -> List[Dict]:
        """Discover all unique pages from YAML files"""
        all_pages = []
        seen_titles = set()
        
        yaml_files = sorted(self.yaml_dir.glob("*.yaml"))
        expected_count = len(yaml_files)
        processed_count = 0
        failed_files = []
        
        self.logger.info(f"Found {expected_count} YAML files to process")
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Try structured parsing first
                try:
                    data = yaml.safe_load(content)
                    if data:
                        self._extract_from_structure(data, all_pages, seen_titles)
                        processed_count += 1
                except yaml.YAMLError:
                    # Fall back to line parsing
                    self._extract_from_lines(content, all_pages, seen_titles)
                    processed_count += 1
                    self.logger.warning(f"Used fallback parsing for {yaml_file.name}")
                    
            except Exception as e:
                self.logger.error(f"Failed to process {yaml_file.name}: {e}")
                failed_files.append(yaml_file.name)
        
        # Validation
        if failed_files:
            self.logger.error(f"Failed to process {len(failed_files)} files: {failed_files}")
            error_msg = f"Failed to process all YAML files. {len(failed_files)} failed out of {expected_count}:\n"
            for file in failed_files:
                error_msg += f"  - {file}\n"
            raise ValueError(error_msg)
        
        if processed_count != expected_count:
            error_msg = f"YAML file count mismatch! Expected {expected_count}, processed {processed_count}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        self.logger.info(f"✓ Successfully processed all {processed_count}/{expected_count} YAML files")
        
        return all_pages
    
    def _extract_from_structure(self, data: dict, all_pages: list, seen_titles: set):
        """Extract pages from parsed YAML structure"""
        if not isinstance(data, dict):
            return
            
        # Core pages
        if 'pages' in data and isinstance(data['pages'], list):
            for page in data['pages']:
                if isinstance(page, dict) and 'title' in page:
                    title = page['title']
                    if title not in seen_titles:
                        seen_titles.add(title)
                        all_pages.append({
                            'title': title,
                            'category': page.get('role', 'general'),
                            'type': 'page'
                        })
        
        # Letters (with capital T)
        if 'letters' in data and isinstance(data['letters'], list):
            for letter in data['letters']:
                if isinstance(letter, dict):
                    title = letter.get('Title') or letter.get('title')
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        all_pages.append({
                            'title': title,
                            'category': 'letters',
                            'type': 'letter'
                        })
        
        # Acceptance rows
        if 'acceptance' in data and isinstance(data['acceptance'], dict):
            if 'rows' in data['acceptance']:
                for row in data['acceptance']['rows']:
                    if isinstance(row, dict) and 'Page' in row:
                        title = row['Page']
                        if title not in seen_titles:
                            seen_titles.add(title)
                            all_pages.append({
                                'title': title,
                                'category': row.get('Section', 'general'),
                                'type': 'page'
                            })
        
        # Admin pages
        if 'admin_page' in data and isinstance(data['admin_page'], dict):
            if 'title' in data['admin_page']:
                title = data['admin_page']['title']
                if title not in seen_titles:
                    seen_titles.add(title)
                    all_pages.append({
                        'title': title,
                        'category': 'admin',
                        'type': 'page'
                    })
    
    def _extract_from_lines(self, content: str, all_pages: list, seen_titles: set):
        """Extract pages by parsing lines when YAML parsing fails"""
        lines = content.split('\n')
        
        for line in lines:
            # Skip comments
            if line.strip().startswith('#'):
                continue
                
            # Core pages
            if line.strip().startswith('- title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_pages.append({
                        'title': title,
                        'category': 'general',
                        'type': 'page'
                    })
            
            # Letters
            elif line.strip().startswith('- Title:'):
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_pages.append({
                        'title': title,
                        'category': 'letters',
                        'type': 'letter'
                    })
            
            # Acceptance pages
            elif 'Page:' in line and not line.strip().startswith('#'):
                parts = line.split('Page:', 1)
                if len(parts) > 1:
                    title = parts[1].strip().strip('"').strip("'")
                    if title and title != 'Page' and title not in seen_titles:
                        seen_titles.add(title)
                        all_pages.append({
                            'title': title,
                            'category': 'general',
                            'type': 'page'
                        })
            
            # Database pages
            elif (line.startswith('  title:') or line.startswith('    title:')) and '{}' not in line:
                title = line.split(':', 1)[1].strip().strip('"').strip("'")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_pages.append({
                        'title': title,
                        'category': 'database',
                        'type': 'page'
                    })
    
    def _determine_emotional_context(self, title: str, category: str) -> EmotionalContext:
        """Determine appropriate emotional context for estate planning sensitivity"""
        title_lower = title.lower()
        category_lower = category.lower()
        
        # High sensitivity contexts
        if any(word in title_lower for word in ['death', 'funeral', 'memorial', 'obituary', 'grief', 'loss']):
            return EmotionalContext.LOSS_PROCESSING
        elif any(word in title_lower for word in ['executor', 'legal', 'will', 'testament', 'probate']):
            return EmotionalContext.PROACTIVE_PLANNING
        elif any(word in title_lower for word in ['family', 'children', 'legacy', 'heritage', 'memory']):
            return EmotionalContext.CELEBRATION
        elif any(word in title_lower for word in ['comfort', 'support', 'guidance', 'help']):
            return EmotionalContext.HEALTH_CONCERN
        elif any(word in title_lower for word in ['celebration', 'life', 'joy', 'gratitude', 'thankful']):
            return EmotionalContext.CELEBRATION
        elif 'admin' in category_lower:
            return EmotionalContext.PROACTIVE_PLANNING
        else:
            return EmotionalContext.PROACTIVE_PLANNING
    
    def _generate_enhanced_icon_prompt(self, title: str, category: str, page_type: str, visual_tier: VisualTier, emotional_context: EmotionalContext) -> str:
        """Generate ultra-premium icon prompt with emotional intelligence"""
        return self.prompt_manager.create_prompt(
            title=title,
            category=category,
            asset_type='icon',
            tier=visual_tier.value,
            custom_elements={
                'emotional_context': emotional_context.value,
                'page_type': page_type,
                'luxury_tier': visual_tier.value
            }
        )
    
    def _generate_enhanced_cover_prompt(self, title: str, category: str, page_type: str, visual_tier: VisualTier, emotional_context: EmotionalContext) -> str:
        """Generate ultra-premium cover prompt with visual hierarchy"""
        return self.prompt_manager.create_prompt(
            title=title,
            category=category,
            asset_type='cover',
            tier=visual_tier.value,
            custom_elements={
                'emotional_context': emotional_context.value,
                'page_type': page_type,
                'visual_tier': visual_tier.value,
                'dimensions': '1500x400px',
                'composition': 'cinematic banner'
            }
        )
    
    def _generate_enhanced_letter_header_prompt(self, title: str, emotional_context: EmotionalContext) -> str:
        """Generate ultra-premium letter header prompt"""
        return self.prompt_manager.create_prompt(
            title=title,
            category='letters',
            asset_type='letter_header',
            custom_elements={
                'emotional_context': emotional_context.value,
                'dimensions': '1920x400px',
                'style': 'formal letterhead'
            }
        )
    
    def _determine_visual_tier(self, title: str, section: str) -> VisualTier:
        """Determine the appropriate visual tier for a page"""
        return self.hierarchy_manager.determine_visual_tier(title, section, 'icon')  # Use icon as default asset_type
    
    def _generate_enhanced_prompt(self, title: str, asset_type: str, section: str) -> str:
        """Generate enhanced prompt for any asset type with luxury aesthetics and emotional intelligence"""
        # Determine visual tier based on title and section
        visual_tier = self._determine_visual_tier(title, section)
        
        # Determine emotional context
        emotional_context = self._determine_emotional_context(title, section)
        
        # Determine page type from section
        page_type = 'hub' if 'hub' in title.lower() else section
        
        # Route to specific prompt generators based on asset type
        if asset_type == 'icon':
            return self._generate_enhanced_icon_prompt(
                title, section, page_type, visual_tier, emotional_context
            )
        elif asset_type == 'cover':
            return self._generate_enhanced_cover_prompt(
                title, section, page_type, visual_tier, emotional_context
            )
        elif asset_type == 'letter_header':
            return self._generate_enhanced_letter_header_prompt(
                title, emotional_context
            )
        else:
            # Fallback for other asset types
            return self.prompt_manager.create_prompt(
                title=title,
                category=section,
                asset_type=asset_type,
                tier=visual_tier.value,
                custom_elements={
                    'emotional_context': emotional_context.value,
                    'page_type': page_type,
                    'luxury_tier': visual_tier.value
                }
            )
    
    def _get_enhanced_textures(self) -> List[Dict]:
        """Get ultra-premium luxury texture patterns"""
        textures = []
        luxury_textures = [
            {"title": "Blueprint Grid", "slug": "blueprint-grid", "category": "technical"},
            {"title": "Parchment", "slug": "parchment", "category": "heritage"},
            {"title": "Legal Pad", "slug": "legal-pad", "category": "professional"},
            {"title": "Marble", "slug": "marble", "category": "luxury"},
            {"title": "Mahogany Grain", "slug": "mahogany-grain", "category": "executive"},
            {"title": "Italian Leather", "slug": "italian-leather", "category": "luxury"},
            {"title": "Belgian Lace", "slug": "belgian-lace", "category": "heritage"},
            {"title": "Gold Leaf Watermark", "slug": "gold-watermark", "category": "premium"},
            {"title": "Engineering Vellum", "slug": "engineering-vellum", "category": "technical"},
            {"title": "Venetian Silk", "slug": "venetian-silk", "category": "luxury"}
        ]
        
        for texture in luxury_textures:
            enhanced_prompt = self.prompt_manager.create_prompt(
                title=texture['title'],
                category=texture['category'],
                asset_type='texture',
                custom_elements={
                    'seamless': True,
                    'luxury_materials': True,
                    'high_resolution': '512x512px',
                    'texture_category': texture['category']
                }
            )
            
            textures.append({
                'title': texture['title'],
                'slug': texture['slug'],
                'category': texture['category'],
                'prompt': enhanced_prompt
            })
        
        return textures
    
    def _get_enhanced_database_icons(self) -> List[Dict]:
        """Get ultra-premium database category icons"""
        db_icons = []
        database_categories = [
            {"title": "Financial Accounts", "slug": "db-accounts", "category": "financial"},
            {"title": "Property Records", "slug": "db-properties", "category": "property"},
            {"title": "Insurance Policies", "slug": "db-insurance", "category": "insurance"},
            {"title": "Professional Contacts", "slug": "db-contacts", "category": "contacts"},
            {"title": "Legal Documents", "slug": "db-documents", "category": "legal"},
            {"title": "Family Keepsakes", "slug": "db-keepsakes", "category": "family"},
            {"title": "Executor Tasks", "slug": "db-tasks", "category": "executor"},
            {"title": "Correspondence", "slug": "db-letters", "category": "letters"},
            {"title": "Digital Assets", "slug": "db-digital", "category": "digital"},
            {"title": "Service Subscriptions", "slug": "db-subscriptions", "category": "subscriptions"}
        ]
        
        for db_category in database_categories:
            visual_tier = VisualTier.TIER_3_DOCUMENT  # Databases are functional/document tier
            emotional_context = self._determine_emotional_context(db_category['title'], db_category['category'])
            
            enhanced_prompt = self.prompt_manager.create_prompt(
                title=db_category['title'],
                category=db_category['category'],
                asset_type='icon',
                tier=visual_tier.value,
                custom_elements={
                    'database_category': True,
                    'emotional_context': emotional_context.value,
                    'data_organization': True,
                    'professional_aesthetic': True
                }
            )
            
            db_icons.append({
                'title': db_category['title'],
                'slug': db_category['slug'],
                'category': db_category['category'],
                'visual_tier': visual_tier.value,
                'emotional_context': emotional_context.value,
                'prompt': enhanced_prompt
            })
        
        return db_icons

# Standalone function for import by asset_generator.py
def sync_with_yaml() -> Dict[str, List[Dict]]:
    """Standalone function wrapper for ultra-premium YAML sync"""
    import logging
    from pathlib import Path
    
    # Set up enhanced logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    
    # Get the correct path to split_yaml directory
    yaml_dir = Path(__file__).parent.parent / 'split_yaml'
    
    # Use the enhanced class-based implementation
    sync = YAMLSyncComprehensive(str(yaml_dir))
    
    logger = logging.getLogger('UltraPremiumSync')
    logger.info("🚀 Starting ultra-premium YAML synchronization...")
    
    try:
        result = sync.sync_with_yaml()
        logger.info("✨ Ultra-premium prompt generation complete!")
        return result
    except Exception as e:
        logger.error(f"❌ Ultra-premium sync failed: {e}")
        raise

if __name__ == "__main__":
    # Test the ultra-premium sync
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('UltraPremiumTest')
    logger.info("🏆 Testing Ultra-Premium Estate Planning Asset Generation System 🏆")
    
    try:
        sync = YAMLSyncComprehensive()
        pages = sync.sync_with_yaml()
        
        total = sum(len(v) for v in pages.values())
        logger.info(f"\n✨ ULTRA-PREMIUM SYNC COMPLETE ✨")
        logger.info(f"Total luxury assets generated: {total}")
        logger.info(f"Estimated cost (premium generation): ${total * 0.08:.2f}")
        
        # Sample some enhanced prompts
        logger.info("\n🔍 Sample Enhanced Prompts:")
        if pages.get('icons'):
            logger.info(f"Icon sample: {pages['icons'][0]['prompt'][:100]}...")
        if pages.get('covers'):
            logger.info(f"Cover sample: {pages['covers'][0]['prompt'][:100]}...")
            
        logger.info("\n📊 Enhanced Features Applied:")
        logger.info("  ✓ 5-tier visual hierarchy")
        logger.info("  ✓ Emotional intelligence integration")
        logger.info("  ✓ Luxury aesthetic enhancement")
        logger.info("  ✓ Section-specific styling")
        logger.info("  ✓ Ultra-premium materials & textures")
        
    except Exception as e:
        logger.error(f"❌ Ultra-premium test failed: {e}")
        raise