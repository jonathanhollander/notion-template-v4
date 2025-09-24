# YAML Modifications Tracking

## Overview
This document tracks the specific modifications needed to existing YAML files to implement the 29 missing systems.

## Files Requiring Modification

### 1. `split_yaml/01_pages_core.yaml`
**Status:** ⏳ Pending
**Lines to Add:** ~190 lines
**Modifications:**
- Add toggle systems for estate planning guide
- Add nested toggles for financial organization
- Add interactive checklists with to_do blocks
- Reference: Tech Plan lines 33-222

### 2. `split_yaml/02_pages_extended.yaml`
**Status:** ⏳ Pending
**Lines to Add:** ~170 lines
**Modifications:**
- Add accordion systems for advanced strategies
- Add nested toggles for trust structures
- Add business succession planning toggles
- Reference: Tech Plan lines 229-398

### 3. `split_yaml/25_help_system.yaml`
**Status:** ⏳ Pending
**Lines to Add:** ~280 lines
**Modifications:**
- Complete replacement with progressive disclosure system
- Add step-by-step task workflows
- Add interactive help center with toggles
- Reference: Tech Plan lines 403-682, 970-1249

### 4. `split_yaml/06_financial_accounts.yaml`
**Status:** ⏳ Pending
**Lines to Add:** ~150 lines
**Modifications:**
- Add contextual help formulas to databases
- Add synchronized formulas for account health
- Add risk assessment calculations
- Reference: Tech Plan lines 693-965, 1602-1626

### 5. `split_yaml/07_property_assets.yaml`
**Status:** ⏳ Pending
**Lines to Add:** ~50 lines
**Modifications:**
- Add equity calculation formulas
- Add estate significance formulas
- Add tax implication formulas
- Reference: Tech Plan lines 1627-1680

## New Files Created

### 1. `split_yaml/26_progress_visualizations.yaml`
**Status:** ✅ Created (placeholder)
**Full Implementation:** Tech Plan lines 1687-2172
- Progress dashboard with ASCII charts
- Milestone tracking system
- Achievement history tables

### 2. `split_yaml/28_analytics_dashboard.yaml`
**Status:** ✅ Created (partial)
**Full Implementation:** Tech Plan lines 1254-1596
- Cross-database rollup systems
- Real-time activity timeline
- Smart recommendations engine

## Implementation Priority

1. **Critical** - Fix existing broken systems first
   - `25_help_system.yaml` - Currently minimal, needs complete overhaul

2. **High** - Add interactive content
   - `01_pages_core.yaml` - Toggle systems
   - `02_pages_extended.yaml` - Accordion content

3. **Medium** - Add guidance systems
   - `06_financial_accounts.yaml` - Contextual help

4. **Low** - Enhance with formulas
   - `07_property_assets.yaml` - Calculation formulas

## Validation Commands

After each modification, validate with:
```bash
# Check syntax
python3 -c "import yaml; yaml.safe_load(open('split_yaml/FILE.yaml', 'r'))"

# Check for required patterns
grep -c "toggle" split_yaml/01_pages_core.yaml  # Should be > 5
grep -c "formula" split_yaml/06_financial_accounts.yaml  # Should be > 8
```

## Rollback Plan

If modifications cause issues:
1. Git diff to review changes: `git diff split_yaml/`
2. Restore specific file: `git checkout -- split_yaml/FILE.yaml`
3. Restore all YAMLs: `git checkout -- split_yaml/*.yaml`

## Notes for Developers

- **Indentation:** Always use 2 spaces, never tabs
- **Testing:** Use `--dry-run` flag when testing deploy.py
- **Formulas:** Test complex formulas in Notion UI first
- **Toggles:** Children blocks must be properly nested
- **Validation:** Run `./validate_complete_implementation.sh` after each phase

## Tracking Progress

- [ ] Phase 1: Interactive Content (0/15 systems)
- [ ] Phase 2: Guidance Systems (0/12 systems)
- [ ] Phase 3: Database Systems (0/8 systems)
- [ ] Phase 4: Dashboard Systems (2/2 files created, 0/2 fully implemented)

Total: 2/37 systems ready (5.4% complete)