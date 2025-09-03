# Estate Planning Concierge v4.0 - Image Generation System
## Complete User Guide & Documentation

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Prerequisites & Setup](#prerequisites--setup)
3. [How the System Works](#how-the-system-works)
4. [Running the System](#running-the-system)
5. [What to Expect](#what-to-expect)
6. [Cost Breakdown](#cost-breakdown)
7. [Workflow Stages](#workflow-stages)
8. [Troubleshooting](#troubleshooting)
9. [Safety Features](#safety-features)
10. [Output Structure](#output-structure)

---

## System Overview

The Estate Planning Concierge v4.0 Image Generation System is an automated AI-powered image creation pipeline designed to generate ~490 visual assets for a comprehensive Notion-based estate planning template. The system uses multiple AI models to create icons, covers, textures, and letterheads with a consistent luxury aesthetic tailored for estate planning professionals.

### Key Features
- **Dynamic Asset Discovery**: Automatically discovers required assets from YAML configuration files
- **Multi-Model Orchestration**: Uses OpenRouter to generate competitive prompts from 3 different AI models
- **Two-Stage Generation**: Sample generation with review before mass production
- **Web-Based Review Interface**: Visual approval system on port 4500
- **Budget Protection**: Enforced spending limits with automatic stopping
- **Git Integration**: Automatic version control for generated assets
- **Quality Scoring**: AI-driven quality assessment for generated images

### Asset Types Generated
- **Icons**: 230+ SVG icons with mechanical poetry aesthetic
- **Covers**: 230+ PNG section covers with blueprint technical style
- **Letter Headers**: 18 professional letterhead designs
- **Database Icons**: 10 data visualization icons
- **Textures**: 10 seamless pattern backgrounds

---

## Prerequisites & Setup

### Required API Keys
You must have at least ONE of these API keys set in your environment:

```bash
# Required for image generation
export REPLICATE_API_KEY="your_replicate_api_key_here"

# Required for prompt orchestration
export OPENROUTER_API_KEY="your_openrouter_api_key_here"

# Optional but recommended for Notion integration
export NOTION_TOKEN="your_notion_integration_token"
export NOTION_PARENT_PAGEID="your_notion_page_id"
```

### Installation

1. **Clone or navigate to the project directory:**
```bash
cd /Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production
```

2. **Install Python dependencies:**
```bash
pip install -r asset_generation/requirements.txt
```

3. **Verify environment variables:**
```bash
echo $REPLICATE_API_KEY
echo $OPENROUTER_API_KEY
```

### Directory Structure
The system will automatically create these directories:
```
output/
├── samples/        # Sample images for review
├── production/     # Final production images
└── backup/         # Backup of previous runs

logs/
├── asset_generation.log     # Main system log
└── llm_generations/         # LLM interaction logs
```

---

## How the System Works

### Architecture Flow
```
1. YAML Discovery → 2. Prompt Generation → 3. Sample Creation → 
4. Review & Approval → 5. Mass Production → 6. Git Commit
```

### Detailed Process

1. **YAML Synchronization**
   - Reads all YAML files from `split_yaml/` directory
   - Discovers ~490 pages requiring visual assets
   - Categorizes by asset type (icons, covers, etc.)

2. **Prompt Orchestration**
   - Uses OpenRouter API to generate prompts
   - Creates 3 competitive variants per asset:
     - Claude: Emotional depth perspective
     - GPT-4: Creative luxury perspective  
     - Gemini: Technical precision perspective
   - Master prompt template guides all generations

3. **Sample Generation**
   - Creates 10 representative samples
   - Uses Replicate API with specific models:
     - Icons: Recraft v3 SVG ($0.04/image)
     - Covers: FLUX 1.1 Pro ($0.04/image)
     - Textures: Stable Diffusion XL ($0.003/image)

4. **Review Process**
   - Web server launches on http://localhost:4500
   - Visual interface for reviewing samples
   - Approve by creating `APPROVED.txt` file

5. **Mass Production**
   - Generates all ~490 assets
   - Real-time progress tracking
   - Budget enforcement throughout

6. **Git Integration**
   - Automatic commit of generated assets
   - Meaningful commit messages with statistics

---

## Running the System

### Basic Commands

#### Standard Full Run (Recommended)
```bash
cd asset_generation
python asset_generator.py
```
This will:
1. Generate 10 samples
2. Launch review server
3. Wait for approval
4. Generate all production assets
5. Commit to Git

#### Dry Run (Test Without API Calls)
```bash
python asset_generator.py --dry-run
```

#### Skip Review (Direct to Production - Dangerous!)
```bash
python asset_generator.py --skip-review
```

#### Mass Production Only (Requires Prior Approval)
```bash
python asset_generator.py --mass-production
```

#### Regenerate Failed Assets
```bash
python asset_generator.py --regenerate
```

### Command Options
- `--dry-run`: Preview operations without API calls
- `--skip-review`: Skip the review server (not recommended)
- `--mass-production`: Jump directly to mass generation (requires APPROVED.txt)
- `--regenerate`: Process regeneration queue from prompts.json
- `--no-commit`: Skip Git commit after generation
- `--edit-prompts`: Launch prompt editor only

---

## What to Expect

### Timeline
- **Sample Generation**: 2-3 minutes (10 images)
- **Review Process**: 5-10 minutes (your review time)
- **Mass Production**: 30-45 minutes (~490 images)
- **Total Time**: ~1 hour from start to finish

### Console Output
You'll see real-time status updates:
```
✅ 14:23:15 [INFO] ESTATE PLANNING CONCIERGE v4.0 - ASSET GENERATOR
================================================================================
✅ 14:23:15 [INFO] Configuration loaded from: config.json
✅ 14:23:15 [INFO] Sample budget: $1.00
✅ 14:23:15 [INFO] Production budget: $25.00
✅ 14:23:16 [INFO] ✓ Directory ready: output/samples
✅ 14:23:16 [INFO] Starting YAML synchronization...
✅ 14:23:17 [INFO] Assets discovered:
  - icons: 230
  - covers: 230
  - letter_headers: 18
  - database_icons: 10
  - textures: 10
  - TOTAL ASSETS: 498
```

### Progress Indicators
- **Progress bars** for batch operations
- **Cost tracking** in real-time
- **Error reporting** with detailed messages
- **Time elapsed** for each stage

---

## Cost Breakdown

### Estimated Costs
| Stage | Images | Cost per Image | Total Cost |
|-------|--------|----------------|------------|
| Sample Generation | 10 | $0.04 avg | $0.40 |
| Mass Production - Icons | 230 | $0.04 | $9.20 |
| Mass Production - Covers | 230 | $0.04 | $9.20 |
| Mass Production - Letters | 18 | $0.04 | $0.72 |
| Mass Production - DB Icons | 10 | $0.04 | $0.40 |
| Mass Production - Textures | 10 | $0.003 | $0.03 |
| **TOTAL** | **498** | - | **$19.95** |

### Budget Limits
- **Sample Budget**: $1.00 (hard limit)
- **Production Budget**: $25.00 (hard limit)
- **Daily Limit**: $25.00 (configured)

The system will automatically stop if budget limits are exceeded.

---

## Workflow Stages

### Stage 1: Sample Generation
```
Duration: 2-3 minutes
Cost: ~$0.40
Output: 10 sample images in output/samples/
```

**What happens:**
1. Syncs with YAML files to discover assets
2. Selects representative samples from each category
3. Generates prompts using OpenRouter
4. Creates images using Replicate
5. Saves manifest.json with metadata

### Stage 2: Review & Approval
```
Duration: 5-10 minutes (user-dependent)
Cost: $0
Output: APPROVED.txt or regeneration queue
```

**What happens:**
1. Web server starts on http://localhost:4500
2. Browser opens automatically (if configured)
3. Review interface shows all samples
4. You can edit prompts and queue regeneration
5. Create APPROVED.txt to proceed

**Review Interface Features:**
- Visual grid of generated samples
- Prompt editing capabilities
- Quality scoring display
- Regeneration queue management
- Approval/rejection buttons

### Stage 3: Mass Production
```
Duration: 30-45 minutes
Cost: ~$19.60
Output: ~490 images in output/production/
```

**What happens:**
1. Confirmation prompt with cost warning
2. Switches to production directory
3. Generates all assets with progress tracking
4. Saves production manifest
5. Automatic Git commit (if enabled)

### Stage 4: Git Commit
```
Duration: 10-30 seconds
Cost: $0
Output: Git commit with statistics
```

**Commit includes:**
- All generated assets
- Meaningful commit message
- Generation statistics
- Cost breakdown

---

## Safety Features

### Multiple Confirmation Points
1. **Cost Warning** before sample generation
2. **Review Server** approval required
3. **Production Confirmation** with total cost
4. **Budget Enforcement** with automatic stopping

### File Safety
- **No Overwrites**: Timestamp-based naming
- **Backup Directory**: Previous runs preserved
- **Manifest Files**: Complete generation history
- **Git Tracking**: Version control for all assets

### Error Recovery
- **Automatic Retries**: 3 attempts per API call
- **Regeneration Queue**: Failed assets can be retried
- **Partial Progress**: Continues from last successful asset
- **Detailed Logging**: Complete error traces

---

## Output Structure

### Generated Files
```
output/samples/
├── icons_001.svg
├── icons_002.svg
├── covers_001.png
├── covers_002.png
├── manifest.json
└── prompts.json

output/production/
├── icons_001.svg through icons_230.svg
├── covers_001.png through covers_230.png
├── letter_headers_001.png through letter_headers_018.png
├── database_icons_001.svg through database_icons_010.svg
├── textures_001.png through textures_010.png
└── manifest.json
```

### Manifest Structure
```json
{
  "assets": [...],
  "total_cost": 19.60,
  "errors": [],
  "timestamp": "2024-09-01T14:30:00",
  "production": true,
  "total_generated": 498,
  "total_expected": 498
}
```

---

## Troubleshooting

### Common Issues

#### API Key Not Found
```
Error: REPLICATE_API_KEY not found in environment
Solution: export REPLICATE_API_KEY="your_key_here"
```

#### Budget Exceeded
```
Error: Budget limit would be exceeded: $20.00 > $19.00
Solution: Increase budget in config.json or reduce asset count
```

#### Port Already in Use
```
Error: [Errno 48] Address already in use
Solution: Kill process on port 4500 or change port in config.json
```

#### YAML Parsing Error
```
Error: CRITICAL ERROR: YAML PARSING FAILED
Solution: Fix syntax errors in YAML files, check for proper indentation
```

### Debug Commands

**Check environment:**
```bash
env | grep -E "REPLICATE|OPENROUTER|NOTION"
```

**Test API connection:**
```bash
curl -H "Authorization: Token $REPLICATE_API_KEY" \
  https://api.replicate.com/v1/account
```

**View logs:**
```bash
tail -f logs/asset_generation.log
```

**Clean up approval:**
```bash
rm APPROVED.txt PRODUCTION_APPROVED.txt
```

---

## Advanced Usage

### Custom Configuration
Edit `asset_generation/config.json` to modify:
- Model selections
- Budget limits
- Rate limiting
- Output directories
- Review server port

### Prompt Customization
Edit `asset_generation/meta_prompts/master_prompt.txt` to change:
- Visual style guidelines
- Color palettes
- Composition rules
- Brand elements

### Selective Generation
To generate only specific asset types:
1. Edit the sample selection in `asset_generator.py`
2. Modify the `sample_configs` list
3. Run with custom parameters

### Integration with Notion
After generation, use the Notion deployment scripts to:
1. Upload assets to Notion
2. Create template structure
3. Link assets to pages

---

## Best Practices

1. **Always run samples first** - Never skip directly to mass production
2. **Review carefully** - Quality control prevents expensive regeneration
3. **Monitor costs** - Check real-time cost tracking
4. **Keep logs** - Useful for debugging and audit trails
5. **Backup before changes** - System creates backups automatically
6. **Test with dry-run** - Verify workflow without spending money
7. **Use Git commits** - Track asset versions over time

---

## Support & Maintenance

### Log Files
- **Main log**: `logs/asset_generation.log`
- **LLM logs**: `logs/llm_generations/*.json`
- **Manifests**: `output/*/manifest.json`

### File Locations
- **Code**: `asset_generation/`
- **Config**: `asset_generation/config.json`
- **YAML**: `split_yaml/*.yaml`
- **Output**: `output/samples/` and `output/production/`

### System Requirements
- Python 3.8+
- 4GB RAM minimum
- 10GB disk space for assets
- Stable internet connection
- Modern web browser for review

---

## Quick Start Checklist

- [ ] Set REPLICATE_API_KEY environment variable
- [ ] Set OPENROUTER_API_KEY environment variable
- [ ] Install Python dependencies
- [ ] Verify YAML files are present
- [ ] Check available disk space (10GB+)
- [ ] Run with --dry-run first
- [ ] Have ~$20 budget available
- [ ] Allow 1 hour for complete run

---

## Emergency Stop

To stop the system at any point:
1. **Keyboard Interrupt**: Press `Ctrl+C`
2. **Remove Approval**: Delete `APPROVED.txt`
3. **Kill Process**: `pkill -f asset_generator.py`

The system will save progress and can resume from where it stopped.

---

*Document Version: 1.0*  
*System Version: Estate Planning Concierge v4.0*  
*Last Updated: September 2025*