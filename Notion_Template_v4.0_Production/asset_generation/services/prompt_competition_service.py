#!/usr/bin/env python3
"""
Prompt Competition Service for Estate Planning Concierge v4.0
Generates competitive prompt variations using multiple AI models.
"""

import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from utils.database_manager import AssetDatabase
from prompt_templates import ESTATE_PROMPT_BUILDER


class PromptCompetitionService:
    """Generates competitive prompt variations using multiple AI models."""
    
    def __init__(self, db: AssetDatabase, api_key: str = None):
        """Initialize the prompt competition service.
        
        Args:
            db: Database manager instance
            api_key: OpenRouter API key
        """
        self.db = db
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        self.logger = self._setup_logger()
        
        # AI models for competitive prompt generation
        self.competitive_models = [
            {
                'name': 'claude-3.5-sonnet',
                'model_id': 'anthropic/claude-3.5-sonnet',
                'specialty': 'Creative and sophisticated prompts'
            },
            {
                'name': 'gpt-4o',
                'model_id': 'openai/gpt-4o',
                'specialty': 'Technical precision and clarity'
            },
            {
                'name': 'gemini-pro',
                'model_id': 'google/gemini-pro',
                'specialty': 'Innovative and unique perspectives'
            }
        ]
        
        if not self.api_key:
            self.logger.warning("No OpenRouter API key provided - competitive generation will be limited")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the service."""
        logger = logging.getLogger('PromptCompetitionService')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    async def create_competition(
        self, base_prompt: str, asset_type: str, category: str, index: int
    ) -> int:
        """Create a new prompt competition with AI model variations.
        
        Args:
            base_prompt: Base prompt from ESTATE_PROMPT_BUILDER
            asset_type: Type of asset (icons, covers, etc.)
            category: Category of the prompt
            index: Index within category
            
        Returns:
            Competition ID
        """
        self.logger.info(f"Creating competition for {asset_type} {index}")
        
        # Create competition record
        competition_id = await self.db.create_competition(
            base_prompt, asset_type, category, index
        )
        
        # Generate variations using different AI models
        for model_config in self.competitive_models:
            try:
                variation = await self._generate_variation(
                    base_prompt, model_config, asset_type, category
                )
                
                await self.db.store_competitive_prompt(
                    competition_id, 
                    model_config['name'], 
                    variation,
                    {'specialty': model_config['specialty']}
                )
                
                self.logger.info(f"Generated {model_config['name']} variation")
                
            except Exception as e:
                self.logger.error(f"Failed to generate variation with {model_config['name']}: {e}")
                
                # Fallback: create a modified version of the base prompt
                fallback_variation = self._create_fallback_variation(
                    base_prompt, model_config['name']
                )
                await self.db.store_competitive_prompt(
                    competition_id,
                    f"{model_config['name']}-fallback",
                    fallback_variation,
                    {'specialty': 'Fallback variation', 'error': str(e)}
                )
        
        self.logger.info(f"Competition {competition_id} created with {len(self.competitive_models)} variations")
        return competition_id
    
    async def _generate_variation(
        self, base_prompt: str, model_config: Dict, asset_type: str, category: str
    ) -> str:
        """Generate a prompt variation using a specific AI model.
        
        Args:
            base_prompt: Original prompt to vary
            model_config: Model configuration
            asset_type: Type of asset
            category: Category name
            
        Returns:
            Generated prompt variation
        """
        if not self.api_key:
            return self._create_fallback_variation(base_prompt, model_config['name'])
        
        # Create variation prompt for the AI model
        variation_prompt = f"""
As an expert prompt engineer specializing in {model_config['specialty']}, create an enhanced version of this image generation prompt for estate planning assets.

Original prompt: "{base_prompt}"

Asset type: {asset_type}
Category: {category}

Requirements:
- Maintain the luxury estate planning theme
- Keep the core visual concept but enhance it with your specialty
- Make it more specific and visually compelling
- Ensure it's suitable for professional estate planning materials
- Add sophisticated details that elevate the visual quality

Return only the enhanced prompt, no explanation.
"""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': model_config['model_id'],
                    'messages': [
                        {'role': 'user', 'content': variation_prompt}
                    ],
                    'max_tokens': 200,
                    'temperature': 0.7
                }
                
                async with session.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        variation = result['choices'][0]['message']['content'].strip()
                        
                        # Clean up the response (remove quotes, explanations, etc.)
                        variation = self._clean_prompt_response(variation)
                        
                        return variation
                    else:
                        error_text = await response.text()
                        raise Exception(f"API error {response.status}: {error_text}")
                        
        except Exception as e:
            self.logger.error(f"API call failed for {model_config['name']}: {e}")
            raise
    
    def _clean_prompt_response(self, response: str) -> str:
        """Clean up AI model response to get just the prompt.
        
        Args:
            response: Raw response from AI model
            
        Returns:
            Cleaned prompt text
        """
        # Remove common prefixes
        prefixes_to_remove = [
            "Here's the enhanced prompt:",
            "Enhanced prompt:",
            "Here is the enhanced version:",
            "Enhanced version:",
        ]
        
        cleaned = response.strip()
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove surrounding quotes
        if (cleaned.startswith('"') and cleaned.endswith('"')) or \
           (cleaned.startswith("'") and cleaned.endswith("'")):
            cleaned = cleaned[1:-1]
        
        return cleaned.strip()
    
    def _create_fallback_variation(self, base_prompt: str, model_name: str) -> str:
        """Create a fallback variation when AI model is unavailable.
        
        Args:
            base_prompt: Original prompt
            model_name: Name of the model we're emulating
            
        Returns:
            Modified prompt as fallback
        """
        # Simple variations based on model specialty
        if 'claude' in model_name.lower():
            return f"{base_prompt}, rendered with sophisticated artistic detail and elegant composition"
        elif 'gpt' in model_name.lower():
            return f"{base_prompt}, with precise technical execution and professional clarity"
        elif 'gemini' in model_name.lower():
            return f"{base_prompt}, featuring innovative visual elements and unique creative perspective"
        else:
            return f"{base_prompt}, enhanced with premium quality and luxury aesthetics"
    
    async def create_competitions_for_asset_type(
        self, asset_type: str, count: int, category: str = "Estate Planning"
    ) -> List[int]:
        """Create competitions for all prompts of a specific asset type.
        
        Args:
            asset_type: Type of asset (icons, covers, textures, etc.)
            count: Number of assets to create competitions for
            category: Category name
            
        Returns:
            List of competition IDs
        """
        self.logger.info(f"Creating {count} competitions for {asset_type}")
        
        competition_ids = []
        
        for i in range(count):
            # Get base prompt from ESTATE_PROMPT_BUILDER
            if asset_type == 'icons':
                base_prompt = ESTATE_PROMPT_BUILDER.get_icon_prompt(i, count)
            elif asset_type == 'covers':
                base_prompt = ESTATE_PROMPT_BUILDER.get_cover_prompt(i, count)
            elif asset_type == 'textures':
                base_prompt = ESTATE_PROMPT_BUILDER.get_texture_prompt(i, count)
            elif asset_type == 'letter_headers':
                base_prompt = ESTATE_PROMPT_BUILDER.get_letter_header_prompt(i, count)
            elif asset_type == 'database_icons':
                base_prompt = ESTATE_PROMPT_BUILDER.get_database_icon_prompt(i, count)
            else:
                base_prompt = f"Estate planning {asset_type} design {i+1}"
            
            competition_id = await self.create_competition(
                base_prompt, asset_type, category, i + 1
            )
            competition_ids.append(competition_id)
            
            # Small delay to avoid overwhelming the API
            await asyncio.sleep(0.1)
        
        self.logger.info(f"Created {len(competition_ids)} competitions for {asset_type}")
        return competition_ids
    
    async def get_competition_status(self, competition_id: int) -> Dict[str, Any]:
        """Get status of a specific competition.
        
        Args:
            competition_id: Competition ID
            
        Returns:
            Competition status information
        """
        async with self.db._get_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM prompt_competitions WHERE id = ?", (competition_id,)
            )
            competition = await cursor.fetchone()
            
            if not competition:
                return {'error': 'Competition not found'}
            
            # Get competitive prompts count
            cursor = await db.execute(
                "SELECT COUNT(*) as count FROM competitive_prompts WHERE competition_id = ?",
                (competition_id,)
            )
            prompts_count = (await cursor.fetchone())['count']
            
            return {
                'competition_id': competition_id,
                'status': competition['competition_status'],
                'asset_type': competition['asset_type'],
                'category': competition['category'],
                'index': competition['index_in_category'],
                'prompts_generated': prompts_count,
                'created_at': competition['created_at']
            }


async def test_prompt_competition_service():
    """Test the prompt competition service."""
    print("🎭 Testing Prompt Competition Service...")
    
    # Initialize database and service
    db = AssetDatabase("test_competitions.db")
    await db.init_database()
    
    service = PromptCompetitionService(db)
    
    # Test single competition
    base_prompt = "Elegant estate planning icon with golden accents"
    competition_id = await service.create_competition(
        base_prompt, "icons", "Estate Planning", 1
    )
    
    print(f"✅ Created competition {competition_id}")
    
    # Test competition status
    status = await service.get_competition_status(competition_id)
    print(f"📊 Competition status: {status}")
    
    # Test batch creation
    competition_ids = await service.create_competitions_for_asset_type(
        "icons", 3, "Test Category"
    )
    print(f"✅ Created {len(competition_ids)} batch competitions")
    
    await db.close()
    print("🎭 Prompt Competition Service test complete!")


if __name__ == "__main__":
    asyncio.run(test_prompt_competition_service())