# Estate Planning Concierge v4.0 - Deployment Guide

## Prerequisites

### System Requirements
- Python 3.8 or higher
- pip package manager
- Git (optional, for asset management)
- Internet connection for Notion API access

### Required Accounts
- Notion account with API access
- Notion Integration token
- Parent page in Notion where the template will be deployed

## Setup Instructions

### 1. Install Dependencies

```bash
# Install all required Python packages
pip install -r requirements.txt

# Verify installation
python3 -c "import requests, yaml, PIL; print('All dependencies installed successfully')"
```

### 2. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use any text editor
```

Required environment variables:
- `NOTION_TOKEN`: Your Notion integration token (starts with `secret_` or `ntn_`)
- `NOTION_PARENT_PAGEID`: The ID of the parent page where the template will be created

Optional environment variables:
- `NOTION_VERSION`: API version (default: 2022-06-28)
- `THROTTLE_RPS`: Rate limit in requests per second (default: 2.5)
- `LOG_LEVEL`: Logging verbosity (INFO, DEBUG, WARNING, ERROR)
- `GITHUB_ASSETS_REPO`: GitHub repository for visual assets

### 3. Validate Setup

Run the validation script to ensure everything is configured correctly:

```bash
python3 validate_deployment_ready.py
```

This will check:
- Python version compatibility
- All required files are present
- Dependencies are installed
- Environment variables are set
- Module imports work correctly
- Configuration is valid
- No duplicate functions exist

Only proceed when all checks pass.

### 4. Test Deployment (Optional but Recommended)

Run a comprehensive test to verify all components:

```bash
python3 test_deployment_requirements.py
```

This performs deeper testing including:
- YAML file validity
- Security configuration
- Error handling coverage
- GitHub assets accessibility
- Database module functionality

## Deployment Process

### 1. Dry Run (Recommended)

First, perform a dry run to see what will be created without making actual API calls:

```bash
python3 deploy.py --dry-run
```

Review the output to ensure the structure looks correct.

### 2. Full Deployment

Execute the deployment:

```bash
python3 deploy.py
```

The deployment will:
1. Validate your Notion token
2. Create the Estate Planning Concierge workspace structure
3. Set up all pages, databases, and relationships
4. Configure visual assets and themes
5. Populate initial data and templates
6. Create role-based dashboards

Expected duration: 15-30 minutes depending on API response times

### 3. Monitor Progress

The deployment script provides detailed logging:
- **INFO**: Normal progress updates
- **WARNING**: Non-critical issues (will continue)
- **ERROR**: Critical issues (may stop deployment)

Logs are saved to: `logs/deployment.log`

## Post-Deployment Verification

### 1. Check Notion Workspace

Navigate to your Notion workspace and verify:
- [ ] Main Estate Planning Concierge page created
- [ ] All hub pages present (Owner, Family, Professional, etc.)
- [ ] Databases created and linked
- [ ] Visual assets loading correctly
- [ ] Dashboards populated with content

### 2. Test Core Features

- [ ] Create a test entry in the Assets database
- [ ] Verify relationships between databases work
- [ ] Check that rollup properties calculate correctly
- [ ] Test filtering and sorting in databases
- [ ] Confirm visual themes apply correctly

### 3. Review Logs

Check the deployment log for any warnings:

```bash
tail -100 logs/deployment.log | grep -E "WARNING|ERROR"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Authentication Error
**Error**: "Invalid token" or "Unauthorized"
**Solution**: 
- Verify your NOTION_TOKEN is correct
- Ensure the integration has access to the parent page
- Check token format (should start with `secret_` or `ntn_`)

#### 2. Rate Limiting
**Error**: "Rate limit exceeded"
**Solution**:
- Reduce THROTTLE_RPS in .env (try 1.5 or 2.0)
- Wait a few minutes and retry
- The script has automatic retry with exponential backoff

#### 3. Missing Dependencies
**Error**: "ModuleNotFoundError"
**Solution**:
```bash
pip install --upgrade -r requirements.txt
```

#### 4. Parent Page Not Found
**Error**: "Parent page not found"
**Solution**:
- Verify NOTION_PARENT_PAGEID is correct
- Ensure the integration has access to the page
- The page ID should be 32 characters (no dashes)

#### 5. YAML Parsing Errors
**Error**: "Invalid YAML in [filename]"
**Solution**:
- Check the specific YAML file for syntax errors
- Common issues: incorrect indentation, missing colons
- Use a YAML validator: https://www.yamllint.com/

#### 6. Duplicate Function Errors
**Error**: "Duplicate function definition"
**Solution**:
- Run: `python3 validate_deployment_ready.py`
- If duplicates found, the validation script will show line numbers
- Remove or rename duplicate functions

### Getting Help

If you encounter issues not covered here:

1. Check the detailed logs:
   ```bash
   cat logs/deployment.log | grep -A5 -B5 ERROR
   ```

2. Run the validation script in verbose mode:
   ```bash
   LOG_LEVEL=DEBUG python3 validate_deployment_ready.py
   ```

3. Verify your Notion API connection:
   ```bash
   python3 -c "from modules.auth import validate_token; validate_token()"
   ```

## Maintenance

### Regular Updates

1. **Update dependencies periodically**:
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Check for API version updates**:
   - Monitor Notion API changelog
   - Update NOTION_VERSION in .env if needed

3. **Backup your deployment**:
   - Export your Notion workspace regularly
   - Keep copies of customized YAML configurations

### Monitoring

- Review logs weekly for warnings
- Monitor API usage in Notion settings
- Check for deprecated features in Notion API docs

## Security Best Practices

1. **Never commit .env files to version control**
2. **Rotate API tokens periodically**
3. **Use read-only tokens when possible**
4. **Limit integration access to specific pages**
5. **Review logs for unauthorized access attempts**
6. **Keep dependencies updated for security patches**

## Advanced Configuration

### Custom Themes

Edit `config.yaml` to customize visual themes:

```yaml
visual_config:
  default_theme: "professional"
  available_themes:
    - default
    - professional
    - family
    - legacy
```

### Rate Limiting

Adjust rate limiting based on your Notion plan:

```yaml
rate_limit_rps: 2.5  # Free/Personal plan
# rate_limit_rps: 10  # Team plan
# rate_limit_rps: 15  # Enterprise plan
```

### Logging Configuration

Customize logging in .env:

```bash
LOG_LEVEL=DEBUG           # More verbose
LOG_FILE=logs/custom.log  # Custom location
LOG_MAX_SIZE=52428800     # 50MB max size
LOG_BACKUP_COUNT=10       # Keep 10 backups
```

## Rollback Procedure

If deployment fails or needs to be reversed:

1. **Delete created pages in Notion** (they'll be in trash for 30 days)
2. **Review deployment log** to understand what was created
3. **Fix identified issues**
4. **Re-run validation**: `python3 validate_deployment_ready.py`
5. **Retry deployment**

## Success Indicators

A successful deployment will show:
- ✅ All validation checks passed
- ✅ No ERROR messages in logs
- ✅ All pages and databases visible in Notion
- ✅ Visual assets loading correctly
- ✅ Relationships between databases working
- ✅ Dashboards populated with data

## Version Information

- **Current Version**: 4.0 Production
- **API Version**: 2022-06-28 (Stable)
- **Python Required**: 3.8+
- **Last Updated**: 2024

---

For additional support or to report issues, please refer to the project documentation or contact the development team.