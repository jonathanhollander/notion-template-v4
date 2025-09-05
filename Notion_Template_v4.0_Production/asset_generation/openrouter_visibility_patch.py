#!/usr/bin/env python3
"""
Patch script to add WebSocket visibility to OpenRouterOrchestrator
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


def backup_file(filepath):
    """Create a backup of the file before modifying"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def patch_imports(content):
    """Add WebSocket broadcaster import"""
    
    # Find the imports section
    import_line = "from typing import Dict, List, Any, Optional, Tuple"
    
    if "from websocket_broadcaster import get_broadcaster" not in content:
        # Add the import after the typing imports
        new_import = "\nfrom websocket_broadcaster import get_broadcaster"
        content = content.replace(import_line, import_line + new_import)
        print("✅ Added WebSocket broadcaster import")
    else:
        print("⏭️ WebSocket import already exists")
    
    return content


def patch_init(content):
    """Add broadcaster initialization to __init__"""
    
    # Find the __init__ method
    init_pattern = """    def __init__(self, api_key: str = None):
        \"\"\"Initialize the orchestrator with OpenRouter API key\"\"\"
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')"""
    
    init_with_broadcaster = """    def __init__(self, api_key: str = None):
        \"\"\"Initialize the orchestrator with OpenRouter API key\"\"\"
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')"""
    
    if "self.broadcaster = get_broadcaster()" not in content:
        # Add broadcaster initialization after api_key setup
        broadcaster_init = """
        
        # Initialize WebSocket broadcaster for real-time visibility
        try:
            self.broadcaster = get_broadcaster()
            self.logger.info("✓ WebSocket broadcaster initialized in OpenRouter orchestrator")
        except Exception as e:
            self.broadcaster = None
            self.logger.warning(f"WebSocket broadcaster not available: {e}")"""
        
        # Find the line after self.api_key setup
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')" in line:
                # Insert after the api_key validation
                for j in range(i+1, min(i+10, len(lines))):
                    if "self.models = {" in lines[j]:
                        # Insert before models initialization
                        lines.insert(j, broadcaster_init)
                        break
                break
        
        content = '\n'.join(lines)
        print("✅ Added broadcaster initialization to __init__")
    else:
        print("⏭️ Broadcaster already initialized")
    
    return content


def patch_generate_competitive_prompts(content):
    """Add visibility to competitive prompt generation"""
    
    # Add visibility at the start of the method
    old_start = '''    async def generate_competitive_prompts(self, page_info: Dict[str, Any]) -> PromptCompetition:
        """Generate competitive prompts using structured master prompt system"""
        self.logger.info(f"Generating competitive prompts for: {page_info['title']}")'''
    
    new_start = '''    async def generate_competitive_prompts(self, page_info: Dict[str, Any]) -> PromptCompetition:
        """Generate competitive prompts using structured master prompt system"""
        self.logger.info(f"Generating competitive prompts for: {page_info['title']}")
        
        # Emit model competition start event
        if self.broadcaster:
            self.broadcaster.emit('model_competition_start', {
                'asset_name': page_info.get('title', 'Unknown'),
                'models': list(self.models.keys()),
                'timestamp': datetime.now().isoformat()
            })'''
    
    if "model_competition_start" not in content:
        content = content.replace(old_start, new_start)
        print("✅ Added competition start visibility")
    
    # Add visibility for each model's prompt generation
    old_loop = '''        # Execute all tasks in parallel
        results = []
        for model_name, task in tasks:
            result = await task
            if result['success']:'''
    
    new_loop = '''        # Execute all tasks in parallel
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
            
            if result['success']:'''
    
    if "prompt_generated" not in content:
        content = content.replace(old_loop, new_loop)
        print("✅ Added prompt generation visibility")
    
    # Add visibility for winner selection
    old_winner = '''        # Find winner based on highest confidence
        winner = max(results, key=lambda x: x.confidence) if results else None'''
    
    new_winner = '''        # Find winner based on highest confidence
        winner = max(results, key=lambda x: x.confidence) if results else None
        
        # Emit winner selection event
        if self.broadcaster and winner:
            self.broadcaster.emit('model_winner_selected', {
                'asset_name': page_info.get('title', 'Unknown'),
                'winner': winner.model,
                'confidence': winner.confidence,
                'competitors': [
                    {
                        'model': v.model,
                        'confidence': v.confidence,
                        'prompt_preview': v.structured_prompt.prompt[:200] + '...'
                    }
                    for v in results
                ],
                'timestamp': datetime.now().isoformat()
            })'''
    
    if "model_winner_selected" not in content:
        content = content.replace(old_winner, new_winner)
        print("✅ Added winner selection visibility")
    
    return content


def patch_call_openrouter(content):
    """Add visibility to OpenRouter API calls"""
    
    # Find the _call_openrouter_with_master_prompt method
    method_start = "async def _call_openrouter_with_master_prompt"
    
    if method_start in content:
        # Add visibility before API call
        old_call = '''        try:
            async with aiohttp.ClientSession() as session:'''
        
        new_call = '''        # Emit API call start event
        if self.broadcaster:
            self.broadcaster.emit('openrouter_api_call', {
                'model': model,
                'status': 'starting',
                'timestamp': datetime.now().isoformat()
            })
        
        try:
            async with aiohttp.ClientSession() as session:'''
        
        if "openrouter_api_call" not in content:
            content = content.replace(old_call, new_call)
            print("✅ Added OpenRouter API call visibility")
    
    return content


def patch_scoring(content):
    """Add visibility to prompt scoring"""
    
    # Find the score_prompt_quality method
    old_scoring = '''    async def score_prompt_quality(self, prompt: str, page_info: Dict[str, Any]) -> float:
        """Score a prompt's quality using multiple criteria"""'''
    
    new_scoring = '''    async def score_prompt_quality(self, prompt: str, page_info: Dict[str, Any]) -> float:
        """Score a prompt's quality using multiple criteria"""
        
        # Emit scoring start event
        if self.broadcaster:
            self.broadcaster.emit('prompt_scoring', {
                'asset_name': page_info.get('title', 'Unknown'),
                'status': 'evaluating',
                'timestamp': datetime.now().isoformat()
            })'''
    
    if "score_prompt_quality" in content and "prompt_scoring" not in content:
        content = content.replace(old_scoring, new_scoring)
        print("✅ Added prompt scoring visibility")
    
    return content


def add_helper_methods(content):
    """Add helper methods for visibility control"""
    
    helper_methods = '''
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
'''
    
    # Find a good place to insert (before the last method or at the end of class)
    if "def emit_progress" not in content:
        # Find the end of the class
        lines = content.split('\n')
        
        # Find the last method in the class
        last_method_index = None
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('def ') and not lines[i].strip().startswith('def __'):
                last_method_index = i
                break
        
        if last_method_index:
            # Find the end of the last method
            indent_level = len(lines[last_method_index]) - len(lines[last_method_index].lstrip())
            
            for i in range(last_method_index + 1, len(lines)):
                # Find where the indentation returns to class level
                if lines[i].strip() and not lines[i].startswith(' ' * (indent_level + 4)):
                    lines.insert(i, helper_methods)
                    break
            else:
                # Add at the end if we couldn't find a good spot
                lines.append(helper_methods)
            
            content = '\n'.join(lines)
            print("✅ Added helper methods for visibility")
    
    return content


def main():
    """Main patch script"""
    
    print("="*60)
    print("OpenRouter Orchestrator Visibility Integration")
    print("="*60)
    
    os.chdir("/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation")
    
    filepath = Path("openrouter_orchestrator.py")
    
    if not filepath.exists():
        print("❌ openrouter_orchestrator.py not found!")
        return 1
    
    # Create backup
    backup_path = backup_file(filepath)
    
    try:
        # Read the file
        with open(filepath, 'r') as f:
            content = f.read()
        
        print("\nApplying visibility patches...")
        
        # Apply patches
        content = patch_imports(content)
        content = patch_init(content)
        content = patch_generate_competitive_prompts(content)
        content = patch_call_openrouter(content)
        content = patch_scoring(content)
        content = add_helper_methods(content)
        
        # Add datetime import if needed
        if "from datetime import datetime" not in content:
            content = "from datetime import datetime\n" + content
            print("✅ Added datetime import")
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(content)
        
        print("\n✅ OpenRouter integration complete!")
        print(f"Backup saved at: {backup_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, filepath)
        return 1


if __name__ == "__main__":
    sys.exit(main())