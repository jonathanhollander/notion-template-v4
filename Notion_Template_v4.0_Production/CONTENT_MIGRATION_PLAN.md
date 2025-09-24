# Content Migration Plan: Hardcoded Python to YAML
Date: September 23, 2025
Status: Ready for Implementation

## Executive Summary

This plan details the systematic migration of 3,063 lines of hardcoded Notion content from Python functions to maintainable YAML configuration files. The migration preserves all functionality while improving maintainability, reusability, and version control.

## Migration Overview

### Current State
- **Location**: Content hardcoded in Python functions within deploy.py
- **Volume**: 3,063 lines of content code
- **Structure**: 72+ function definitions creating Notion blocks directly
- **Content Types**: Security pages, dashboards, navigation, onboarding, role-specific content

### Target State
- **Location**: YAML files in `split_yaml/content/` directory
- **Structure**: Declarative YAML with block definitions
- **Integration**: Enhanced deploy.py with YAML content loader
- **Benefits**: Easier maintenance, version control, reusability

## Phase 1: Analysis & Preparation (Day 1)

### 1.1 Content Inventory
Create comprehensive inventory of all content functions:

```python
# Script: analyze_content_functions.py
# Analyzes deploy_WITH_CONTENT.py.recovered to catalog all functions

CONTENT_FUNCTIONS = [
    # Security Center Functions
    "create_security_center_page",          # Line 3366
    "create_security_monitoring_dashboard",  # Line 3469
    "create_encryption_guidelines",         # Line 3557
    "setup_access_logging_system",         # Line 3670
    "create_security_checklists",          # Line 3758
    "create_security_audit_templates",     # Line 3872
    
    # Onboarding Functions
    "create_onboarding_hub_page",          # Line 4034
    "create_welcome_wizard",               # Line 4157
    "create_guided_setup_flow",            # Line 4195
    "create_complexity_selector",          # Line 4263
    "create_role_selection_system",        # Line 4391
    "create_onboarding_progress_tracker",  # Line 4519
    
    # Dashboard Functions
    "create_grid_dashboard",
    "create_progress_visualization",
    "create_metrics_display",
    
    # Navigation Functions
    "create_breadcrumb_navigation",
    "create_back_to_hub_navigation",
    "create_quick_jump_menu",
]
```

### 1.2 YAML Schema Design
Design comprehensive schema for all Notion block types:

```yaml
# split_yaml/content/_schema.yaml
block_types:
  heading_1:
    properties:
      text: string
      color: optional[string]
  
  paragraph:
    properties:
      text: string
      link: optional[url]
  
  callout:
    properties:
      icon: emoji|url
      text: string
      color: background_color
  
  numbered_list_item:
    properties:
      text: string
      children: optional[blocks]
  
  bulleted_list_item:
    properties:
      text: string
      children: optional[blocks]
  
  to_do:
    properties:
      text: string
      checked: boolean
  
  toggle:
    properties:
      text: string
      children: blocks
  
  divider:
    properties: {}
```

### 1.3 Directory Structure Setup
```bash
split_yaml/
├── content/
│   ├── _schema.yaml              # Block type definitions
│   ├── security/
│   │   ├── security_center.yaml
│   │   ├── monitoring_dashboard.yaml
│   │   ├── encryption_guidelines.yaml
│   │   ├── access_logging.yaml
│   │   ├── security_checklists.yaml
│   │   └── audit_templates.yaml
│   ├── onboarding/
│   │   ├── onboarding_hub.yaml
│   │   ├── welcome_wizard.yaml
│   │   ├── guided_setup.yaml
│   │   ├── complexity_selector.yaml
│   │   ├── role_selection.yaml
│   │   └── progress_tracker.yaml
│   ├── dashboards/
│   │   ├── preparation_hub.yaml
│   │   ├── executor_hub.yaml
│   │   └── family_hub.yaml
│   └── navigation/
│       ├── breadcrumbs.yaml
│       ├── hub_navigation.yaml
│       └── quick_menus.yaml
```

## Phase 2: Content Extraction Tools (Day 1-2)

### 2.1 Python Function Parser
```python
# extract_content.py
import ast
import json
import yaml
from pathlib import Path

class ContentExtractor:
    def __init__(self, source_file):
        self.source_file = source_file
        self.functions = {}
        
    def extract_function_content(self, function_name):
        """Extract block definitions from a function"""
        # Parse the function AST
        # Extract block array definitions
        # Convert to YAML-friendly structure
        
    def convert_block_to_yaml(self, block):
        """Convert a Notion block dict to YAML format"""
        yaml_block = {
            'type': block['type']
        }
        
        # Handle different block types
        if block['type'] == 'heading_1':
            yaml_block['text'] = self.extract_text(block['heading_1'])
        elif block['type'] == 'callout':
            yaml_block['icon'] = block['callout']['icon']['emoji']
            yaml_block['text'] = self.extract_text(block['callout'])
            yaml_block['color'] = block['callout']['color']
            
        return yaml_block
        
    def extract_text(self, block_content):
        """Extract plain text from rich text array"""
        rich_text = block_content.get('rich_text', [])
        if rich_text:
            return rich_text[0]['text']['content']
        return ""
```

### 2.2 Batch Conversion Script
```python
# migrate_content.py
import os
from pathlib import Path
from extract_content import ContentExtractor

def migrate_all_content():
    extractor = ContentExtractor('deploy_WITH_CONTENT.py.recovered')
    
    # Security Center content
    security_functions = [
        ('create_security_center_page', 'security/security_center.yaml'),
        ('create_security_monitoring_dashboard', 'security/monitoring_dashboard.yaml'),
        # ... more functions
    ]
    
    for func_name, output_path in security_functions:
        content = extractor.extract_function_content(func_name)
        save_to_yaml(content, f'split_yaml/content/{output_path}')
        
def save_to_yaml(content, path):
    """Save extracted content to YAML file"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(content, f, default_flow_style=False, sort_keys=False)
```

## Phase 3: YAML Content Structure (Day 2)

### 3.1 Page Content YAML Format
```yaml
# split_yaml/content/security/security_center.yaml
page:
  title: "Security Center"
  icon: "🔒"
  blocks:
    - type: heading_1
      text: "🔒 Estate Security Center"
    
    - type: paragraph
      text: "Comprehensive security management and monitoring for estate planning activities, document protection, and access control oversight."
    
    - type: heading_2
      text: "Security Dashboard"
    
    - type: callout
      icon: "🛡️"
      text: "Security Status: ACTIVE - All systems monitored and protected"
      color: green_background
    
    - type: callout
      icon: "🔐"
      text: "Access Control: ENFORCED - Role-based permissions active"
      color: blue_background
    
    - type: heading_2
      text: "Security Protocols"
    
    - type: numbered_list
      items:
        - "Document encryption requirements enforced"
        - "Multi-factor authentication recommended for all users"
        - "Regular security audits and compliance checks"
        - "Secure backup and recovery procedures"
        - "Access logging and activity monitoring"
```

### 3.2 Reusable Components
```yaml
# split_yaml/content/components/navigation.yaml
components:
  back_to_hub:
    - type: divider
    
    - type: paragraph
      text: "↩️ Return to {{hub_name}}"
      link: "{{hub_url}}"
  
  breadcrumb:
    - type: paragraph
      text: "📍 {{path}}"
      style: "gray_text"
  
  progress_bar:
    - type: callout
      icon: "📊"
      text: "Progress: {{percentage}}% [{{bar}}] {{current}}/{{total}}"
      color: "{{color}}_background"
```

## Phase 4: Deploy.py Enhancement (Day 2-3)

### 4.1 YAML Content Loader
```python
# modules/content_loader.py
import yaml
from pathlib import Path
from typing import Dict, List, Any

class ContentLoader:
    def __init__(self, content_dir='split_yaml/content'):
        self.content_dir = Path(content_dir)
        self.content_cache = {}
        self.components = {}
        
    def load_page_content(self, page_name: str) -> List[Dict]:
        """Load content blocks for a specific page"""
        # Check if page has YAML content
        content_file = self.find_content_file(page_name)
        
        if content_file:
            return self.load_yaml_content(content_file)
        else:
            # Fallback to empty paragraph (current behavior)
            return [{"type": "paragraph", "paragraph": {"rich_text": []}}]
            
    def load_yaml_content(self, file_path: Path) -> List[Dict]:
        """Load and process YAML content file"""
        with open(file_path) as f:
            data = yaml.safe_load(f)
            
        blocks = []
        for block_def in data.get('blocks', []):
            notion_block = self.convert_to_notion_block(block_def)
            blocks.append(notion_block)
            
        return blocks
        
    def convert_to_notion_block(self, yaml_block: Dict) -> Dict:
        """Convert YAML block definition to Notion API format"""
        block_type = yaml_block['type']
        notion_block = {"type": block_type}
        
        if block_type == 'heading_1':
            notion_block['heading_1'] = {
                "rich_text": [{"text": {"content": yaml_block['text']}}]
            }
        elif block_type == 'callout':
            notion_block['callout'] = {
                "icon": {"emoji": yaml_block['icon']},
                "rich_text": [{"text": {"content": yaml_block['text']}}],
                "color": yaml_block.get('color', 'gray_background')
            }
        # ... handle other block types
        
        return notion_block
```

### 4.2 Integration with Deploy.py
```python
# Modification to deploy.py around line 699
from modules.content_loader import ContentLoader

content_loader = ContentLoader()

# In create_page_with_content function:
def create_page_with_content(parent_id, page_data):
    # ... existing code ...
    
    # Replace lines 699-702 with:
    if 'blocks' in page_data and page_data['blocks']:
        # Use provided blocks
        children = process_blocks(page_data['blocks'])
    else:
        # Try to load from YAML content
        yaml_content = content_loader.load_page_content(title)
        
        if yaml_content:
            logging.debug(f"Loaded {len(yaml_content)} blocks from YAML for '{title}'")
            children = yaml_content
        else:
            logging.debug(f"No content found for page '{title}', adding empty paragraph")
            children = [{"type": "paragraph", "paragraph": {"rich_text": []}}]
```

## Phase 5: Migration Execution (Day 3-4)

### 5.1 Automated Migration Script
```bash
#!/bin/bash
# migrate_all_content.sh

echo "Starting content migration..."

# Step 1: Extract all content
python3 scripts/extract_all_content.py \
    --source deploy_WITH_CONTENT.py.recovered \
    --output split_yaml/content/

# Step 2: Validate extracted content
python3 scripts/validate_yaml_content.py \
    --directory split_yaml/content/

# Step 3: Test with single page
python3 deploy.py \
    --test-single-page "Security Center" \
    --use-yaml-content

# Step 4: Generate migration report
python3 scripts/generate_migration_report.py \
    --before deploy_WITH_CONTENT.py.recovered \
    --after split_yaml/content/ \
    --output migration_report.md
```

### 5.2 Validation Script
```python
# validate_yaml_content.py
def validate_content_migration():
    """Validate all content was successfully migrated"""
    
    # Count blocks in original Python
    original_blocks = count_blocks_in_python('deploy_WITH_CONTENT.py.recovered')
    
    # Count blocks in YAML files
    yaml_blocks = count_blocks_in_yaml('split_yaml/content/')
    
    # Compare
    print(f"Original blocks: {original_blocks}")
    print(f"YAML blocks: {yaml_blocks}")
    print(f"Migration rate: {yaml_blocks/original_blocks*100:.1f}%")
    
    # Check for missing content
    missing = find_missing_content(original_blocks, yaml_blocks)
    if missing:
        print("WARNING: Missing content detected")
        for item in missing:
            print(f"  - {item}")
```

## Phase 6: Testing & Validation (Day 4-5)

### 6.1 Test Strategy
1. **Unit Testing**: Each YAML file loads correctly
2. **Integration Testing**: Deploy.py uses YAML content
3. **Comparison Testing**: Generated pages match original
4. **Performance Testing**: No degradation in deployment speed

### 6.2 Test Scripts
```python
# test_yaml_content.py
import pytest
from modules.content_loader import ContentLoader

def test_security_center_content():
    loader = ContentLoader()
    blocks = loader.load_page_content("Security Center")
    
    assert len(blocks) > 0
    assert blocks[0]['type'] == 'heading_1'
    assert '🔒' in blocks[0]['heading_1']['rich_text'][0]['text']['content']

def test_all_pages_have_content():
    loader = ContentLoader()
    pages = get_all_page_names()
    
    for page in pages:
        blocks = loader.load_page_content(page)
        assert len(blocks) > 0, f"Page {page} has no content"
```

## Phase 7: Rollout & Documentation (Day 5)

### 7.1 Gradual Rollout
1. Deploy Security Center with YAML content
2. Verify in Notion
3. Deploy Onboarding Hub with YAML content
4. Verify in Notion
5. Deploy remaining pages
6. Full system validation

### 7.2 Documentation Updates
- Update README with new YAML content structure
- Document content editing workflow
- Create content contribution guidelines
- Update deployment instructions

## Benefits of Migration

### Immediate Benefits
1. **Maintainability**: Edit content without touching code
2. **Version Control**: Track content changes separately
3. **Reusability**: Share content between pages
4. **Clarity**: Declarative content easier to understand

### Long-term Benefits
1. **Localization**: Easy translation to other languages
2. **Templates**: Create page templates for reuse
3. **Content Management**: Non-developers can edit content
4. **Testing**: Easier to test content separately

## Risk Mitigation

### Backup Strategy
1. Keep `deploy_WITH_CONTENT.py.recovered` as backup
2. Git commit after each successful migration phase
3. Test in separate Notion workspace first
4. Maintain rollback procedure

### Validation Checkpoints
- After each function migration
- After each page type (security, onboarding, etc.)
- Before and after full deployment
- User acceptance testing

## Timeline

**Day 1**: Analysis & Preparation
- Inventory all content functions
- Design YAML schema
- Set up directory structure

**Day 2**: Tool Development
- Build extraction scripts
- Create conversion utilities
- Test on sample functions

**Day 3**: Content Migration
- Run automated migration
- Validate YAML output
- Fix any conversion issues

**Day 4**: Integration & Testing
- Enhance deploy.py
- Test YAML loading
- Validate content rendering

**Day 5**: Rollout & Documentation
- Deploy to test workspace
- Update documentation
- Train team on new structure

## Success Criteria

✅ All 3,063 lines of content successfully extracted
✅ YAML files validate against schema
✅ Deploy.py loads and uses YAML content
✅ Generated Notion pages match original
✅ No content lost in migration
✅ Performance maintained or improved
✅ Documentation complete and accurate

## Next Steps

1. **Approval**: Review and approve this migration plan
2. **Environment Setup**: Create test Notion workspace
3. **Tool Development**: Build extraction and conversion scripts
4. **Execute Migration**: Run phased migration process
5. **Validate Results**: Comprehensive testing
6. **Production Deployment**: Roll out to main workspace

---

This migration plan ensures your valuable content is preserved, organized, and maintainable for the future. The systematic approach minimizes risk while maximizing the benefits of a configuration-driven architecture.