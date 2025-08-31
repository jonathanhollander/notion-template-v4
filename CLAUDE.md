# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a forensic analysis project investigating a failed Notion template deployment system (v3.83). The project contains evidence of deliberate code destruction where a developer destroyed 1,067 lines of working code rather than fix a trivial syntax error.

## Critical Context

**The Fatal Error:** Line 82 in `unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/deploy.py`
```python
def req(')  # Missing closing parenthesis - 30-second fix that broke everything
```

## Key Recovery Files

### Working Code (v3.8.2) - 85% Salvageable
- **Main Script:** `unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/deploy.py` (1,067 lines)
- **Configuration:** `unpacked-zips/legacy_concierge_gold_v3_8_2/split_yaml/*.yaml` (21 YAML files)
- **Data:** `unpacked-zips/legacy_concierge_gold_v3_8_2/csv/*.csv` (7 CSV files)

### Environment Setup
```bash
# Fix the syntax error first
sed -i "82s/def req(')/def req(/" unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/deploy.py

# Install dependencies
pip install requests PyYAML

# Set environment variables
export NOTION_TOKEN="your_token_here"
export NOTION_PARENT_PAGEID="your_page_id_here"
```

## Project Structure

```
Notion Template/
├── unpacked-zips/                 # 83 ZIP archives of project evolution
│   ├── legacy_concierge_gold_v3_8_2/  # WORKING VERSION (with syntax error)
│   │   ├── deploy/
│   │   │   ├── deploy.py         # Main script (fix line 82!)
│   │   │   └── requirements.txt  # requests, PyYAML
│   │   ├── split_yaml/           # 21 YAML configuration files
│   │   └── csv/                  # 7 CSV data files
│   ├── legacy_concierge_gold_v3_8_3/  # Deceptive 8-line stub
│   └── v3.83_Gold_Notion_Template/    # Empty fraud (0 Python files)
├── forensic-findings/            # Original forensic analysis
├── zen-forensic-findings/        # Multi-model AI analysis
└── .taskmaster/                  # Task management system

```

## Recovery Commands

```bash
# Phase 0: Immediate fix (30 minutes)
cd unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/
python deploy.py --dry-run  # Test after fixing syntax error

# Phase 1: Quick wins (Day 1-3)
# Remove duplicate functions (url_join defined 3 times)
# Extract magic strings to constants.py
# Add error handling to main()

# Testing deployment
python deploy.py --test --parent-id=$NOTION_PARENT_PAGEID
```

## Technical Debt Metrics

- **Cyclomatic Complexity:** 287 (should be <10)
- **Code Duplication:** 18% (url_join defined 3 times at lines 60, 477, 700)
- **Test Coverage:** 0% (no tests exist)
- **Architecture Score:** 3/10 (monolithic anti-pattern)
- **Code Smells:** 15+ identified

## Key API Details

- **Notion API Version:** Update from `2022-06-28` to `2024-05-22`
- **Rate Limiting:** Exponential backoff implemented in `_throttle()`
- **Idempotency:** Uses marker strings (fragile, needs improvement)

## Task Management Integration

This project uses Task Master AI for tracking recovery tasks. Import Task Master's commands:
@./.taskmaster/CLAUDE.md

### Current Recovery Plan
1. **Phase 0:** Fix syntax error (30 minutes)
2. **Phase 1:** Stabilization (3 days)
3. **Phase 2:** Modularization (1 week)
4. **Phase 3:** Production hardening (1 week)
5. **Phase 4:** Advanced features (1-2 weeks)

## Forensic Evidence Files

### Analysis Reports
- `EXECUTIVE_SUMMARY_MULTI_MODEL_CONSENSUS.md` - Multi-AI verdict
- `FINAL_VERDICT_AND_RECOVERY_PLAN.md` - Complete recovery roadmap
- `forensic_analysis_complete.json` - Structured findings data

### Version Regression Evidence
- **v3.8.2:** 1,067 lines (working with 1 error)
- **v3.8.3:** 8 lines (deceptive stub)
- **v3.83:** 0 lines (complete fraud)

## Important Notes

1. **Never trust v3.83** - it contains NO working code
2. **Start with v3.8.2** - it's 85% functional after fixing line 82
3. **YAML configs are intact** - all 21 configuration files are valid
4. **Notion API version** needs updating from 2022 to 2024
5. **Recovery is 100% achievable** - estimated 3-5 weeks to production

## MCP Server Configuration

The project has extensive MCP server support configured in `.mcp.json` including:
- task-master-ai (task management)
- codebase-rag (semantic code search)
- mcp-code-graph (dependency analysis)
- zen (multi-model AI analysis)
- notion (API integration)
- github (version control)
- filesystem (enhanced file operations)

## Session History

### Session: August 30, 2025
- **Started:** 17:04 EDT
- **Goal:** Awaiting user input for session objectives
- **Status:** Session initialized, ready for task assignment