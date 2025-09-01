
## Codebase Notes

[2025-09-01 02:22:37] - # Estate Planning v4.0 - Codebase Structure & Key Insights

## Directory Structure
```
Notion_Template_v4.0_Production/
├── asset_generation/           # Core image generation system
│   ├── openrouter_orchestrator.py
│   ├── asset_generator.py
│   ├── sync_yaml_comprehensive.py
│   ├── prompt_templates.py
│   ├── emotional_elements.py
│   ├── visual_hierarchy.py
│   ├── quality_scorer.py
│   └── [7 more Python modules]
├── split_yaml/                # 21 YAML configuration files
├── meta_prompts/
│   └── master_prompt.txt     # USER-EDITABLE prompt control
└── create_audit_file.py      # Generates code audit

```

## Key Design Decisions

### 1. User Empowerment via master_prompt.txt
- **Problem Solved:** Prompts previously hard-coded in Python
- **Solution:** Editable text file for business stakeholder control
- **Format:** SYSTEM/TEMPERATURE/ROLE/PROMPT structure

### 2. Competitive Multi-Model Generation
- **Problem Solved:** Single model limitations and quality variance
- **Solution:** 3 models compete, best output selected
- **Implementation:** asyncio.gather() for parallel calls

### 3. 5-Tier Visual Hierarchy
- **Levels:** HUB → SECTION → DOCUMENT → LETTER → DIGITAL
- **Purpose:** Consistent luxury brand standards
- **Implementation:** visual_hierarchy.py module

## Critical Code Patterns

### Async Orchestration Pattern
```python
# Concurrent API calls to multiple models
responses = await asyncio.gather(
    call_claude(prompt),
    call_gpt4(prompt),
    call_gemini(prompt)
)
best = select_best_response(responses)
```

### Dynamic Prompt Loading
```python
# Load user-editable prompts at runtime
with open('master_prompt.txt') as f:
    prompts = parse_meta_prompts(f.read())
```

## Important Clarifications

### What's NOT in This Codebase
- ❌ Notion template deployment code (that's v3.8.x)
- ❌ Database management systems
- ❌ Hard-coded prompts in Python files
- ❌ Single-model generation

### What IS in This Codebase  
- ✅ 433 asset generation capability
- ✅ User-controlled prompt system
- ✅ Multi-model orchestration
- ✅ Emotional intelligence mapping
- ✅ Quality scoring and selection
