# Estate Planning Concierge v4.0 - Asset Generation System

## Overview
Automated asset generation system with comprehensive logging, real-time status updates, and approval workflows for the Estate Planning Concierge v4.0 Notion template.

## Features
- ✅ **Comprehensive Logging**: See exactly what's happening at all times
- 📊 **Real-time Status Updates**: Current phase, asset being generated, costs, time elapsed
- 💰 **Cost Tracking**: Live accumulation with budget limits
- 🎨 **Two-Stage Generation**: Sample → Review → Mass Production
- 🌐 **Web Review Interface**: Port 4500 with auto-browser opening
- 🔐 **Approval Gates**: Maintain ultimate control over quality and costs

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable
```bash
export REPLICATE_API_KEY="your_replicate_api_key_here"
```

### 3. Run Sample Generation
```bash
python asset_generator.py
```

### 4. Review Samples
- Browser auto-opens to http://localhost:4500
- Review the 8 sample assets
- Click "Approve for Production" or "Reject & Refine"

### 5. Mass Generation (After Approval)
The system automatically proceeds to mass generation after approval.

## Configuration

Edit `config.json` to customize:

### Models & Costs
```json
"models": {
  "icons": {
    "model_id": "black-forest-labs/recraft-v3-svg",
    "cost_per_image": 0.04
  },
  "covers": {
    "model_id": "black-forest-labs/flux-1.1-pro", 
    "cost_per_image": 0.04
  }
}
```

### Budget Limits
```json
"budget": {
  "sample_generation": {
    "max_cost": 0.50,    // Sample budget
    "items": 8           // Number of samples
  },
  "mass_generation": {
    "max_cost": 8.00,    // Production budget
    "items": 255         // Total assets
  }
}
```

### Review Server
```json
"review": {
  "port": 4500,          // Review server port
  "auto_open": true      // Auto-open browser
}
```

## Workflow

### Phase 1: Configuration (Automatic)
- Loads config.json
- **✨ NEW: Syncs with YAML files** from `../split_yaml/` directory
- Dynamically discovers pages needing icons and covers
- Validates API keys
- Sets up logging

### Phase 2: Sample Generation ($0.50 Budget)
- **✨ NEW: Generates samples based on YAML data**:
  - First 3 pages needing icons (from YAML discovery)
  - First 3 pages needing covers (from YAML discovery)  
  - 2-4 texture patterns (predefined)
- Intelligent prompt generation based on page titles and descriptions
- Real-time progress with cost tracking
- Saves to `output/samples/`

### Phase 3: Review & Approval
- Review server launches on port 4500
- Browser opens automatically
- Review samples in web interface
- Approve or reject with one click

### Phase 4: Mass Generation ($8.00 Budget)
- After approval, **✨ NEW: generates ALL assets from YAML**:
  - Icons for ALL pages with `icon_file` property (~30+ icons)
  - Covers for ALL pages with `cover_file` property (~30+ covers)
  - Complete texture set (4-12 patterns)
- Progress bars with nested tracking
- **✨ NEW: Integrated with deploy.py** using `--generate-assets` flag

## Logging Output Example

```
✅ 14:23:45 [INFO] ================================================================================
✅ 14:23:45 [INFO] ESTATE PLANNING CONCIERGE v4.0 - ASSET GENERATOR
✅ 14:23:45 [INFO] ================================================================================
✅ 14:23:45 [INFO] Configuration loaded from: config.json
✅ 14:23:45 [INFO] Sample budget: $0.50
✅ 14:23:45 [INFO] Production budget: $8.00
✅ 14:23:45 [INFO] Review server port: 4500
✅ 14:23:45 [INFO] ================================================================================

✅ 14:23:46 [INFO] [1.2s] [$0.000] SAMPLES: Starting icons generation (3 items)
✅ 14:23:48 [INFO] [3.4s] [$0.040] ICONS: ✓ Generated icons_001.png (Cost: $0.040, Total: $0.040)
✅ 14:23:50 [INFO] [5.6s] [$0.080] ICONS: ✓ Generated icons_002.png (Cost: $0.040, Total: $0.080)

Generating Samples: 100%|████████████████████| 8/8 [00:32<00:00, 4.02s/asset]

✅ 14:24:18 [INFO] ================================================================================
✅ 14:24:18 [INFO] SAMPLE GENERATION COMPLETE
✅ 14:24:18 [INFO] Generated: 8 samples
✅ 14:24:18 [INFO] Errors: 0
✅ 14:24:18 [INFO] Total Cost: $0.320
✅ 14:24:18 [INFO] Time Elapsed: 32.4s
✅ 14:24:18 [INFO] ================================================================================

✅ 14:24:19 [INFO] Starting review server on port 4500...
✅ 14:24:19 [INFO] Review URL: http://localhost:4500
🌐 Opening browser automatically...
```

## File Structure

```
asset_generation/
├── asset_generator.py      # Main generation script
├── review_server.py        # Web review interface
├── config.json            # Configuration
├── requirements.txt       # Dependencies
├── output/
│   ├── samples/          # Sample assets
│   │   ├── review.html   # Review interface
│   │   ├── manifest.json # Asset metadata
│   │   └── *.png/svg     # Generated assets
│   └── production/       # Mass generation output
└── logs/
    └── asset_generation.log  # Detailed logs
```

## Approval Files

- `APPROVED.txt` - Created when samples approved
- `REJECTED.txt` - Created when samples rejected
- `PRODUCTION_APPROVED.txt` - Required for GitHub deployment

## Cost Breakdown

### Sample Generation (Stage 1)
- 3 icons @ $0.04 = $0.12
- 3 covers @ $0.04 = $0.12
- 2 textures @ $0.003 = $0.006
- **Total: ~$0.25** (under $0.50 budget)

### Mass Generation (Stage 2)
- 30 icons @ $0.04 = $1.20
- 35 covers @ $0.04 = $1.40
- 12 textures @ $0.003 = $0.036
- 178 variations @ $0.03 avg = $5.34
- **Total: ~$7.98** (under $8.00 budget)

## Integration with Deploy.py

The asset generation system is now integrated with the main deployment script:

### Generate Assets Only
```bash
# Generate assets without deployment
python deploy.py --assets-only

# Generate assets with full verbose logging  
python deploy.py --assets-only --verbose --verbose
```

### Generate Assets Then Deploy
```bash
# Complete workflow: assets → deployment
python deploy.py --generate-assets

# With detailed logging
python deploy.py --generate-assets --verbose
```

### Standalone Asset Generation
```bash
# Original standalone mode (still supported)
cd asset_generation/
python asset_generator.py
```

## YAML Integration Features

### Dynamic Asset Discovery
- **Single Source of Truth**: YAML files in `../split_yaml/` drive asset generation
- **Intelligent Prompts**: Page titles and descriptions become asset prompts
- **Automatic Scaling**: System adapts to any number of pages
- **Zero Hardcoding**: No more manual prompt lists in code

### Example YAML Processing
```yaml
# From split_yaml/01_pages_core.yaml
- title: Preparation Hub
  description: Your personal starting place to set everything in motion
  icon_file: assets/icons/preparation-hub-icon.svg
  cover_file: assets/covers/preparation-hub-cover.svg
```

Becomes:
```
Icon Prompt: "Technical drawing icon for 'Preparation Hub': Your personal starting place to set everything in motion, mechanical poetry style, readable at 24px"

Cover Prompt: "Blueprint cover for 'Preparation Hub': Your personal starting place to set everything in motion, architectural drawing style, golden ratio grid"
```

### Asset Counts (Auto-discovered from YAML)
- **Icons**: ~35 pages with `icon_file` property
- **Covers**: ~35 pages with `cover_file` property  
- **Textures**: 4 predefined patterns
- **Total**: ~74 unique assets (dynamic based on YAML content)

## Troubleshooting

### Port 4500 In Use
The system automatically finds the next available port (4501, 4502, etc.)

### API Key Not Found
```bash
export REPLICATE_API_KEY="r8_xxxxxxxxxxxxx"
```

### Browser Doesn't Open
Navigate manually to http://localhost:4500

### Approval Not Working
Create `APPROVED.txt` manually in the current directory

## Support

For issues or questions about the asset generation system, refer to:
- REPLICATE_ASSET_GENERATION_PLAN.md - Detailed implementation plan
- PREMIUM_UI_COMBINED_IMPLEMENTATION_PLAN.md - Overall UI strategy
- logs/asset_generation.log - Detailed execution logs