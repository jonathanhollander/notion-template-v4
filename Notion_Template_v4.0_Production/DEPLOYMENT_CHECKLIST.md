# Notion Template v4.0 Production Deployment Checklist

## 🚀 Pre-Deployment (5-10 minutes)

### Environment Setup
- [ ] **Install Python 3.8+**
  ```bash
  python3 --version  # Should be 3.8 or higher
  ```

- [ ] **Install dependencies**
  ```bash
  cd Notion_Template_v4.0_Production/deploy
  pip install -r requirements.txt
  ```

- [ ] **Set environment variables**
  ```bash
  export NOTION_TOKEN="your_token_here"  # Must start with 'secret_' or 'ntn_'
  export NOTION_PARENT_PAGEID="your_page_id_here"
  export NOTION_VERSION="2025-09-03"  # Latest API version
  ```

### Validation Phase
- [ ] **Run validation only**
  ```bash
  python deploy.py --validate-only --verbose
  ```
  - ✅ Environment variables validated
  - ✅ YAML structure validated
  - ✅ No circular dependencies detected
  - ✅ All 22 YAML files loaded
  - ✅ All 9 CSV files accessible

- [ ] **Run dry run**
  ```bash
  python deploy.py --dry-run --verbose
  ```
  - Confirms deployment plan without making changes
  - Shows what will be created

## 📋 Deployment Options

### Option 1: Full Automated Deployment (Recommended)
```bash
python deploy.py --verbose
```

### Option 2: Interactive Deployment (For First Time)
```bash
python deploy.py --interactive --verbose
```
- Prompts before each phase
- Allows skipping problematic sections
- Good for debugging

### Option 3: Phased Deployment (For Testing)
```bash
# Deploy only pages first
python deploy.py --phase pages --verbose

# Then databases
python deploy.py --phase databases --verbose

# Then data
python deploy.py --phase data --verbose
```

### Option 4: Resume Failed Deployment
```bash
python deploy.py --resume --verbose
```
- Continues from last checkpoint
- Skips already completed items

## 🔍 During Deployment

### Monitor Progress
- [ ] **Pages Creation** (22 pages)
  - Progress bar shows completion
  - Each page logged with ID
  - Parent-child relationships maintained

- [ ] **Database Creation** (varies by YAML)
  - Schema properties configured
  - Relations prepared for setup
  - Formulas validated

- [ ] **Data Import** (9 CSV files)
  - Bucket_List.csv
  - Digital_Accounts.csv
  - Ethical_Will.csv
  - Financial_Accounts.csv
  - Final_Arrangements.csv
  - Important_Contacts.csv
  - Insurance_Policies.csv
  - Legal_Documents.csv
  - Medical_Information.csv

### Rate Limiting
- Default: 2.5 requests per second
- Automatic retry with exponential backoff
- Handles 429 rate limit responses gracefully

## ✅ Post-Deployment Verification

### Immediate Checks (2-3 minutes)
- [ ] **Verify root page created**
  - Open Notion
  - Navigate to parent page
  - Confirm "Estate Planning Concierge" exists

- [ ] **Check page hierarchy**
  - Verify all 22 pages created
  - Confirm parent-child relationships
  - Check navigation links work

- [ ] **Validate databases**
  - Open each database
  - Verify schema properties
  - Check formulas render correctly

- [ ] **Test data import**
  - Spot check 2-3 rows per database
  - Verify data formatting preserved
  - Check relations link correctly

### Functionality Tests (5-10 minutes)
- [ ] **Test navigation**
  - Click through main hub links
  - Verify all pages accessible
  - Check back navigation works

- [ ] **Test database views**
  - Switch between views if configured
  - Sort and filter work correctly
  - Formulas calculate properly

- [ ] **Test templates**
  - Create new entry from template
  - Verify default values populate
  - Check required fields marked

## 🔧 Troubleshooting

### Common Issues and Fixes

#### 1. Authentication Error
```bash
# Check token format
echo $NOTION_TOKEN | head -c 7
# Should show "secret_" or "ntn_"
```

#### 2. Rate Limiting
```bash
# Reduce request rate
export THROTTLE_RPS=1.0
python deploy.py --verbose
```

#### 3. Partial Deployment
```bash
# Resume from checkpoint
python deploy.py --resume --verbose

# Or clean start
rm .notion_deploy_state
python deploy.py --verbose
```

#### 4. Parent Page Not Found
```bash
# Override parent ID
python deploy.py --parent-id="actual-page-id-here" --verbose
```

#### 5. YAML Loading Issues
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('split_yaml/01_pages_core.yaml'))"
```

## 📊 Success Metrics

### Deployment Summary Should Show:
```
✅ Deployment completed successfully!
⏱️  Duration: ~120-180 seconds
📄 Pages created: 22+
🗄️  Databases created: 8+
📊 Data imported: 9 datasets
```

### Expected Structure:
```
Estate Planning Concierge (Root)
├── 📋 Getting Started
├── 🏠 Main Hub
│   ├── 📊 Dashboards
│   ├── 📁 Document Vault
│   └── 🔧 Admin Center
├── 💼 Financial Planning
│   ├── Financial Accounts (DB)
│   ├── Insurance Policies (DB)
│   └── Digital Accounts (DB)
├── 📜 Legal & Medical
│   ├── Legal Documents (DB)
│   ├── Medical Information (DB)
│   └── Important Contacts (DB)
├── 🎯 Personal Legacy
│   ├── Ethical Will (DB)
│   ├── Bucket List (DB)
│   └── Final Arrangements (DB)
└── 📚 Resources
    ├── Templates
    ├── Guides
    └── FAQs
```

## 🛡️ Security Reminders

1. **Never commit `.env` files** with tokens
2. **Rotate tokens** after deployment if shared
3. **Use read-only tokens** for testing
4. **Set page permissions** in Notion after deployment
5. **Backup template** before modifications

## 📝 Final Notes

### Deployment Time Estimates:
- **Validation**: 5-10 seconds
- **Pages Creation**: 30-45 seconds
- **Database Creation**: 20-30 seconds
- **Data Import**: 60-90 seconds
- **Total**: 2-3 minutes

### Resource Usage:
- **API Calls**: ~500-700 total
- **Network**: ~5-10 MB transfer
- **Memory**: <100 MB Python process

### Recovery Options:
- State checkpoint saved every operation
- Can resume within 24 hours
- Manual rollback via Notion UI if needed

## 🎉 Deployment Complete!

Once all checks pass, your Notion Estate Planning Template v4.0 is ready for use!

### Next Steps:
1. Customize branding and colors in Notion
2. Set up workspace permissions
3. Create user documentation
4. Train end users on features
5. Set up backup/export schedule

---

**Support**: For issues, check the forensic analysis in `../forensic-findings/`
**Version**: v4.0 Production (August 2025)
**API**: Notion API 2025-09-03