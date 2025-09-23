# Developer Walkthrough - Running the Estate Planning v4.0 System

## Quick Start: Your First Image Generation

### What You Need Before Starting
```bash
# Required API Key (get from replicate.com)
export REPLICATE_API_KEY="r8_your_key_here"

# Python 3.8+ installed
python --version  # Should show 3.8 or higher

# Install dependencies
pip install replicate pillow pyyaml requests flask
```

### Generate Your First 5 Images (10 minutes)

#### Option 1: Web Interface (RECOMMENDED)
```bash
# Navigate to the project
cd /path/to/asset_generation

# Start the web server
python3 review_dashboard.py

# Open browser to http://localhost:4500
# Click "Start Test Generation (3 Images)" button
# Watch real-time WebSocket updates as images generate
```

#### Option 2: Command Line
```bash
# Run the test script
python test_generate_samples.py --samples 5

# Watch the magic happen:
# 1. Emotional AI analyzes content
# 2. Meta-prompts are generated
# 3. Images are created via Replicate
# 4. Review dashboard available at localhost:4500
```

## Understanding What Just Happened

### Step 1: The Test Script Loaded Asset Definitions
```python
# test_generate_samples.py called:
generator = AssetGenerator()
assets = generator.load_yaml_files()  # Loaded 490 definitions
sample_assets = assets[:5]  # Took first 5 for testing
```

### Step 2: Emotional AI Analyzed Each Asset
```python
# For each asset, this happened:
emotional_profile = emotional_mgr.analyze_content(
    title="Estate Planning Concierge",
    description="Your comprehensive guide to protecting your family's future"
)

# Result:
{
    "life_stage": "Legacy",
    "primary_emotion": "security",
    "color_palette": ["deep blue", "gold", "warm gray"],
    "mood": "professional trust with warmth"
}
```

### Step 3: Images Were Generated
```python
# Replicate API was called with enhanced prompts:
"Professional estate planning cover image with deep blue and gold 
accents, conveying security and legacy, balanced composition with 
forward-looking elements, photorealistic style, 1792x1024"
```

### Step 4: Web Interface Features
- Navigate to http://localhost:4500 (manual navigation required)
- Main dashboard with generation controls
- Master Prompt Editor at /edit-master-prompt
- Emotional Config at /emotional-config
- Real-time WebSocket status updates
- Live log streaming during generation
- Each image has Approve/Reject/Regenerate buttons
- Approved images moved to /assets folder

## Full System Walkthrough

### 1. Starting Fresh - First Time Setup

```bash
# 1. Check your environment
python --version  # Need 3.8+
pip --version     # Need pip installed

# 2. Install all dependencies
pip install -r requirements.txt

# 3. Set your API key
export REPLICATE_API_KEY="r8_xxxxx"  # Get from replicate.com

# 4. Verify file structure exists
ls -la
# Should see:
# - asset_generator.py (main orchestrator - 70KB)
# - emotional_elements.py (emotional AI - 33KB)
# - review_dashboard.py (web server - 1,590 lines)
# - quality_scorer.py (quality evaluation)
# - generate_real_evaluations.py (dynamic scoring)
# - websocket_broadcaster.py (real-time updates)
# - templates/ (dashboard.html, master_prompt_editor.html, emotional_config.html)
# - static/js/ (dashboard.js and 6 modules)
# - config.json (configuration)
# - prompts.json (prompt templates)
# - split_yaml/ (21 YAML files)
```

### 2. Understanding the File Structure

```
asset_generation/
├── Core Generation System
│   ├── asset_generator.py         # Main orchestrator (70KB, 1,500+ lines)
│   ├── emotional_elements.py      # Emotional AI (33KB, 708 lines)
│   ├── openrouter_orchestrator.py # Multi-model system (27KB)
│   ├── quality_scorer.py          # Quality evaluation system
│   ├── generate_real_evaluations.py # Dynamic evaluation (266 lines)
│   └── websocket_broadcaster.py   # Real-time updates
│
├── Web Interface System
│   ├── review_dashboard.py        # Flask server (1,590 lines)
│   ├── templates/                 # HTML templates
│   │   ├── dashboard.html         # Main interface
│   │   ├── master_prompt_editor.html  # Prompt editor
│   │   └── emotional_config.html  # Emotional tuning
│   └── static/                    # Frontend assets
│       ├── js/
│       │   ├── dashboard.js      # Main controller (1,006 lines)
│       │   └── modules/          # 6 specialized modules
│       └── css/
│
├── Configuration
│   ├── config.json               # API settings, models
│   ├── prompts.json             # Prompt templates  
│   ├── meta_prompts/            # Master prompt storage
│   └── split_yaml/              # 21 YAML asset definitions
│
└── Output
    ├── temp/                    # Pending approval
    ├── assets/                  # Approved images
    │   ├── icons/              # 273 icons
    │   ├── covers/             # 147 covers
    │   └── textures/           # 70 textures
    └── APPROVED.txt            # Approval tracking
```

### 3. Running a Test Generation (Sample Mode)

```bash
# Generate 10 test images to understand the system
python test_generate_samples.py --samples 10

# What you'll see in terminal:
"""
Estate Planning v4.0 Asset Generator
====================================
Loading 490 asset definitions...
Generating 10 sample images...

[1/10] Generating: Estate Planning Concierge
  - Emotional Analysis: Legacy/Security
  - Color Palette: deep blue, gold, warm gray
  - Calling Replicate API...
  - Cost: $0.04
  - Saved to temp/asset_001.png

[2/10] Generating: Last Will & Testament
  - Emotional Analysis: Legacy/Transcendence
  - Color Palette: navy, heritage gold, oak brown
  - Calling Replicate API...
  - Cost: $0.04
  - Saved to temp/asset_002.png

...

Total Cost: $0.40
Opening approval dashboard at http://localhost:4500
"""
```

### 4. Using the Approval Dashboard

```javascript
// When dashboard opens, you'll see:

┌─────────────────────────────────────────┐
│  Estate Planning v4.0 Approval Dashboard │
├─────────────────────────────────────────┤
│                                         │
│  [Image Grid View]                      │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐      │
│  │     │ │     │ │     │ │     │      │
│  │ IMG │ │ IMG │ │ IMG │ │ IMG │      │
│  │  1  │ │  2  │ │  3  │ │  4  │      │
│  └─────┘ └─────┘ └─────┘ └─────┘      │
│   ✓ ✗ ↻   ✓ ✗ ↻   ✓ ✗ ↻   ✓ ✗ ↻      │
│                                         │
│  Session Stats:                        │
│  Approved: 0 | Rejected: 0 | Cost: $0  │
└─────────────────────────────────────────┘

// Click any image for full view
// ✓ = Approve (moves to /assets)
// ✗ = Reject (deletes)
// ↻ = Regenerate (creates new version)
```

### 5. Running Full Generation (490 Images)

```bash
# WARNING: This costs ~$20 and takes 4-6 hours
python asset_generator.py --full-run

# Better approach: Run in batches
python asset_generator.py --batch 1  # Images 1-100
python asset_generator.py --batch 2  # Images 101-200
# ... etc
```

### 6. Monitoring Progress

```python
# Check generation progress
tail -f generation.log

# Sample log output:
2024-01-15 14:23:45 - Image 156/490 generated
2024-01-15 14:23:47 - Cost so far: $6.24
2024-01-15 14:23:48 - Approval rate: 87%
2024-01-15 14:23:50 - Estimated time remaining: 3.2 hours
```

## Debugging Common Issues

### Issue 1: "API Key Not Found"
```bash
# Solution:
export REPLICATE_API_KEY="r8_your_actual_key"
# Verify:
echo $REPLICATE_API_KEY
```

### Issue 2: "ModuleNotFoundError"
```bash
# Solution:
pip install -r requirements.txt
# Or individually:
pip install replicate pyyaml pillow requests flask
```

### Issue 3: "Rate Limit Exceeded"
```python
# The system handles this automatically, but you can adjust:
# In config.json:
"rate_limit": 1,  # Reduce to 1 request per second
"retry": 5        # Increase retries
```

### Issue 4: "Dashboard Won't Open"
```bash
# Check if port 4500 is in use:
lsof -i :4500
# Kill any process using it:
kill -9 [PID]
# Or change port in config.json:
"port": 4501
```

## Understanding the Code Flow

### The Main Generation Loop
```python
# Simplified version of what happens:

for asset in assets:
    # 1. Emotional Analysis
    emotions = emotional_ai.analyze(asset)
    
    # 2. Prompt Generation
    prompt = meta_prompt_system.generate(asset, emotions)
    
    # 3. Image Generation
    image = replicate_api.generate(prompt)
    
    # 4. Quality Validation
    if quality_validator.check(image):
        # 5. Queue for Review
        pending_queue.add(image)
    else:
        # Retry with adjustments
        retry_with_tweaks(asset)
```

## Customizing Generation

### Adjusting Emotional Parameters
```python
# In emotional_elements.py, you can tweak:
EMOTION_INTENSITY_MULTIPLIER = 1.2  # Make emotions stronger
COLOR_SATURATION = 0.8  # Make colors more muted
SYMBOL_COMPLEXITY = "simple"  # Use simpler symbols
```

### Changing Image Styles
```json
// In config.json:
"styles": {
    "icons": {
        "style": "flat_design",  // Change from realistic_image
        "colors": "vibrant"      // Change from professional
    }
}
```

### Modifying Prompts
```json
// In prompts.json:
"base_template": "Create a {style} image that {emotion} for {context}"
// Customize the template structure
```

## Testing Individual Components

### Test Emotional AI Only
```python
from emotional_elements import EmotionalElementsManager

em = EmotionalElementsManager()
result = em.analyze_content(
    "Last Will & Testament",
    "Document for final wishes"
)
print(result)
# See the emotional analysis without generating images
```

### Test Prompt Generation Only
```python
from openrouter_orchestrator import OpenRouterOrchestrator

orch = OpenRouterOrchestrator()
prompt = orch.generate_prompt(
    {"title": "Trust Fund", "description": "Financial security"},
    {"life_stage": "Legacy", "emotion": "security"}
)
print(prompt)
# See the generated prompt without calling Replicate
```

### Test Single Image Generation
```python
from asset_generator import AssetGenerator

gen = AssetGenerator()
result = gen.generate_single_image(
    asset_id="test_001",
    title="Test Image",
    description="Testing the system"
)
print(f"Image saved to: {result['path']}")
print(f"Cost: ${result['cost']}")
```

## Performance Tips

### Speed Optimizations
```python
# Enable parallel processing (in asset_generator.py):
PARALLEL_GENERATION = True
MAX_WORKERS = 3  # Generate 3 images simultaneously

# Use caching for similar content:
ENABLE_EMOTION_CACHE = True
CACHE_SIZE = 1000
```

### Cost Optimizations
```python
# Use cheaper models for less important images:
if asset["visual_priority"] == "low":
    model = "stability-ai/sdxl"  # $0.003 vs $0.04
```

### Memory Management
```python
# Process in smaller batches:
BATCH_SIZE = 50  # Instead of all 490 at once

# Clear temp files regularly:
AUTO_CLEANUP = True
CLEANUP_AFTER_BATCH = True
```

## Production Deployment Notes

### Running as a Service
```bash
# Create systemd service (Linux):
sudo nano /etc/systemd/system/estate-planning-generator.service

[Unit]
Description=Estate Planning Image Generator
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
Environment="REPLICATE_API_KEY=r8_xxxxx"
ExecStart=/usr/bin/python3 review_dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start:
sudo systemctl enable estate-planning-generator
sudo systemctl start estate-planning-generator
```

### Monitoring and Logging
```python
# Enable detailed logging (in config.json):
"logging": {
    "level": "DEBUG",
    "file": "generation.log",
    "rotate_size": "10MB",
    "backup_count": 5
}
```

## Next Steps for Developers

1. **Run test generation** (5-10 images) to see the system work
2. **Review the generated images** in the approval dashboard
3. **Examine the logs** to understand the emotional analysis
4. **Modify one parameter** (like color intensity) and regenerate
5. **Check the code** that interests you most (emotional AI? prompt generation?)
6. **Build something new** on top of this foundation

## The Most Important Files to Read

1. **asset_generator.py** - Start here, it orchestrates everything
2. **emotional_elements.py** - The innovative emotional AI system
3. **dashboard.html** - See how the approval UI works
4. **config.json** - Understand the configuration options
5. **test_generate_samples.py** - Perfect starting point for testing

## Final Tips

- Start with sample generation (5-10 images) not full 490
- Watch the terminal output to understand the flow
- Use the dashboard to see quality and approve/reject
- Check generation.log for detailed debugging
- Modify config.json for quick behavior changes
- The emotional AI is the secret sauce - study emotional_elements.py

---

*This walkthrough gives you everything needed to run, understand, and modify the Estate Planning v4.0 Asset Generation System. The code is production-ready and battle-tested on 490 real images.*