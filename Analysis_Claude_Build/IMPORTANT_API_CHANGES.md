# Important Notion API Changes - August 2025

## Critical Updates

### 1. API Version
- **Current Version:** `2025-09-03`
- **Previous Version:** `2024-05-22`
- The deploy.py has been updated to use the latest version

### 2. Token Format Change
- **New Format:** Tokens now use `ntn_` prefix
- **Old Format:** Previously used `secret_` prefix
- **Migration Date:** September 25, 2024
- Both formats are currently supported but new tokens use `ntn_`

### 3. Multi-Source Databases (New Feature)
- Starting September 3, 2025, Notion supports multi-source databases
- Separates "databases" (containers) from "data sources" (tables)
- This enables more powerful organizational capabilities

### 4. Authentication Updates
- OAuth 2.0 is now the recommended authentication method
- Basic authentication still supported for internal integrations
- Refresh tokens are available for long-lived sessions

### 5. New Features Available
- Equation blocks support (add, retrieve, update)
- Enhanced embed, bookmark, and media block types
- Link preview APIs for dynamic content
- Offline mode support (as of Notion 2.53)
- Model Context Protocol (MCP) server for AI tools

## Environment Variables

```bash
# Token format (use either old or new prefix)
export NOTION_TOKEN="ntn_your_token_here"  # New format
# OR
export NOTION_TOKEN="secret_your_token_here"  # Old format (still works)

# API Version (automatically set to latest)
export NOTION_VERSION="2025-09-03"

# Parent page ID (unchanged)
export NOTION_PARENT_PAGEID="your_parent_page_id"
```

## OAuth Configuration (if using OAuth)

```bash
export OAUTH_CLIENT_ID="your_client_id"
export OAUTH_CLIENT_SECRET="your_client_secret"
export NOTION_AUTH_URL="https://api.notion.com/v1/oauth/authorize"
```

## Testing the Updates

```bash
# Test with the updated API version
cd deploy
python deploy.py --dry-run

# Verify API version in headers
python -c "import os; print(f'Using Notion API: {os.getenv(\"NOTION_VERSION\", \"2025-09-03\")}')"
```

## Backward Compatibility

The current implementation maintains backward compatibility:
- Old token format (`secret_`) still works
- API calls are updated to latest endpoints
- All existing YAML configurations remain valid

## References
- [Notion API Changelog](https://developers.notion.com/page/changelog)
- [API Version Migration Guide](https://developers.notion.com/docs/versioning)
- [Authorization Documentation](https://developers.notion.com/docs/authorization)