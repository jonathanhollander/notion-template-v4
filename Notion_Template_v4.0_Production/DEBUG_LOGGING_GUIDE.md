# Enhanced Debug Logging Guide

## Overview

The deployment system now includes comprehensive debug logging to help troubleshoot issues with Notion API calls and asset deployment. This system provides detailed visibility into every request, response, and asset processing step.

## Quick Start

### 1. Enable API Debugging (Recommended)
```bash
python debug_deploy.py --debug-api --dry-run
```
This logs every API request and response to `logs/deploy_debug_api.log` in JSON format.

### 2. Enable Full Debugging
```bash
python debug_deploy.py --debug-all --dry-run
```
This enables all debugging options and creates multiple specialized log files.

### 3. View Debug Logs
```bash
python debug_deploy.py --show-logs
```
Shows recent entries from all debug log files.

## Debug Options

| Flag | Description | Log File |
|------|-------------|----------|
| `--debug-api` | API requests/responses | `logs/deploy_debug_api.log` |
| `--debug-assets` | Asset processing pipeline | `logs/deploy_debug_assets.log` |
| `--trace-requests` | Request correlation tracing | `logs/deploy_debug_trace.log` |
| `--debug-all` | All of the above | Multiple files |

## Log Files Explained

### 1. `logs/deploy_debug_api.log` (JSON Format)
**Purpose**: Complete API request/response logging
**Format**: One JSON object per line
**Contains**:
- Full request details (method, URL, headers, payload)
- Complete response data (status, headers, body)
- Request timing and correlation IDs
- Sanitized sensitive information

**Example Entry**:
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "DEBUG",
  "correlation_id": "abc12345",
  "type": "api_request",
  "method": "POST",
  "url": "https://api.notion.com/v1/pages",
  "payload_size": 1234,
  "has_files": false
}
```

### 2. `logs/deploy_debug_assets.log`
**Purpose**: Asset deployment pipeline tracking
**Contains**:
- Page processing progress
- Block creation details with content previews
- YAML section processing
- Asset file handling (icons, covers)
- Content transformations

**Example Entry**:
```
2024-01-15 10:30:45 - Processing page: 'Estate Overview' (15 blocks)
2024-01-15 10:30:46 - ✓ Created heading_1 block: Estate Planning Concierge Overview
2024-01-15 10:30:46 - ✓ Created paragraph block: Welcome to your comprehensive estate planning...
2024-01-15 10:30:47 - ✓ Processed icon: /assets/estate-overview-icon.png
```

### 3. `logs/deploy_debug_trace.log`
**Purpose**: Request correlation and tracing
**Contains**:
- Request/response pairs with correlation IDs
- Timing information
- Success/failure status

**Example Entry**:
```
2024-01-15 10:30:45 - [abc12345] → POST https://api.notion.com/v1/pages
2024-01-15 10:30:46 - [abc12345] ← 201 (0.85s) ✓
```

### 4. `logs/deploy_errors.log`
**Purpose**: All errors with full context
**Contains**:
- Error messages with stack traces
- Failed API calls with full request/response details
- Asset processing failures
- YAML parsing errors

### 5. `logs/deployment.log`
**Purpose**: Main deployment log
**Contains**:
- High-level deployment progress
- Page and database creation status
- Summary statistics
- General information messages

## Common Debugging Scenarios

### Problem: Pages created but no content appears
```bash
# Debug the asset pipeline
python debug_deploy.py --debug-assets --dry-run

# Look for:
# - Block creation failures
# - Content transformation issues
# - YAML processing problems
```

### Problem: API calls failing
```bash
# Debug API requests/responses
python debug_deploy.py --debug-api --dry-run

# Look for:
# - HTTP error status codes
# - Invalid request payloads
# - Authentication issues
# - Rate limiting problems
```

### Problem: Intermittent failures
```bash
# Trace requests to correlate failures
python debug_deploy.py --trace-requests --debug-api

# Look for:
# - Request timing patterns
# - Correlation between specific requests and failures
# - Network timeout issues
```

## Environment Variables

You can also control debugging through environment variables:

```bash
export DEBUG_API=true          # Enable API debugging
export DEBUG_ASSETS=true       # Enable asset debugging
export TRACE_REQUESTS=true     # Enable request tracing
export LOG_LEVEL=DEBUG         # Set log level

python deploy.py --dry-run
```

## Integration with Existing deploy.py

The enhanced logging is designed to work with existing deploy.py usage:

```bash
# Add debugging to your existing commands
python debug_deploy.py --debug-api --generate-assets --test-pages 3
python debug_deploy.py --debug-all --parent-id=your-page-id --verbose
```

All original deploy.py flags are supported and passed through.

## Log Analysis Tips

### 1. Finding Specific Issues
```bash
# Search for errors in API log
grep -i "error" logs/deploy_debug_api.log

# Find failed page creations
grep "Failed to create page" logs/deploy_debug_assets.log

# Check request timing
grep "elapsed_seconds" logs/deploy_debug_api.log
```

### 2. Analyzing API Responses
The API debug log uses JSON format for easy parsing:
```bash
# Extract all 4xx/5xx responses
jq 'select(.status_code >= 400)' logs/deploy_debug_api.log

# Find long-running requests
jq 'select(.elapsed_seconds > 2)' logs/deploy_debug_api.log

# Show response summaries
jq '.response_summary' logs/deploy_debug_api.log
```

### 3. Monitoring Asset Processing
```bash
# Count successful block creations
grep "✓ Created" logs/deploy_debug_assets.log | wc -l

# Find skipped assets
grep "⚠ Skipped" logs/deploy_debug_assets.log

# Check YAML processing
grep "YAML section" logs/deploy_debug_assets.log
```

## Log File Management

### Clear Old Logs
```bash
python debug_deploy.py --clear-logs
```

### View Recent Logs
```bash
python debug_deploy.py --show-logs
```

### Log Rotation
Logs automatically rotate when they reach 10MB, keeping 5 backup files.

## Security Notes

- Sensitive information (tokens, API keys) is automatically redacted
- Request payloads are sanitized to remove credentials
- Only the first 1000 characters of large payloads are logged
- Response content is truncated for privacy

## Performance Impact

- API debugging adds ~5-10ms per request for logging overhead
- Asset debugging has minimal performance impact
- Request tracing adds correlation ID generation (~1ms per request)
- Log files are written asynchronously to minimize blocking

## Troubleshooting the Logging System

If the enhanced logging isn't working:

1. **Check imports**: Verify `modules/logging_config.py` exists
2. **Check permissions**: Ensure `logs/` directory is writable
3. **Check environment**: Verify debug environment variables are set
4. **Fallback mode**: The system gracefully falls back to basic logging if enhanced logging fails

## Example Debugging Session

```bash
# 1. Clear old logs
python debug_deploy.py --clear-logs

# 2. Run deployment with full debugging
python debug_deploy.py --debug-all --dry-run --verbose

# 3. Check for issues
python debug_deploy.py --show-logs

# 4. Analyze specific problems
grep -A5 -B5 "Failed" logs/deploy_errors.log

# 5. Check API responses
jq '.response_summary' logs/deploy_debug_api.log | head -20
```

This enhanced logging system provides complete visibility into the deployment process, making it much easier to identify and fix issues with asset deployment and API interactions.