#!/usr/bin/env python3
"""
Patch script to add WebSocket visibility to PromptTemplateManager
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
    import_line = "from typing import Dict, List, Optional, Any"
    
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
    
    # Find the __init__ method of PromptTemplateManager
    init_pattern = '''    def __init__(self):
        """Initialize the prompt template manager"""
        self.emotional_elements = EmotionalIntelligence()'''
    
    if "self.broadcaster = " not in content:
        # Add broadcaster initialization
        broadcaster_init = '''    def __init__(self):
        """Initialize the prompt template manager"""
        self.emotional_elements = EmotionalIntelligence()
        
        # Initialize WebSocket broadcaster for real-time visibility
        try:
            self.broadcaster = get_broadcaster()
        except Exception:
            self.broadcaster = None  # Graceful fallback if not available'''
        
        content = content.replace(init_pattern, broadcaster_init)
        print("✅ Added broadcaster initialization to __init__")
    else:
        print("⏭️ Broadcaster already initialized")
    
    return content


def patch_create_prompt(content):
    """Add visibility to prompt creation"""
    
    # Find the create_prompt method
    old_method_start = '''    def create_prompt(self, 
                     title: str,
                     category: str,
                     asset_type: str,
                     tier: str = None,
                     custom_elements: Dict[str, Any] = None) -> str:
        """Create a complete prompt with all elements"""'''
    
    new_method_start = '''    def create_prompt(self, 
                     title: str,
                     category: str,
                     asset_type: str,
                     tier: str = None,
                     custom_elements: Dict[str, Any] = None) -> str:
        """Create a complete prompt with all elements"""
        
        # Emit prompt template creation start
        if self.broadcaster:
            self.broadcaster.emit('prompt_template_start', {
                'title': title,
                'category': category,
                'asset_type': asset_type,
                'tier': tier,
                'timestamp': datetime.now().isoformat()
            })'''
    
    if "prompt_template_start" not in content:
        content = content.replace(old_method_start, new_method_start)
        print("✅ Added prompt creation start visibility")
    
    # Add visibility for template selection
    old_template = '''        # Get tier-specific template
        if not tier:
            tier = self._determine_tier(category, title)'''
    
    new_template = '''        # Get tier-specific template
        if not tier:
            tier = self._determine_tier(category, title)
        
        # Emit tier selection event
        if self.broadcaster:
            self.broadcaster.emit('prompt_tier_selected', {
                'title': title,
                'tier': tier,
                'category': category,
                'timestamp': datetime.now().isoformat()
            })'''
    
    if "prompt_tier_selected" not in content:
        content = content.replace(old_template, new_template)
        print("✅ Added tier selection visibility")
    
    # Add visibility for emotional elements
    old_emotional = '''        # Add emotional intelligence layer
        emotional_layer = self.emotional_elements.get_emotional_prompt('''
    
    new_emotional = '''        # Add emotional intelligence layer
        if self.broadcaster:
            self.broadcaster.emit('adding_emotional_layer', {
                'title': title,
                'status': 'processing',
                'timestamp': datetime.now().isoformat()
            })
        
        emotional_layer = self.emotional_elements.get_emotional_prompt('''
    
    if "adding_emotional_layer" not in content:
        content = content.replace(old_emotional, new_emotional)
        print("✅ Added emotional layer visibility")
    
    return content


def patch_build_template(content):
    """Add visibility to template building"""
    
    # Look for _build_*_template methods
    template_methods = [
        '_build_icon_template',
        '_build_cover_template',
        '_build_texture_template',
        '_build_letter_header_template',
        '_build_database_icon_template'
    ]
    
    for method_name in template_methods:
        pattern = f"def {method_name}("
        
        if pattern in content:
            # Add visibility at the start of each template builder
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if f"    def {method_name}(" in line:
                    # Find the docstring end
                    for j in range(i+1, min(i+10, len(lines))):
                        if '"""' in lines[j] and j > i+1:  # End of docstring
                            # Insert visibility code after docstring
                            visibility_code = f'''        
        # Emit template building event
        if self.broadcaster:
            self.broadcaster.emit('template_building', {{
                'template_type': '{method_name.replace("_build_", "").replace("_template", "")}',
                'tier': tier.value,
                'timestamp': datetime.now().isoformat()
            }})'''
                            if "template_building" not in content:
                                lines.insert(j+1, visibility_code)
                                print(f"✅ Added visibility to {method_name}")
                            break
                    break
            
            content = '\n'.join(lines)
    
    return content


def add_helper_methods(content):
    """Add helper methods for visibility"""
    
    helper_methods = '''
    def emit_template_complete(self, title: str, prompt_length: int, complexity: str = "standard"):
        """Emit template completion event"""
        if self.broadcaster:
            self.broadcaster.emit('prompt_template_complete', {
                'title': title,
                'prompt_length': prompt_length,
                'complexity': complexity,
                'timestamp': datetime.now().isoformat()
            })
    
    def emit_style_elements(self, title: str, elements: List[str]):
        """Emit style elements being applied"""
        if self.broadcaster:
            self.broadcaster.emit('style_elements_applied', {
                'title': title,
                'elements': elements,
                'count': len(elements),
                'timestamp': datetime.now().isoformat()
            })
    
    def emit_luxury_indicators(self, title: str, indicators: List[str]):
        """Emit luxury indicators being applied"""
        if self.broadcaster:
            self.broadcaster.emit('luxury_indicators_applied', {
                'title': title,
                'indicators': indicators,
                'count': len(indicators),
                'timestamp': datetime.now().isoformat()
            })
'''
    
    # Find a good place to insert (at the end of the class)
    if "def emit_template_complete" not in content:
        # Find the end of the PromptTemplateManager class
        lines = content.split('\n')
        
        # Find the class definition
        class_start = None
        for i, line in enumerate(lines):
            if "class PromptTemplateManager:" in line:
                class_start = i
                break
        
        if class_start:
            # Find the end of the class (next class or end of file)
            class_end = len(lines)
            for i in range(class_start + 1, len(lines)):
                if lines[i].startswith("class ") and not lines[i].startswith("    "):
                    class_end = i
                    break
            
            # Insert before the end of class
            lines.insert(class_end - 1, helper_methods)
            content = '\n'.join(lines)
            print("✅ Added helper methods for visibility")
    
    return content


def main():
    """Main patch script"""
    
    print("="*60)
    print("Prompt Templates Visibility Integration")
    print("="*60)
    
    os.chdir("/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation")
    
    filepath = Path("prompt_templates.py")
    
    if not filepath.exists():
        print("❌ prompt_templates.py not found!")
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
        content = patch_create_prompt(content)
        content = patch_build_template(content)
        content = add_helper_methods(content)
        
        # Add datetime import if needed
        if "from datetime import datetime" not in content:
            # Add after other imports
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("from typing import"):
                    lines.insert(i+1, "from datetime import datetime")
                    break
            content = '\n'.join(lines)
            print("✅ Added datetime import")
        
        # Write back
        with open(filepath, 'w') as f:
            f.write(content)
        
        print("\n✅ Prompt Templates integration complete!")
        print(f"Backup saved at: {backup_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Integration failed: {e}")
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, filepath)
        return 1


if __name__ == "__main__":
    sys.exit(main())