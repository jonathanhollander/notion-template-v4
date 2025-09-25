# Estate Planning Concierge v4.0 - QWEN Documentation

## Project Overview

The Estate Planning Concierge v4.0 is a comprehensive Notion workspace template deployment system that creates an integrated estate planning management system. This Python-based tool automates the creation of pages, databases, and content blocks in Notion, providing a structured approach to estate planning with professional design elements and premium functionality.

The system combines features from multiple AI implementations (ChatGPT, Gemini, Qwen, Claude, DeepSeek) into a unified deployment tool with:
- Validation-focused foundation with comprehensive error handling
- Phased deployment with progress tracking
- Interactive CLI interface
- Component-based architecture
- State management and recovery capabilities

## Key Features

- **Multi-tier Content Management**: Pages, databases, and content blocks for comprehensive estate planning
- **Premium Visual Design**: Professional themes and assets with a dignified aesthetic appropriate for estate planning
- **State Management**: Recovery capabilities to resume deployments after failures
- **Asset Generation**: Integrated image and icon generation system
- **Variable Substitution**: Environment variable injection in content
- **Formula Placeholders**: Support for dynamic formula expressions
- **Enhanced Select Options**: Support for both simple and color-enhanced select options
- **Rollup Properties**: Two-pass database creation to handle rollup dependencies
- **Unified Logging**: Color-coded logging system with API, LLM, Asset, Error, Trace, YAML, and Info prefixes

## Architecture

The system is organized into several key directories:

- `split_yaml/`: Contains the template structure split across multiple YAML files
- `asset_generation/`: Asset generation system with themes, models, and services
- `csv/`: Data seeding files for database population
- `modules/`: Reusable components and utilities
- `logs/`: Debug logging output (unified to single file)

## Building and Running

### Prerequisites
- Python 3.8+
- Notion API token with appropriate permissions
- Internet connection for API calls

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your NOTION_TOKEN and NOTION_PARENT_PAGEID
```

### Running the Deployment
```bash
# Test deployment (validate only)
python deploy.py --dry-run

# Full deployment
python deploy.py

# Interactive mode
python deploy.py --interactive

# Resume from checkpoint after failure
python deploy.py --resume

# Deploy only specific phase
python deploy.py --phase pages
```

### Debugging & Logs
All logs go to `logs/debug.log` with color-coded prefixes:
- **🟢 API** = Notion API calls/responses
- **🟤 LLM** = AI/LLM calls (Replicate, OpenAI, etc.)
- **🔵 ASSET** = Asset processing (icons, covers, page creation)
- **🔴 ERROR** = Errors, failures, warnings
- **🟣 TRACE** = Request tracing, correlation IDs
- **🟠 YAML** = Configuration file processing
- **⚫ INFO** = General information

## Development Conventions

- YAML files are processed in alphabetical order from the `split_yaml/` directory
- Parent-child page relationships are established using the `parent` field in YAML
- Variable substitution uses `${VARIABLE}` or `${VARIABLE:-default_value}` format
- Formula placeholders use `{{formula:expression}}` format
- The system handles Notion's 100-block limit per request by chunking content
- Rollup properties require a two-pass database creation approach due to relation dependencies

## File Structure

The system uses a modular approach with:
- YAML configuration files split by functionality (`00_admin_hub.yaml`, `01_pages_core.yaml`, etc.)
- Asset generation system with theme support
- Comprehensive logging and state management
- Integration with external asset hosting (GitHub raw content)

## Troubleshooting

When pages are created but no content appears:
1. Check API responses: `grep "🟢 API" logs/debug.log`
2. Check asset processing: `grep "🔵 ASSET" logs/debug.log`
3. Check for errors: `grep "🔴 ERROR" logs/debug.log`
4. Check YAML parsing: `grep "🟠 YAML" logs/debug.log`

The system automatically attempts to clear existing content before deployment to avoid archived content conflicts.

## Configuration

The system uses several environment variables:
- `NOTION_TOKEN`: Notion API integration token
- `NOTION_PARENT_PAGEID`: Target parent page ID for deployment
- `NOTION_VERSION`: API version (defaults to "2025-09-03")
- `THROTTLE_RPS`: Rate limit in requests per second (defaults to 2.5)
- `NOTION_TIMEOUT`: API request timeout (defaults to 25s)
- `RETRY_MAX`: Maximum retry attempts (defaults to 5)
- `RETRY_BACKOFF_BASE`: Backoff multiplier for retries (defaults to 1.5)

The visual configuration in `config.yaml` defines premium themes, emoji sets, and asset URLs appropriate for estate planning contexts.