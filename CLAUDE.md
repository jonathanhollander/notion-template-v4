# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains two distinct Notion template deployment projects:

### 1. Legacy v3.8x Recovery Project
- **Location:** `/unpacked-zips/`, `/forensic-findings/`
- **Status:** Documented incident - developer deleted 1,067 lines instead of fixing syntax error
- **Recovery Path:** Fix line 82 in `unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/deploy.py`

### 2. Estate Planning v4.0 Production System (ACTIVE)
- **Location:** `/Notion_Template_v4.0_Production/`
- **Status:** ✅ COMPLETE and FUNCTIONAL with web interface
- **Purpose:** Notion workspace deployment with AI-powered asset generation

## ⚠️ Critical Restrictions

**ASSET GENERATION LIMITS:**
- **NEVER run full generation (490 images)** - costs ~$20 in Replicate API credits
- **ALWAYS use test mode** (3 images max) for development
- Test via web: Click "Start Test Generation (3 Images)" button
- Test via CLI: `python asset_generator.py --test-pages 3`
- Full production runs require explicit user authorization

## Common Development Tasks

### Quick Start - Web Interface (Recommended)
```bash
cd Notion_Template_v4.0_Production/asset_generation
python3 review_dashboard.py
# Opens browser at http://localhost:4500
```

### Testing Commands
```bash
# Test deployment readiness
cd Notion_Template_v4.0_Production
python test_deployment_requirements.py
python validate_deployment_ready.py

# Test YAML configuration
python test_full_discovery.py

# Test asset generation (web)
cd asset_generation
python test_websocket_connection.py
python test_buttons_functional.py
```

### Deployment Workflow
```bash
# 1. Dry run (no API calls)
python deploy.py --dry-run --verbose

# 2. Test deployment (3 sample assets)
python deploy.py --test --generate-assets --test-pages 3

# 3. Full deployment (requires authorization)
python deploy.py --generate-assets --parent-id=$NOTION_PARENT_PAGEID
```

### Environment Setup
```bash
# Required environment variables (.env file)
NOTION_TOKEN="your_notion_integration_token"
NOTION_PARENT_PAGEID="your_parent_page_id"
REPLICATE_API_TOKEN="your_replicate_api_key"

# Optional for enhanced features
OPENROUTER_API_KEY="your_openrouter_api_key"

# Install dependencies
pip install -r requirements.txt
pip install -r asset_generation/requirements.txt
```

### Code Quality
```bash
# Format code
black deploy.py asset_generation/*.py

# Run linter
ruff check deploy.py asset_generation/*.py
```

## Debugging & Monitoring

### Unified Color-Coded Logging
All logs consolidated in `logs/debug.log` with color codes:
- **🟢 API** - Notion API calls/responses
- **🟤 LLM** - AI/LLM calls (Replicate, OpenRouter)
- **🔵 ASSET** - Asset processing (icons, covers)
- **🔴 ERROR** - Errors, failures, warnings
- **🟣 TRACE** - Request tracing, correlation IDs
- **🟠 YAML** - Configuration file processing
- **⚫ INFO** - General information

**Debug Commands:**
```bash
# View all logs
cat logs/debug.log

# Monitor real-time
tail -f logs/debug.log

# Filter by type
grep "🟢 API" logs/debug.log     # API calls only
grep "🔴 ERROR" logs/debug.log   # Errors only
```

## Architecture Overview

### Core Components

1. **Deployment System** (`deploy.py`)
   - 192KB, 4000+ lines orchestrating Notion workspace creation
   - Integrates asset generation via `--generate-assets`
   - Rate limiting: 2.5 requests/second
   - Idempotency through marker strings

2. **Asset Generation** (`asset_generation/`)
   - `review_dashboard.py` - Web interface (port 4500)
   - `asset_generator.py` - Core generator with budget controls
   - `emotional_elements.py` - 32KB emotional intelligence engine
   - `quality_scorer.py` - Multi-model quality evaluation
   - `openrouter_orchestrator.py` - Model competition system

3. **Configuration** (`split_yaml/`)
   - 21 YAML files defining Notion structure
   - Single source of truth for deployment
   - Dynamic prompt generation from metadata

### Key Design Patterns
- **Two-Stage Workflow:** Sample → Review → Production
- **Approval Gates:** Human review at port 4500
- **Cost Controls:** $0.50 samples, $8.00 production
- **Real-time Updates:** WebSocket broadcasts
- **Comprehensive Logging:** Unified debug.log

## File Organization
```
Notion_Template_v4.0_Production/
├── deploy.py                    # Main deployment orchestrator
├── asset_generation/            # Asset generation system
│   ├── review_dashboard.py      # Web server (port 4500)
│   ├── asset_generator.py       # Core generator
│   ├── templates/               # HTML templates
│   ├── static/                  # JS/CSS for web UI
│   └── output/                  # Generated assets
├── split_yaml/                  # 21 YAML configuration files
│   ├── 01_pages_core.yaml      # Core page definitions
│   ├── 04_databases.yaml       # Database structures
│   └── [more YAML files]
├── logs/                        # Execution logs
│   └── debug.log               # Unified debug log
└── assets/                      # Static assets

```

## Technical Requirements
- **Python:** 3.8+ (async functionality required)
- **Notion API:** Version `2022-06-28` (consider updating)
- **Libraries:** Flask-SocketIO, asyncio, aiohttp
- **Database:** SQLite for session tracking

## Common Issues & Solutions

### Asset Generation Fails
- Check `REPLICATE_API_TOKEN` is set
- Verify budget limits in `asset_generation/config.json`
- Review logs: `grep "🔴 ERROR" logs/debug.log`

### Deployment Rate Limiting
- Default: 2.5 requests/second
- Adjust in `deploy.py` if hitting limits
- Monitor: `grep "429" logs/debug.log`

### WebSocket Connection Issues
- Verify port 4500 is available
- Check: `python test_websocket_connection.py`
- Browser console should show "Connected to WebSocket"

## MCP Server Integration
Configure in `.mcp.json`:
- `task-master-ai` - Task management
- `notion` - API operations
- `zen` - Multi-model analysis
- `filesystem` - Enhanced file operations

## Important Notes
- Asset generation uses dynamic meta-prompting from YAML
- Web interface auto-refreshes every 30 seconds
- Quality scores stored in `quality_evaluation_results.json`
- All assets saved with metadata in SQLite database
- Comprehensive audit logs at `estate_planning_v4_code_audit.txt`
- Idempotency maintained through content marker strings