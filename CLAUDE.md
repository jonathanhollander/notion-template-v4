# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains two major projects related to Notion template deployment:

### 1. Legacy v3.8x Recovery Project (forensic analysis)
- **Location:** `/unpacked-zips/`, `/forensic-findings/`
- **Status:** Documented code destruction incident - developer deleted 1,067 lines rather than fix syntax error
- **Recovery:** Start with `unpacked-zips/legacy_concierge_gold_v3_8_2/deploy/deploy.py` (fix line 82)

### 2. Estate Planning v4.0 Production System (ACTIVE)
- **Location:** `/Notion_Template_v4.0_Production/`
- **Status:** COMPLETE and FUNCTIONAL with web interface
- **Primary Focus:** Asset generation system for Notion pages

## Critical Restrictions

⚠️ **ASSET GENERATION LIMITS:**
- **NEVER run full generation (490 images)** - costs ~$20 in Replicate API credits
- **ALWAYS use test mode** (3 images max) for development
- Test via web: Click "Start Test Generation (3 Images)" button
- Test via CLI: `python asset_generator.py --test-pages 3`
- Full production runs must be explicitly authorized by user

## Common Development Tasks

### Starting the Web Interface (Recommended)
```bash
cd Notion_Template_v4.0_Production/asset_generation
python3 review_dashboard.py
# Auto-opens browser at http://localhost:4500
```

### Running Tests
```bash
# Test deployment requirements
cd Notion_Template_v4.0_Production
python test_deployment_requirements.py

# Test YAML discovery
python test_full_discovery.py

# Validate deployment readiness
python validate_deployment_ready.py

# Test asset generation (web interface)
cd asset_generation
python test_websocket_connection.py
python test_buttons_functional.py
```

### Deployment Commands
```bash
# Dry run (no API calls)
python deploy.py --dry-run --verbose

# Test deployment with sample assets
python deploy.py --test --generate-assets --test-pages 3

# Full deployment (requires user authorization)
python deploy.py --generate-assets --parent-id=$NOTION_PARENT_PAGEID
```

### Environment Setup
```bash
# Required environment variables
export NOTION_TOKEN="your_notion_integration_token"
export NOTION_PARENT_PAGEID="your_parent_page_id"
export REPLICATE_API_TOKEN="your_replicate_api_key"
export OPENROUTER_API_KEY="your_openrouter_api_key"  # Optional

# Install dependencies
pip install -r requirements.txt
pip install -r asset_generation/requirements.txt
```

### Linting and Code Quality
```bash
# Format code
black deploy.py asset_generation/*.py

# Run linter
ruff check deploy.py asset_generation/*.py
```

## Architecture & Key Components

### Core Systems

1. **Deployment System** (`deploy.py`)
   - 4000+ lines orchestrating Notion workspace creation
   - Integrates with asset generation via `--generate-assets`
   - Rate limiting: 2.5 requests/second (configurable)
   - Idempotency through marker strings

2. **Asset Generation** (`asset_generation/`)
   - **Web Interface:** `review_dashboard.py` (WebSocket real-time updates)
   - **Core Generator:** `asset_generator.py` (budget controls, parallel processing)
   - **AI Enhancement:** `emotional_elements.py` (32KB emotional intelligence)
   - **Quality Scoring:** `quality_scorer.py` (multi-model evaluation)
   - **Orchestration:** `openrouter_orchestrator.py` (model competition system)

3. **Configuration** (`split_yaml/`)
   - 21 YAML files defining complete Notion structure
   - Single source of truth for deployment and assets
   - Dynamic prompt generation from metadata

### Key Design Patterns

- **Two-Stage Workflow:** Sample generation → Human review → Mass production
- **Approval Gates:** Web interface at port 4500 for asset review
- **Cost Controls:** Strict budgets ($0.50 samples, $8.00 production)
- **Real-time Monitoring:** WebSocket broadcasts for live status updates
- **Comprehensive Logging:** All operations logged to `logs/` directory

## File Organization

```
Notion Template/
├── .taskmaster/                         # Task management system
│   └── tasks/tasks.json                # Current task tracking
├── Notion_Template_v4.0_Production/    # Active production system
│   ├── deploy.py                       # Main deployment orchestrator
│   ├── asset_generation/               # Asset generation system
│   │   ├── review_dashboard.py         # Web server (port 4500)
│   │   ├── asset_generator.py          # Core generator with budgets
│   │   ├── templates/                  # HTML templates
│   │   ├── static/                     # JS/CSS for web UI
│   │   └── output/                     # Generated assets
│   ├── split_yaml/                     # 21 YAML configuration files
│   └── logs/                           # Execution logs
└── unpacked-zips/                      # Legacy v3.8x recovery files
```

## Key Technical Details

- **Python Version:** 3.8+ required (async functionality)
- **Notion API:** Update from `2022-06-28` to `2024-05-22`
- **WebSocket:** Real-time updates via Flask-SocketIO
- **Database:** SQLite for asset tracking (`review_sessions.db`)
- **Parallel Processing:** asyncio for concurrent asset generation
- **Error Handling:** Exponential backoff, comprehensive retry logic

## MCP Server Integration

Extensive MCP support via `.mcp.json`:
- `task-master-ai` - Task management
- `codebase-rag` - Semantic code search
- `zen` - Multi-model AI analysis
- `notion` - API operations
- `filesystem` - Enhanced file operations
- `mcp-code-graph` - Dependency analysis

## Important Notes

- Asset generation uses dynamic meta-prompting from YAML metadata
- Web interface auto-refreshes every 30 seconds during generation
- Quality scores stored in `quality_evaluation_results.json`
- All generated assets saved with metadata in SQLite database
- Comprehensive audit logs available at `estate_planning_v4_code_audit.txt`