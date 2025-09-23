# IG-LATEST-Newest Build
## Estate Planning v4.0 Image Generation System

### Migration Completed: 2025-09-06 22:21 EDT

This directory contains the complete, standalone Image Generation system extracted from the Estate Planning v4.0 project. All dependencies and required files have been carefully migrated and verified.

## Migration Summary

✅ **Successfully Migrated: 110 Total Files**
- 9 Core Python modules
- 19 Utility modules  
- 5 HTML templates
- 25 Static assets (CSS/JS/libraries)
- 3 Meta prompt files
- 36 YAML configuration files
- 5 JSON configuration files
- 6 Database files
- 2 Documentation files

## Quick Start

### 1. Setup Environment
```bash
# Install dependencies
pip3 install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys:
# - REPLICATE_API_TOKEN (required)
# - OPENROUTER_API_KEY (required)
```

### 2. Launch Web Interface
```bash
python3 review_dashboard.py
# Opens browser at http://localhost:4500
```

### 3. Test Generation (3 images only)
```bash
python3 asset_generator.py --test-pages 3
```

## System Architecture

### Core Components
- `asset_generator.py` - Main generation orchestrator
- `review_dashboard.py` - Web interface (Flask + WebSocket)
- `openrouter_orchestrator.py` - Multi-model prompt competition
- `websocket_broadcaster.py` - Real-time status updates
- `emotional_elements.py` - 32KB emotional intelligence engine
- `quality_scorer.py` - Multi-criteria evaluation system

### Key Features
- **Web-Based Editor**: Edit master prompts via browser
- **Real-Time Updates**: WebSocket streaming of generation status
- **Multi-Model Competition**: Claude vs GPT-4 vs Gemini prompts
- **Dynamic Scoring**: Content-based quality evaluation
- **Budget Controls**: Strict cost limits ($0.50 test, $8.00 production)

## Directory Structure
```
IG-LATEST-Newest Build/
├── Core Python Files (9)
├── utils/ (19 modules)
├── templates/ (5 HTML)
├── static/
│   ├── css/ (styles)
│   ├── js/ (dashboard.js + libraries)
│   └── lib/ (Bootstrap, Socket.IO)
├── meta_prompts/ (3 master prompts)
├── split_yaml/ (36 YAML configs)
├── db/ (SQLite databases)
├── output/ (generated images)
└── logs/ (execution logs)
```

## Web Interface URLs
- **Dashboard**: http://localhost:4500
- **Master Prompt Editor**: http://localhost:4500/edit-master-prompt
- **Emotional Config**: http://localhost:4500/emotional-config
- **API Status**: http://localhost:4500/api/status

## Testing Commands

### Web Interface Test
```bash
# Start server
python3 review_dashboard.py

# In browser:
# 1. Click "Start Test Generation (3 Images)"
# 2. Watch real-time progress
# 3. Review generated images
```

### CLI Test
```bash
# Test with 3 pages
python3 asset_generator.py --test-pages 3

# Dry run (no actual generation)
python3 asset_generator.py --dry-run

# Test specific functionality
python3 test_generate_samples.py
```

## Production Warning

⚠️ **NEVER run full generation (490 images)**
- Costs approximately $20 in API fees
- Takes 2-3 hours to complete
- Must be explicitly initiated by user

## API Requirements
- **REPLICATE_API_TOKEN**: For image generation
- **OPENROUTER_API_KEY**: For multi-model prompts
- Optional: Individual model API keys

## Key Files Migrated

### Python Core (9 files)
1. asset_generator.py - Main controller
2. review_dashboard.py - Web server
3. openrouter_orchestrator.py - Model orchestration
4. websocket_broadcaster.py - Real-time updates
5. prompt_templates.py - Prompt structures
6. emotional_elements.py - Emotional AI
7. quality_scorer.py - Scoring system
8. generate_real_evaluations.py - Dynamic scoring
9. test_generate_samples.py - Testing suite

### Configuration Files
- config.json - Main configuration
- quality_evaluation_results.json - Scoring data
- test_generation_summary.json - Test results
- test_sample_competitions.json - Model competitions
- requirements.txt - Python dependencies
- .env.example - Environment template

### YAML Configurations (36 files)
Complete Notion template structure from 01_pages_core.yaml to 36_tags.yaml

## Migration Verification
Total files verified: 110
All critical dependencies included
No missing imports or modules
Ready for standalone deployment

## Support Files
- MIGRATION_REPORT.md - Detailed migration log
- README.md - This documentation

---
*Migration completed successfully by Estate Planning v4.0 Asset Generation System*
*Build Date: 2025-09-06 22:21 EDT*