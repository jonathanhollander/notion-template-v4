# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Estate Planning Concierge v4.0 - Two major systems in this repository:

### 1. ✅ WORKING: Web-Based Image Generation System
**Status**: COMPLETE and FUNCTIONAL (2025-09-03)
- **Location**: `/asset_generation/` directory  
- **Access**: http://localhost:4500 (auto-opens on start)
- **Features**:
  - Edit master prompt in web browser (no CLI needed)
  - One-click "GO" button for generation
  - Real-time WebSocket status updates
  - Live log streaming during generation
  - Progress bars and cost tracking

**Key Files**:
- `asset_generation/review_dashboard.py` - Web server (lines 764-1073)
- `asset_generation/websocket_broadcaster.py` - Real-time updates
- `asset_generation/templates/master_prompt_editor.html` - Editor UI
- `asset_generation/static/js/dashboard.js` - Client WebSocket (lines 537-724)

### 2. 🚀 PLANNED: IMAGE FORGE Platform Evolution
**Status**: Vision documented, ready for implementation
- Evolution of Estate Planning v4.0 into multi-industry platform
- 80% code reuse from current system
- Core differentiator: 32KB emotional intelligence engine
- 7-phase roadmap to $1M+ MRR

**Documentation**:
- `UNIFIED_SYSTEM_DOCUMENTATION.md` - Complete system overview
- `IMAGE_FORGE_COMPLETE_VISION.md` - Platform roadmap
- `WEB_SYSTEM_COMPLETE_DOCUMENTATION.md` - Web implementation details

## Critical Restrictions

**⚠️ ASSET GENERATION LIMITS:**
- **NEVER run full generation (490 images)** - costs ~$20
- **ALWAYS use test mode** (3 images max) for development
- Test via web: Click "Start Test Generation (3 Images)" button
- Test via CLI: `python asset_generator.py --test-pages 3`
- Full production: FORBIDDEN for Claude - user must explicitly run

## Key Commands

### Web Interface (RECOMMENDED)
```bash
# Start web server (auto-opens browser)
cd asset_generation
python3 review_dashboard.py

# Access URLs:
# Dashboard: http://localhost:4500
# Editor: http://localhost:4500/edit-master-prompt
```

### Testing Commands
```bash
# Test web system (3 images only)
# 1. Start server: python3 review_dashboard.py
# 2. Click "Start Test Generation (3 Images)"

# Test via CLI (if needed)
cd asset_generation
python3 asset_generator.py --test-pages 3

# Check WebSocket connection
# Open browser console, should see "Connected to WebSocket"
```

### Environment Setup
```bash
# Required for operation
export REPLICATE_API_TOKEN="your_token"
export OPENROUTER_API_KEY="your_key"

# Install dependencies
pip3 install flask flask-cors flask-socketio flask-limiter
```

## Architecture & Structure

### Core Components

1. **deploy.py** (192KB, 4000+ lines)
   - Main deployment orchestrator
   - Handles YAML parsing, Notion API calls, progress tracking
   - Integrates with asset generation system via `--generate-assets` flag
   - Contains rate limiting, retry logic, and comprehensive error handling

2. **Asset Generation System** (`asset_generation/`)
   - `asset_generator.py` - Main generation controller with budget limits
   - `review_server.py` - Web interface for asset approval (port 4500)
   - `emotional_elements.py` - Emotional intelligence prompt enhancement
   - `quality_scorer.py` - Multi-model quality assessment
   - `openrouter_orchestrator.py` - Multi-model prompt competition system

3. **Configuration** (`split_yaml/`)
   - 21 YAML files defining complete Notion workspace structure
   - Dynamically drives both deployment and asset generation
   - Single source of truth for all page content and structure

### Key Design Patterns

- **Dynamic Meta-Prompting**: Asset prompts generated from YAML metadata
- **Two-Stage Generation**: Sample → Review → Mass Production workflow
- **Approval Gates**: Human review required before production generation
- **Cost Controls**: Strict budget limits ($0.50 samples, $8.00 production)
- **Comprehensive Logging**: Real-time status, costs, progress tracking

## Environment Setup

Required environment variables (create `.env` from `.env.example`):
```bash
# Required for Notion deployment
NOTION_TOKEN=your_notion_integration_token
NOTION_PARENT_PAGEID=your_parent_page_id

# Required for asset generation
REPLICATE_API_KEY=your_replicate_api_key

# Optional for enhanced features
OPENROUTER_API_KEY=your_openrouter_api_key
```

## File Organization

```
Notion_Template_v4.0_Production/
├── deploy.py                    # Main deployment script
├── asset_generation/            # Asset generation system
│   ├── asset_generator.py      # Main generator
│   ├── review_server.py        # Web review interface
│   ├── config.json             # Generation configuration
│   └── output/                 # Generated assets
├── split_yaml/                  # Notion structure configuration
│   ├── 01_pages_core.yaml     # Core pages definition
│   ├── 02_pages_extended.yaml # Extended pages
│   └── [19 more YAML files]
├── logs/                        # Execution logs
└── validation/                  # Test and validation scripts
```

## Testing Approach

The project uses functional testing through validation scripts rather than unit tests:
- `test_deployment_requirements.py` - Validates environment and dependencies
- `validate_deployment_ready.py` - Checks deployment prerequisites
- `test_full_discovery.py` - Tests YAML discovery and parsing
- Manual testing via `--dry-run` flag to simulate without API calls

## Asset Generation Integration

The system automatically:
1. Discovers pages needing assets from YAML files
2. Generates intelligent prompts based on page titles/descriptions
3. Creates samples for review (8 items, ~$0.25)
4. Launches web review interface on port 4500
5. Waits for human approval
6. Generates full asset set after approval (~255 items, ~$8.00)

## Common Development Tasks

### Adding New Pages
1. Edit appropriate YAML file in `split_yaml/`
2. Add `icon_file` and/or `cover_file` properties if assets needed
3. Run `python test_full_discovery.py` to validate
4. Deploy with `python deploy.py --dry-run` first

### Modifying Asset Prompts
Edit prompt templates in:
- `asset_generation/prompt_templates.py` - Base prompt structures
- `asset_generation/emotional_elements.py` - Emotional enhancement layers

### Debugging Deployment Issues
1. Check logs in `logs/deployment.log`
2. Use `--verbose --verbose` for detailed output
3. Use `--dry-run` to test without API calls
4. Validate with `python validate_deployment_ready.py`

## Important Notes

- The project requires Python 3.8+ for async functionality
- Asset generation uses asyncio for parallel processing
- Notion API version should be updated from `2022-06-28` to latest
- Rate limiting is set to 2.5 requests/second by default
- The system maintains idempotency through marker strings in content