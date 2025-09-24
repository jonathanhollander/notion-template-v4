# Estate Planning Concierge v4.0

Complete Notion workspace template deployment system with unified color-coded logging.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your NOTION_TOKEN and NOTION_PARENT_PAGEID

# Test deployment
python deploy.py --dry-run

# Full deployment
python deploy.py
```

## Debugging & Logs

**All logs go to ONE file**: `logs/debug.log` with color-coded prefixes:

- **🟢 API** = Notion API calls/responses
- **🟤 LLM** = AI/LLM calls (Replicate, OpenAI, etc.)
- **🔵 ASSET** = Asset processing (icons, covers, page creation)
- **🔴 ERROR** = Errors, failures, warnings
- **🟣 TRACE** = Request tracing, correlation IDs
- **🟠 YAML** = Configuration file processing
- **⚫ INFO** = General information

### View Logs

```bash
# View all logs
cat logs/debug.log

# Monitor in real-time
tail -f logs/debug.log

# Check API calls only
grep "🟢 API" logs/debug.log

# Check for errors
grep "🔴 ERROR" logs/debug.log
```

## Troubleshooting Assets Not Appearing

When pages are created but no content appears:

1. **Check API responses**: `grep "🟢 API" logs/debug.log`
2. **Check asset processing**: `grep "🔵 ASSET" logs/debug.log`
3. **Check errors**: `grep "🔴 ERROR" logs/debug.log`
4. **Check YAML parsing**: `grep "🟠 YAML" logs/debug.log`

## Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment instructions
- **[CLAUDE.md](CLAUDE.md)** - Claude Code integration guide
- **[DEBUG_LOGGING_GUIDE.md](DEBUG_LOGGING_GUIDE.md)** - Advanced logging features

## System Requirements

- Python 3.8+
- Notion API token
- Internet connection for API calls