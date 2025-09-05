# Theme Generation Integration Plan

## Current State Analysis

### What We Have Working
- **Web Dashboard** at `http://localhost:4500`
- **Master Prompt Editor** for icons/covers
- **YAML-driven discovery** from `split_yaml/` directory
- **Review & Approve workflow** with visual preview
- **WebSocket real-time updates**
- **Budget tracking** and cost controls

### What Needs Integration
- Theme-specific assets (337 total):
  - 162 Icons
  - 162 Covers
  - 3 Letter Headers
  - 10 Textures

## Core Requirements

1. **ALL generation must use existing web GUI** - No standalone scripts
2. **ALL prompts must be editable** - User can modify before generation
3. **ALL assets must be reviewable** - Visual preview before approval
4. **ALL configuration in YAML** - Follow existing pattern from split_yaml/

## Proposed Implementation

### Phase 1: YAML Configuration for Themes

Create `split_yaml/22_theme_assets.yaml`:

```yaml
theme:
  name: "Estate Planning Executive"
  version: "1.0.0"
  description: "Premium theme for high-net-worth estate planning"
  
  style_guide:
    colors:
      primary: "#0A1628"  # Deep Navy
      secondary: "#D4AF37"  # Gold
      neutral: "#2C3E50"  # Charcoal Grey
    
    mood_keywords:
      - sophisticated
      - minimalist
      - corporate
      - premium
      - trustworthy

  assets:
    icons:
      count: 162
      budget: 6.48
      categories:
        - name: "document_types"
          items:
            - title: "Last Will and Testament"
              description: "Formal will document icon"
              emotional_tone: "SECURE_PROTECTION"
            - title: "Living Trust"
              description: "Revocable trust icon"
              emotional_tone: "TRUSTED_GUIDE"
            # ... more items
        
    covers:
      count: 162
      budget: 6.48
      dimensions: "1500x400"
      # ... similar structure
    
    letter_headers:
      count: 3
      budget: 0.15
      dimensions: "2100x600"
      items:
        - title: "Formal Correspondence"
        - title: "Legal Documents"
        - title: "Client Communications"
    
    textures:
      count: 10
      budget: 0.50
      dimensions: "1920x1080"
      materials:
        - "brushed_metal"
        - "fine_linen"
        - "marble_veining"
        # ... more materials
```

### Phase 2: Extend Web Dashboard

#### 2.1 Add Theme Routes to review_dashboard.py

```python
@app.route('/theme-generator')
def theme_generator():
    """Theme asset generation interface"""
    theme_config = load_yaml('split_yaml/22_theme_assets.yaml')
    return render_template('theme_generator.html', 
                         theme=theme_config)

@app.route('/api/theme-assets')
def get_theme_assets():
    """API endpoint for theme asset discovery"""
    return discover_theme_assets_from_yaml()
```

#### 2.2 Extend Master Prompt Editor

Add tabs for new asset types:
- Icons (existing)
- Covers (existing) 
- Letter Headers (NEW)
- Textures (NEW)

### Phase 3: Integration Points

#### 3.1 Discovery Function
```python
def discover_all_generation_needs():
    """Unified discovery from YAML"""
    page_assets = discover_page_assets()      # Existing
    theme_assets = discover_theme_assets()    # New
    return {
        'pages': page_assets,
        'theme': theme_assets,
        'total_count': len(page_assets) + len(theme_assets),
        'total_budget': calculate_total_budget()
    }
```

#### 3.2 Generation Flow
```
1. Load YAMLs → Auto-discover all assets
2. Generate initial prompts from metadata
3. Display in Web GUI with edit capability
4. User edits prompts as needed
5. Generate 3-5 samples for review
6. User approves/rejects
7. Generate full set (337 assets)
8. Organize in theme directory structure
```

### Phase 4: Testing Strategy

#### 4.1 Test Current System First
```bash
# Test existing icon/cover generation
cd asset_generation
python3 review_dashboard.py

# Navigate to http://localhost:4500
# Test with 3 sample images
# Verify edit/review/approve flow works
```

#### 4.2 Incremental Theme Integration
1. Start with just 3 theme icons
2. Test full workflow with minimal set
3. Expand to full 337 assets only after validation

### Phase 5: File Organization

```
asset_generation/
├── split_yaml/
│   ├── [01-21]_*.yaml          # Existing page definitions
│   └── 22_theme_assets.yaml    # NEW theme definitions
├── themes/
│   └── estate_planning_executive/
│       ├── prompts/             # Generated prompts
│       │   ├── icons.json
│       │   ├── covers.json
│       │   ├── headers.json
│       │   └── textures.json
│       ├── samples/             # Test generations
│       └── production/          # Final assets
│           ├── icons/
│           ├── covers/
│           ├── headers/
│           └── textures/
```

## Implementation Order

1. **Test existing system** - Verify current icon/cover flow
2. **Create theme YAML** - Define all 337 assets
3. **Extend discovery** - Add theme asset discovery
4. **Update web routes** - Add theme endpoints
5. **Create UI components** - Theme tabs in editor
6. **Test with samples** - 3 images per type
7. **Full generation** - Only after approval

## Risk Mitigation

- **Budget Protection**: Hard limit at $13.11
- **Sample First**: Always test with 3 images
- **Incremental Development**: One asset type at a time
- **Rollback Ready**: Keep existing code intact

## Success Criteria

✅ All prompts editable in web GUI
✅ All assets reviewable before generation  
✅ All configuration in YAML files
✅ Budget never exceeds $13.11
✅ Same UX as current icon/cover flow

## Next Immediate Steps

1. Test current system with 3 sample icons
2. Verify web GUI edit/review flow
3. Create minimal theme YAML (3 assets)
4. Test theme integration with samples
5. Expand to full 337 assets

---

**Note**: No code changes until current system is fully tested and validated.