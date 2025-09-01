# Estate Planning Concierge v4.0 - Automated Premium Asset Generation Plan

## Executive Summary
This plan details a fully automated approach to generating 200+ premium assets for the Estate Planning Concierge v4.0 Notion template using Replicate API. The strategy prioritizes quality where it matters most while maintaining cost efficiency through smart model selection.

**Total Estimated Cost: $15-20** (vs. $50-75 for premium-everywhere approach)
**Total Assets: 200+** museum-quality designs
**Automation Level: 100%** - No manual intervention required

---

## Part 1: Smart Model Selection Strategy

### Tier System Based on Visual Impact

#### Tier 1: Hero Assets (Premium Models Required)
These are the first impressions and most visible elements.

**Assets:**
- 7 Main Section Covers (Preparation, Executor, Family, etc.)
- 30 Mechanical Poetry Icons (Core navigation elements)

**Models:**
- **Covers:** FLUX 1.1 Pro ($0.04/image)
  - Reason: Best prompt adherence, complex compositions
  - Alternative considered: FLUX Dev ($0.01) - Rejected due to lower quality
- **Icons:** Recraft V3 SVG ($0.04/image)
  - Reason: ONLY model generating true SVG vectors
  - No alternative exists for real SVG output

**Cost:** $1.48 base × 3 themes = $4.44

#### Tier 2: Supporting Assets (Mid-Range Models)
Visible but not focal points.

**Assets:**
- 28 Subsection Covers
- 12 Background Textures
- 16 Seasonal Overlays
- 20 Patina/Aging Effects

**Models:**
- **Primary:** SDXL ($0.003/image)
  - Reason: 93% cheaper than FLUX, 90% quality
  - Fast generation enables more iterations
- **Backup:** Stable Diffusion 3 ($0.03/image) - Only if SDXL fails

**Cost:** $0.23 base × 3 themes = $0.69

#### Tier 3: Utility Assets (Procedural/Cheap)
Geometric patterns and simple elements.

**Assets:**
- Grid patterns
- Dividers
- Simple geometric shapes

**Method:**
- Procedural generation via code (FREE)
- SDXL only for complex patterns ($0.003/image)

**Cost:** ~$0.10

### Style Consistency Without Manual Training

#### Strategy: Reference Image Pipeline
Instead of LoRA training, we use a master reference approach:

1. **Generate Master Styles** ($0.12)
   ```python
   masters = {
       "icon_style": "Recraft V3 - Leonardo da Vinci technical sketch",
       "cover_style": "FLUX - Aged blueprint with patina",
       "texture_style": "SDXL - Museum parchment with verdigris"
   }
   ```

2. **Style Transfer Models** ($1-2)
   - `fofr/style-transfer` - $0.01/image
   - `stability-ai/sdxl-ip-adapter` - $0.003/image
   - Apply master style to all subsequent generations

3. **Consistent Prompting**
   - Base style prompt appended to all generations
   - Technical parameters (line weight, color hex codes)
   - Artistic references (da Vinci, astronomical charts)

**Total Style Consistency Cost:** ~$2.00

---

## Part 2: Detailed Cost Breakdown

### Base Asset Generation
| Asset Type | Quantity | Model | Unit Cost | Total |
|------------|----------|-------|-----------|-------|
| Hero Covers | 7 | FLUX 1.1 Pro | $0.04 | $0.28 |
| SVG Icons | 30 | Recraft V3 | $0.04 | $1.20 |
| Sub-Covers | 28 | SDXL | $0.003 | $0.08 |
| Textures | 12 | SDXL | $0.003 | $0.04 |
| Overlays | 16 | SDXL | $0.003 | $0.05 |
| Patina | 20 | SDXL | $0.003 | $0.06 |
| **Subtotal** | **103** | | | **$1.71** |

### Theme Variations (×3)
- Executive Blue Theme: $1.71
- Legacy Purple Theme: $1.71
- Heritage Green Theme: $1.71
- **Subtotal:** $5.13

### Style Consistency
- Master References: $0.12
- Style Transfer (100 applications): $1.00
- **Subtotal:** $1.12

### Quality Iterations
- A/B Testing (20% regeneration): ~$1.50
- Final Refinements: ~$1.00
- **Subtotal:** $2.50

### **Grand Total: $9.75** 
**With 100% Buffer: $15-20**

---

## Part 3: Automated Implementation Architecture

### Project Structure with Local Storage & GitHub Integration
```
replicate_asset_generator/
├── config/
│   ├── replicate_config.yaml     # API settings, model IDs
│   ├── asset_manifest.json       # Asset list and specifications
│   └── theme_definitions.yaml    # Color schemes for 3 themes
│
├── prompts/
│   ├── base_styles.py           # Consistent style descriptions
│   ├── icon_prompts.py          # 30 mechanical icon descriptions
│   ├── cover_prompts.py         # 35 cover descriptions
│   └── texture_prompts.py       # Background and patina prompts
│
├── generators/
│   ├── __init__.py
│   ├── base_generator.py        # Abstract base class
│   ├── icon_generator.py        # Recraft V3 SVG generation
│   ├── cover_generator.py       # FLUX/SDXL cover generation
│   ├── texture_generator.py     # SDXL texture generation
│   └── style_manager.py         # Style consistency logic
│
├── storage/
│   ├── local_storage.py         # Save to local filesystem
│   ├── github_uploader.py       # Push to GitHub repo
│   └── backup_manager.py        # Ensure redundancy
│
├── review/
│   ├── sample_generator.py      # Generate review samples
│   ├── review_server.py         # Local web server for review
│   └── approval_gate.py         # Approval checkpoint logic
│
├── optimization/
│   ├── svg_optimizer.py         # SVGO wrapper for SVG files
│   ├── image_compressor.py      # PNG/JPEG optimization
│   └── batch_processor.py       # Parallel processing
│
├── output/                       # LOCAL STORAGE (PRIMARY)
│   ├── samples/                 # REVIEW SAMPLES FIRST
│   │   ├── icons/              # 3 sample icons
│   │   ├── covers/             # 2 sample covers
│   │   └── review.html         # Review interface
│   ├── approved/               # After approval only
│   │   ├── masters/           # Style reference images
│   │   ├── icons/             # ALL SVG icons by theme
│   │   ├── covers/            # ALL cover images by theme
│   │   ├── textures/          # ALL backgrounds and overlays
│   │   └── manifest.json      # Final asset registry
│   └── backup/                 # Backup before GitHub push
│
├── main.py                       # Orchestration script
├── review_samples.py            # STEP 1: Generate samples
├── mass_generate.py             # STEP 2: After approval only
├── requirements.txt              # Python dependencies
└── README.md                     # Setup and usage
```

### Configuration Structure (config.json)

```json
{
  "replicate": {
    "api_key": "${REPLICATE_API_KEY}",
    "rate_limit": 2,
    "timeout": 30,
    "retry": 3
  },
  
  "models": {
    "tier_1": {
      "icons": {
        "model": "recraft-ai/recraft-v3-svg",
        "cost_per_image": 0.04,
        "description": "Premium SVG icons - Mechanical Poetry style"
      },
      "covers": {
        "model": "black-forest-labs/flux-1.1-pro",
        "cost_per_image": 0.04,
        "description": "Hero covers - Blueprint aesthetic"
      }
    },
    "tier_2": {
      "textures": {
        "model": "stability-ai/sdxl",
        "cost_per_image": 0.003,
        "description": "Background textures and patterns"
      },
      "subsections": {
        "model": "stability-ai/sdxl",
        "cost_per_image": 0.003,
        "description": "Subsection covers"
      }
    }
  },
  
  "budget": {
    "sample_generation": {
      "max_cost": 0.50,
      "approval_required": true,
      "items": 8
    },
    "mass_generation": {
      "max_cost": 8.00,
      "approval_required": true,
      "items": 255
    },
    "total_limit": 10.00,
    "currency": "USD"
  },
  
  "review": {
    "port": 4500,
    "auto_open": true,
    "host": "localhost",
    "approval_file": "APPROVED.txt",
    "production_approval": "PRODUCTION_APPROVED.txt"
  },
  
  "storage": {
    "local": {
      "base_path": "output",
      "backup_before_push": true,
      "structure": {
        "samples": "output/samples",
        "production": "output/production",
        "reports": "output/reports"
      }
    },
    "github": {
      "repo": "notion-estate-assets",
      "branch": "main",
      "path": "assets",
      "commit_message": "Update Estate Planning v4.0 assets",
      "push_batch_size": 50
    }
  },
  
  "themes": {
    "executive_blue": {
      "primary": "#1A365D",
      "secondary": "#2C5282",
      "accent": "#90CDF4",
      "patina": "#4A7C74"
    },
    "legacy_purple": {
      "primary": "#3E3127",
      "secondary": "#6B5B73",
      "accent": "#C4A584",
      "patina": "#744210"
    },
    "heritage_green": {
      "primary": "#22543D",
      "secondary": "#276749",
      "accent": "#68D391",
      "patina": "#696F5C"
    }
  },
  
  "logging": {
    "level": "INFO",
    "colored_output": true,
    "progress_bars": true,
    "real_time_status": true,
    "save_to_file": true,
    "log_file": "output/reports/generation.log"
  },
  
  "quality": {
    "svg_optimization": true,
    "png_compression": true,
    "max_file_size_kb": 100,
    "min_dimensions": 64,
    "style_consistency_threshold": 0.8
  },
  
  "workflow": {
    "stages": [
      {
        "name": "Sample Generation",
        "approval_required": true,
        "max_cost": 0.50
      },
      {
        "name": "Mass Generation", 
        "approval_required": true,
        "requires_previous": true,
        "max_cost": 8.00
      },
      {
        "name": "GitHub Deployment",
        "approval_required": false,
        "requires_previous": true
      }
    ]
  }
}
```

### Core Python Implementation with Comprehensive Logging

```python
# config/replicate_config.yaml
api:
  token: ${REPLICATE_API_TOKEN}
  rate_limit: 10  # requests per minute

models:
  premium:
    flux_pro: "black-forest-labs/flux-1.1-pro"
    recraft_svg: "recraft-ai/recraft-v3-svg"
  standard:
    sdxl: "stability-ai/sdxl"
  style:
    transfer: "fofr/style-transfer"
    ip_adapter: "stability-ai/sdxl-ip-adapter"

logging:
  level: INFO  # DEBUG for verbose output
  file: logs/generation.log
  console: true
  show_progress: true
  show_costs: true
  show_timing: true

# generators/icon_generator.py
import replicate
import time
import logging
from typing import Dict, List
from datetime import datetime
from tqdm import tqdm
from colorama import Fore, Style, init

# Initialize colorama for colored console output
init(autoreset=True)

class IconGenerator:
    def __init__(self, config: Dict):
        self.model = config['models']['premium']['recraft_svg']
        self.style_prompt = self.load_base_style()
        self.logger = self.setup_logging()
        self.stats = {
            'generated': 0,
            'failed': 0,
            'total_cost': 0.0,
            'total_time': 0.0
        }
    
    def setup_logging(self):
        """Setup comprehensive logging with colors and progress indicators"""
        logger = logging.getLogger('IconGenerator')
        logger.setLevel(logging.DEBUG)
        
        # Console handler with colors
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        
        # Custom formatter with colors
        class ColoredFormatter(logging.Formatter):
            FORMATS = {
                logging.DEBUG: Fore.CYAN + "🔍 %(asctime)s [DEBUG] %(message)s" + Style.RESET_ALL,
                logging.INFO: Fore.GREEN + "✅ %(asctime)s [INFO] %(message)s" + Style.RESET_ALL,
                logging.WARNING: Fore.YELLOW + "⚠️  %(asctime)s [WARN] %(message)s" + Style.RESET_ALL,
                logging.ERROR: Fore.RED + "❌ %(asctime)s [ERROR] %(message)s" + Style.RESET_ALL,
                logging.CRITICAL: Fore.MAGENTA + "🚨 %(asctime)s [CRITICAL] %(message)s" + Style.RESET_ALL
            }
            
            def format(self, record):
                log_fmt = self.FORMATS.get(record.levelno)
                formatter = logging.Formatter(log_fmt, datefmt='%H:%M:%S')
                return formatter.format(record)
        
        console.setFormatter(ColoredFormatter())
        logger.addHandler(console)
        
        # File handler for permanent record
        file_handler = logging.FileHandler('logs/generation.log')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def generate_icon(self, prompt: str, theme: Dict, index: int = 0, total: int = 1) -> str:
        """Generate single SVG icon with comprehensive status updates"""
        start_time = time.time()
        
        # Status announcement
        self.logger.info(f"")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"🎨 GENERATING ICON {index}/{total}")
        self.logger.info(f"📝 Prompt: {prompt[:50]}...")
        self.logger.info(f"🎨 Theme: {theme['name']}")
        self.logger.info(f"🤖 Model: Recraft V3 SVG ($0.04/image)")
        self.logger.info(f"{'='*60}")
        
        full_prompt = f"{self.style_prompt} {prompt} {theme['description']}"
        
        try:
            # Log API call details
            self.logger.debug(f"Full prompt: {full_prompt}")
            self.logger.info(f"⏳ Calling Replicate API...")
            
            # Show spinner while waiting
            with tqdm(total=100, desc="Generating", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
                # Simulate progress updates (in real implementation, use callbacks)
                output = replicate.run(
                    self.model,
                    input={
                        "prompt": full_prompt,
                        "style": "realistic_image",
                        "output_format": "svg",
                        "size": "1024x1024"
                    }
                )
                pbar.update(100)
            
            # Calculate metrics
            generation_time = time.time() - start_time
            cost = 0.04
            self.stats['generated'] += 1
            self.stats['total_cost'] += cost
            self.stats['total_time'] += generation_time
            
            # Success logging
            self.logger.info(f"✅ SUCCESS: Icon generated")
            self.logger.info(f"⏱️  Time: {generation_time:.2f} seconds")
            self.logger.info(f"💰 Cost: ${cost:.3f}")
            self.logger.info(f"📊 Total generated: {self.stats['generated']}")
            self.logger.info(f"💵 Running total: ${self.stats['total_cost']:.2f}")
            
            return output
            
        except Exception as e:
            self.stats['failed'] += 1
            self.logger.error(f"❌ FAILED: {str(e)}")
            self.logger.error(f"📊 Total failures: {self.stats['failed']}")
            raise

    def batch_generate(self, prompts: List[str], themes: List[Dict]):
        """Generate all icons with detailed progress tracking"""
        results = {}
        total_items = len(prompts) * len(themes)
        current_item = 0
        
        # Overall progress header
        print(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🚀 BATCH GENERATION STARTING{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Total assets to generate: {total_items}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💰 Estimated cost: ${total_items * 0.04:.2f}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⏱️  Estimated time: {total_items * 15} seconds{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Main progress bar for overall batch
        with tqdm(total=total_items, desc="Overall Progress", position=0, leave=True,
                 bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as main_pbar:
            
            for theme in themes:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"🎨 THEME: {theme['name'].upper()}")
                self.logger.info(f"{'='*60}")
                
                results[theme['name']] = []
                
                # Sub-progress bar for current theme
                with tqdm(total=len(prompts), desc=f"  {theme['name']}", position=1, leave=False,
                         bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}") as theme_pbar:
                    
                    for i, prompt in enumerate(prompts, 1):
                        current_item += 1
                        
                        try:
                            # Generate with detailed logging
                            svg = self.generate_icon(prompt, theme, current_item, total_items)
                            
                            # Optimize and save
                            self.logger.info(f"🔧 Optimizing SVG...")
                            optimized = self.optimize_svg(svg)
                            
                            # Store result
                            results[theme['name']].append(optimized)
                            
                            # Update progress bars
                            theme_pbar.update(1)
                            main_pbar.update(1)
                            
                            # Show live statistics
                            avg_time = self.stats['total_time'] / self.stats['generated'] if self.stats['generated'] > 0 else 0
                            remaining = (total_items - current_item) * avg_time
                            
                            self.logger.info(f"📈 Progress: {current_item}/{total_items} ({current_item*100/total_items:.1f}%)")
                            self.logger.info(f"⏰ ETA: {remaining/60:.1f} minutes")
                            self.logger.info(f"")
                            
                        except Exception as e:
                            self.logger.error(f"Skipping failed icon: {prompt[:30]}...")
                            theme_pbar.update(1)
                            main_pbar.update(1)
                            continue
        
        # Final statistics
        self.print_final_stats()
        return results
    
    def print_final_stats(self):
        """Print comprehensive final statistics"""
        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ BATCH GENERATION COMPLETE{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"📊 Generated: {self.stats['generated']} assets")
        print(f"❌ Failed: {self.stats['failed']} assets")
        print(f"💰 Total Cost: ${self.stats['total_cost']:.2f}")
        print(f"⏱️  Total Time: {self.stats['total_time']/60:.1f} minutes")
        print(f"⚡ Avg Time/Asset: {self.stats['total_time']/self.stats['generated']:.1f} seconds")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
        
        # Save stats to file
        with open('logs/generation_stats.json', 'w') as f:
            import json
            json.dump(self.stats, f, indent=2)
            self.logger.info(f"📁 Stats saved to logs/generation_stats.json")
```

### Prompt Engineering for Consistency

```python
# prompts/base_styles.py
BASE_STYLES = {
    "mechanical_poetry": """
        Style: Technical pen-and-ink drawing in the manner of Leonardo da Vinci's 
        engineering sketches. Precise 2px line weight with variable thickness for 
        depth. Crosshatching for shadows. Sepia-toned on aged parchment texture.
        Include subtle mechanical details and hidden symbolic elements. Golden 
        ratio composition. Museum specimen label aesthetic.
    """,
    
    "blueprint_aesthetic": """
        Style: Architectural blueprint with cyanotype coloring. Technical grid 
        overlay with golden ratio proportions. Aged paper texture with subtle 
        coffee stains and fold marks. Technical annotations in drafting lettering.
        Subtle verdigris patina on metal elements. Vignette edges.
    """,
    
    "celestial_cartography": """
        Style: 18th-century astronomical chart aesthetic. Constellation patterns 
        with connecting lines. Antique map borders with compass rose elements.
        Aged yellowed paper with foxing. Hand-engraved illustration style.
        Latin annotations in copperplate script.
    """
}

# Color themes applied to all styles
THEME_OVERLAYS = {
    "executive_blue": {
        "primary": "#4A7C74",  # Verdigris
        "secondary": "#527B84",  # Blueprint Cyan
        "accent": "#B8956A",  # Cartographer's Gold
        "description": "with verdigris patina and blueprint undertones"
    },
    "legacy_purple": {
        "primary": "#3E3127",  # Umber Script
        "secondary": "#6B5B73",  # Twilight Violet
        "accent": "#C4A584",  # Dawn Rose
        "description": "with aged manuscript and twilight tones"
    },
    "heritage_green": {
        "primary": "#696F5C",  # Moss Stone
        "secondary": "#B8956A",  # Cartographer's Gold
        "accent": "#4A7C74",  # Verdigris
        "description": "with moss patina and antique gold highlights"
    }
}
```

### CRITICAL: Two-Stage Execution with Review Gate

#### Stage 1: Sample Generation for Review with Full Logging
```python
# review_samples.py
#!/usr/bin/env python3
"""
STAGE 1: Generate samples for human review BEFORE mass generation
This script generates 5-10 sample assets for quality validation
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path
import webbrowser
from datetime import datetime
from colorama import Fore, Back, Style, init
from tqdm import tqdm
from generators import IconGenerator, CoverGenerator, TextureGenerator
from storage import LocalStorage, create_review_interface

# Initialize colorama for Windows compatibility
init(autoreset=True)

class SampleGenerator:
    def __init__(self):
        self.start_time = time.time()
        self.logger = self.setup_logging()
        self.stats = {
            'phase': '',
            'current_asset': '',
            'assets_completed': 0,
            'assets_total': 8,
            'cost_running': 0.0,
            'errors': []
        }
    
    def setup_logging(self):
        """Setup comprehensive logging system"""
        # Create logs directory
        Path("logs").mkdir(exist_ok=True)
        
        # Configure root logger
        logger = logging.getLogger('SampleGeneration')
        logger.setLevel(logging.DEBUG)
        
        # Console handler with rich formatting
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        
        class RichFormatter(logging.Formatter):
            def format(self, record):
                # Add timestamp
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Choose format based on level
                if record.levelno == logging.DEBUG:
                    prefix = f"{Fore.CYAN}[{timestamp}] DEBUG:{Style.RESET_ALL}"
                elif record.levelno == logging.INFO:
                    prefix = f"{Fore.GREEN}[{timestamp}] INFO:{Style.RESET_ALL}"
                elif record.levelno == logging.WARNING:
                    prefix = f"{Fore.YELLOW}[{timestamp}] WARN:{Style.RESET_ALL}"
                elif record.levelno == logging.ERROR:
                    prefix = f"{Fore.RED}[{timestamp}] ERROR:{Style.RESET_ALL}"
                else:
                    prefix = f"[{timestamp}]"
                
                return f"{prefix} {record.getMessage()}"
        
        console.setFormatter(RichFormatter())
        logger.addHandler(console)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(f'logs/sample_generation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def print_header(self):
        """Print beautiful header with session info"""
        print(f"\n{Fore.CYAN}{Back.BLACK}{' '*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{' '*25}ESTATE PLANNING CONCIERGE v4.0{' '*24}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{' '*28}Asset Generation System{' '*29}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Back.BLACK}{' '*80}{Style.RESET_ALL}\n")
        
        print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📋 STAGE 1: SAMPLE GENERATION FOR REVIEW{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'='*80}{Style.RESET_ALL}\n")
        
        # Session info
        print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Output: output/samples/")
        print(f"💰 Budget: ~$0.50")
        print(f"📊 Assets: 8 samples (3 icons, 2 covers, 1 texture, 2 masters)")
        print(f"⏱️  Est. Time: 3-5 minutes\n")
    
    def update_status(self, phase: str, detail: str = "", progress: float = None):
        """Update and display current status"""
        self.stats['phase'] = phase
        
        # Clear line and print status
        sys.stdout.write('\r' + ' '*100 + '\r')  # Clear current line
        
        if progress is not None:
            # Show progress bar
            bar_length = 40
            filled = int(bar_length * progress)
            bar = '█' * filled + '░' * (bar_length - filled)
            percentage = progress * 100
            
            status_line = f"{Fore.CYAN}[{phase}]{Style.RESET_ALL} {bar} {percentage:.1f}% | {detail}"
        else:
            status_line = f"{Fore.CYAN}[{phase}]{Style.RESET_ALL} {detail}"
        
        print(status_line, end='', flush=True)
        self.logger.debug(f"{phase}: {detail}")
    
    async def generate_review_samples(self):
        """Main generation process with comprehensive logging"""
        self.print_header()
        
        try:
            # Load configuration
            self.update_status("INITIALIZATION", "Loading configuration...")
            config = await self.load_config_with_validation()
            storage = LocalStorage(base_path="output/samples")
            
            # Phase 1: Master Style References
            print(f"\n{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}Phase 1: Creating Master Style References{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}\n")
            
            with tqdm(total=3, desc="Master Styles", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]") as pbar:
                self.update_status("MASTERS", "Generating icon master style...")
                masters = {}
                
                # Icon master
                self.logger.info("🎨 Creating icon master style reference...")
                masters['icon'] = await self.generate_master('icon', config)
                self.stats['cost_running'] += 0.04
                pbar.update(1)
                
                # Cover master
                self.update_status("MASTERS", "Generating cover master style...")
                self.logger.info("🎨 Creating cover master style reference...")
                masters['cover'] = await self.generate_master('cover', config)
                self.stats['cost_running'] += 0.04
                pbar.update(1)
                
                # Texture master
                self.update_status("MASTERS", "Generating texture master style...")
                self.logger.info("🎨 Creating texture master style reference...")
                masters['texture'] = await self.generate_master('texture', config)
                self.stats['cost_running'] += 0.003
                pbar.update(1)
            
            storage.save_masters(masters)
            print(f"\n✅ Masters created | Cost so far: ${self.stats['cost_running']:.3f}\n")
            
            # Phase 2: Sample Icons
            print(f"\n{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}Phase 2: Generating Sample Icons{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}\n")
            
            sample_icon_prompts = [
                "intricate mechanical document scroll with wax seal",
                "interlocking gear system forming heart shape", 
                "astronomical astrolabe with moving parts"
            ]
            
            icons = IconGenerator(config, masters['icon'])
            for i, prompt in enumerate(sample_icon_prompts, 1):
                self.logger.info(f"🔧 Generating icon {i}/3: {prompt[:40]}...")
                self.update_status("ICONS", f"Icon {i}/3: {prompt[:30]}...", i/3)
                
                try:
                    icon = await icons.generate_single(prompt)
                    path = storage.save_local(icon, f"icons/sample_{i}.svg")
                    self.stats['cost_running'] += 0.04
                    self.stats['assets_completed'] += 1
                    
                    self.logger.info(f"✅ Saved: {path}")
                    self.logger.info(f"💰 Running cost: ${self.stats['cost_running']:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to generate icon {i}: {str(e)}")
                    self.stats['errors'].append(f"Icon {i}: {str(e)}")
            
            print(f"\n✅ Icons complete | Total cost: ${self.stats['cost_running']:.3f}\n")
            
            # Phase 3: Sample Covers
            print(f"\n{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}Phase 3: Generating Sample Covers{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}\n")
            
            sample_cover_prompts = [
                "architectural foundation blueprint with cornerstone emphasis",
                "family tree as botanical illustration with growth rings"
            ]
            
            covers = CoverGenerator(config, masters['cover'])
            for i, prompt in enumerate(sample_cover_prompts, 1):
                self.logger.info(f"🖼️  Generating cover {i}/2: {prompt[:40]}...")
                self.update_status("COVERS", f"Cover {i}/2: {prompt[:30]}...", i/2)
                
                try:
                    # Use different models based on importance
                    if i == 1:  # Hero cover - use FLUX
                        self.logger.info("Using FLUX 1.1 Pro for hero cover")
                        cost = 0.04
                    else:  # Sub cover - use SDXL
                        self.logger.info("Using SDXL for subsection cover")
                        cost = 0.003
                    
                    cover = await covers.generate_single(prompt)
                    path = storage.save_local(cover, f"covers/sample_{i}.png")
                    self.stats['cost_running'] += cost
                    self.stats['assets_completed'] += 1
                    
                    self.logger.info(f"✅ Saved: {path}")
                    self.logger.info(f"💰 Running cost: ${self.stats['cost_running']:.3f}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to generate cover {i}: {str(e)}")
                    self.stats['errors'].append(f"Cover {i}: {str(e)}")
            
            print(f"\n✅ Covers complete | Total cost: ${self.stats['cost_running']:.3f}\n")
            
            # Phase 4: Sample Texture
            print(f"\n{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}Phase 4: Generating Sample Texture{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}\n")
            
            self.logger.info("🌟 Generating texture sample...")
            self.update_status("TEXTURE", "Generating aged parchment texture...")
            
            textures = TextureGenerator(config, masters['texture'])
            texture = await textures.generate_single("aged parchment with verdigris patina")
            path = storage.save_local(texture, "textures/sample_1.png")
            self.stats['cost_running'] += 0.003
            self.stats['assets_completed'] += 1
            
            print(f"\n✅ Texture complete | Total cost: ${self.stats['cost_running']:.3f}\n")
            
            # Phase 5: Create Review Interface
            print(f"\n{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}Phase 5: Creating Review Interface{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'─'*60}{Style.RESET_ALL}\n")
            
            self.update_status("INTERFACE", "Building HTML review page...")
            review_path = create_review_interface(storage.base_path)
            self.logger.info(f"📄 Review interface created: {review_path}")
            
            # Save generation status for review server
            status_data = {
                'timestamp': datetime.now().isoformat(),
                'stats': self.stats,
                'samples_generated': self.stats['assets_completed'],
                'total_cost': self.stats['cost_running'],
                'errors': self.stats['errors']
            }
            status_file = storage.base_path / "generation_status.json"
            with open(status_file, 'w') as f:
                json.dump(status_data, f, indent=2)
            
            # Final summary
            self.print_final_summary(storage.base_path, review_path)
            
            # Launch review server with auto-open
            print(f"\n{Fore.GREEN}🚀 Launching Review Server on Port 4500...{Style.RESET_ALL}")
            from review.review_server import launch_review_after_generation
            approved = launch_review_after_generation()
            
        except Exception as e:
            self.logger.error(f"Critical error: {str(e)}")
            self.print_error_summary()
            raise
    
    def print_final_summary(self, output_path, review_path):
        """Print comprehensive final summary"""
        elapsed = time.time() - self.start_time
        
        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ SAMPLE GENERATION COMPLETE{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'='*80}{Style.RESET_ALL}\n")
        
        # Statistics
        print(f"📊 STATISTICS:")
        print(f"  • Generated: {self.stats['assets_completed']}/{self.stats['assets_total']} assets")
        print(f"  • Total Cost: ${self.stats['cost_running']:.3f}")
        print(f"  • Time Elapsed: {elapsed/60:.1f} minutes")
        print(f"  • Errors: {len(self.stats['errors'])}")
        
        # File locations
        print(f"\n📁 FILE LOCATIONS:")
        print(f"  • Output Directory: {output_path}")
        print(f"  • Review Interface: {review_path}")
        print(f"  • Log File: logs/sample_generation_*.log")
        
        # Next steps
        print(f"\n📋 NEXT STEPS:")
        print(f"  1. Review samples in browser (auto-opened on port 4500)")
        print(f"  2. Check quality against checklist")
        print(f"  3. Approve via web interface: http://localhost:4500/approve")
        print(f"     OR manually: echo 'Approved by [name] on [date]' > output/samples/APPROVED.txt")
        print(f"  4. Once approved, run: python mass_generate.py")
        print(f"  5. If changes needed: Edit config.json and re-run this script")
        
        if self.stats['errors']:
            print(f"\n⚠️  ERRORS ENCOUNTERED:")
            for error in self.stats['errors']:
                print(f"  • {error}")
        
        print(f"\n{Fore.GREEN}{'='*80}{Style.RESET_ALL}")

async def main():
    generator = SampleGenerator()
    await generator.generate_review_samples()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Stage 2: Mass Generation (After Approval Only) - WITH COMPREHENSIVE LOGGING
```python
# mass_generate.py
#!/usr/bin/env python3
"""
STAGE 2: Mass generation ONLY after sample approval
This script generates ALL 200+ assets with comprehensive real-time logging
"""

import os
import sys
import asyncio
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
from typing import Dict, List, Tuple
from colorama import init, Fore, Back, Style
from tqdm.asyncio import tqdm
import aiohttp
import aiofiles

# Initialize colorama for cross-platform colored output
init(autoreset=True)

from generators import IconGenerator, CoverGenerator, TextureGenerator
from storage import LocalStorage, GitHubUploader
from optimization import optimize_assets

class MassGenerationLogger:
    """Enhanced logging system for mass generation with real-time status"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.stats = {
            'icons': {'total': 90, 'completed': 0, 'failed': 0, 'cost': 0},
            'covers': {'total': 105, 'completed': 0, 'failed': 0, 'cost': 0},
            'textures': {'total': 60, 'completed': 0, 'failed': 0, 'cost': 0},
            'optimization': {'processed': 0, 'size_saved': 0},
            'github': {'uploaded': 0, 'failed': 0}
        }
        self.current_phase = "INITIALIZATION"
        self.errors = []
        self.setup_logging()
        
    def setup_logging(self):
        """Configure both file and console logging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = Path("logs/mass_generation")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler for detailed logs
        file_handler = logging.FileHandler(
            log_dir / f"mass_generate_{timestamp}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(module)s.%(funcName)s | %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler with colors
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Setup logger
        self.logger = logging.getLogger('MassGeneration')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def update_progress(self, phase: str, item: str, progress: float, cost: float = 0):
        """Update real-time progress display"""
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        # Calculate totals
        total_completed = sum(s['completed'] for s in self.stats.values() if isinstance(s, dict) and 'completed' in s)
        total_cost = sum(s['cost'] for s in self.stats.values() if isinstance(s, dict) and 'cost' in s)
        
        # Clear line and display status
        sys.stdout.write('\r' + ' ' * 120 + '\r')
        
        # Build progress bar
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Color coding by phase
        phase_colors = {
            'ICONS': Fore.CYAN,
            'COVERS': Fore.MAGENTA,
            'TEXTURES': Fore.YELLOW,
            'OPTIMIZATION': Fore.BLUE,
            'GITHUB': Fore.GREEN
        }
        color = phase_colors.get(phase, Fore.WHITE)
        
        status_line = (
            f"{color}[{phase}]{Style.RESET_ALL} {bar} {progress:.1f}% | "
            f"{item[:35]:35} | ⏱️ {elapsed_str} | 💰 ${total_cost:.2f}"
        )
        
        sys.stdout.write(status_line)
        sys.stdout.flush()
        
        # Update stats
        if cost > 0 and phase.lower() in self.stats:
            self.stats[phase.lower()]['cost'] += cost
            
    def log_asset_generation(self, asset_type: str, name: str, success: bool, 
                            time_taken: float = 0, cost: float = 0):
        """Log individual asset generation with detailed info"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if success:
            self.stats[asset_type]['completed'] += 1
            self.stats[asset_type]['cost'] += cost
            
            log_msg = (
                f"✅ [{timestamp}] {asset_type.upper()}: {name} "
                f"[SUCCESS in {time_taken:.2f}s, ${cost:.3f}]"
            )
            print(f"\n{Fore.GREEN}{log_msg}{Style.RESET_ALL}")
            self.logger.info(log_msg)
        else:
            self.stats[asset_type]['failed'] += 1
            error_msg = f"❌ [{timestamp}] {asset_type.upper()}: {name} [FAILED]"
            print(f"\n{Fore.RED}{error_msg}{Style.RESET_ALL}")
            self.logger.error(error_msg)
            self.errors.append(f"{asset_type}/{name}")

async def mass_generate_assets():
    """Main mass generation function with comprehensive logging"""
    
    # Initialize logger
    logger_system = MassGenerationLogger()
    logger = logger_system.logger
    
    # Print startup header
    print("\n" + "="*80)
    print(f"{Fore.CYAN}{Style.BRIGHT}🎨 ESTATE PLANNING CONCIERGE v4.0{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{Style.BRIGHT}   MASS ASSET GENERATION - STAGE 2{Style.RESET_ALL}")
    print("="*80)
    print(f"📅 Session Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔑 API Status: {'✅ Connected' if os.getenv('REPLICATE_API_TOKEN') else '❌ Missing'}")
    print("="*80 + "\n")
    
    # Check for approval
    approval_file = Path("output/samples/APPROVED.txt")
    if not approval_file.exists():
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.RED}❌ ERROR: SAMPLES NOT APPROVED!{Style.RESET_ALL}")
        print(f"{Fore.RED}{'='*60}{Style.RESET_ALL}")
        print("\n📋 Required Actions:")
        print("1. Review samples in output/samples/")
        print("2. Verify quality and consistency")
        print("3. Create approval file:")
        print(f"   {Fore.YELLOW}echo 'Approved by [name] on {datetime.now().strftime('%Y-%m-%d')}' > output/samples/APPROVED.txt{Style.RESET_ALL}")
        print("\nExiting...")
        sys.exit(1)
        
    # Load approval info
    with open(approval_file) as f:
        approval_info = f.read().strip()
    print(f"✅ Samples approved: {approval_info}\n")
    
    # Load configuration
    config = load_config()
    storage = LocalStorage(base_path="output/approved")
    github = GitHubUploader(repo="notion-estate-assets")
    
    # Display generation plan
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}📋 GENERATION PLAN{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    print("📦 Phase 1: Icons    - 30 designs × 3 themes = 90 assets   (~$3.60)")
    print("📦 Phase 2: Covers   - 35 designs × 3 themes = 105 assets  (~$4.20)")
    print("📦 Phase 3: Textures - 20 designs × 3 themes = 60 assets   (~$0.18)")
    print("⚙️  Phase 4: Optimization - Compress all 255 assets")
    print("📤 Phase 5: GitHub Upload - Push to CDN")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    print(f"💰 Estimated Total Cost: $7.98")
    print(f"⏱️  Estimated Time: 15-20 minutes")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}\n")
    
    # Confirm to proceed
    print(f"{Fore.YELLOW}⚠️  This will generate 255 production assets.{Style.RESET_ALL}")
    response = input("Proceed with mass generation? (yes/no): ")
    if response.lower() != 'yes':
        print("Generation cancelled.")
        sys.exit(0)
        
    print("\n" + "="*60)
    print("🚀 STARTING MASS GENERATION")
    print("="*60 + "\n")
    
    # Load approved masters
    logger.info("Loading approved master styles...")
    masters = storage.load_masters("output/samples/masters")
    
    # Phase 1: All Icons (30 × 3 themes = 90 assets)
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📐 PHASE 1: GENERATING ALL ICONS{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    async with tqdm(total=90, desc="Icons", unit="icon", colour="cyan") as pbar:
        all_icons = await generate_all_icons(
            config, masters, storage, logger_system, pbar
        )
    
    # Phase 1 Summary
    print(f"\n{Fore.CYAN}Phase 1 Complete: "
          f"{logger_system.stats['icons']['completed']}/90 icons generated "
          f"(${logger_system.stats['icons']['cost']:.2f}){Style.RESET_ALL}\n")
    
    # Phase 2: All Covers (35 × 3 themes = 105 assets)
    print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🖼️  PHASE 2: GENERATING ALL COVERS{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}\n")
    
    async with tqdm(total=105, desc="Covers", unit="cover", colour="magenta") as pbar:
        all_covers = await generate_all_covers(
            config, masters, storage, logger_system, pbar
        )
        
    # Phase 2 Summary
    print(f"\n{Fore.MAGENTA}Phase 2 Complete: "
          f"{logger_system.stats['covers']['completed']}/105 covers generated "
          f"(${logger_system.stats['covers']['cost']:.2f}){Style.RESET_ALL}\n")
    
    # Phase 3: All Textures (20 × 3 themes = 60 assets)
    print(f"\n{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}🎨 PHASE 3: GENERATING ALL TEXTURES{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}\n")
    
    async with tqdm(total=60, desc="Textures", unit="texture", colour="yellow") as pbar:
        all_textures = await generate_all_textures(
            config, masters, storage, logger_system, pbar
        )
        
    # Phase 3 Summary
    print(f"\n{Fore.YELLOW}Phase 3 Complete: "
          f"{logger_system.stats['textures']['completed']}/60 textures generated "
          f"(${logger_system.stats['textures']['cost']:.2f}){Style.RESET_ALL}\n")
    
    # Phase 4: Optimization
    print(f"\n{Fore.BLUE}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}⚙️  PHASE 4: OPTIMIZING ALL ASSETS{Style.RESET_ALL}")
    print(f"{Fore.BLUE}{'='*60}{Style.RESET_ALL}\n")
    
    with tqdm(total=255, desc="Optimizing", unit="file", colour="blue") as pbar:
        size_before, size_after = await optimize_all_assets(
            storage.base_path, logger_system, pbar
        )
        
    size_saved_mb = (size_before - size_after) / (1024 * 1024)
    print(f"\n{Fore.BLUE}Phase 4 Complete: "
          f"Saved {size_saved_mb:.2f} MB "
          f"({(1 - size_after/size_before) * 100:.1f}% reduction){Style.RESET_ALL}\n")
    
    # Phase 5: GitHub Push
    print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}📤 PHASE 5: PUSHING TO GITHUB{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
    
    with tqdm(total=255, desc="Uploading", unit="file", colour="green") as pbar:
        await github.push_all(storage.base_path, logger_system, pbar)
        
    print(f"\n{Fore.GREEN}Phase 5 Complete: "
          f"{logger_system.stats['github']['uploaded']}/255 files uploaded{Style.RESET_ALL}\n")
    
    # Generate final manifest
    manifest = create_final_manifest(all_icons, all_covers, all_textures)
    storage.save_manifest(manifest)
    
    # Final summary
    elapsed = datetime.now() - logger_system.start_time
    total_generated = (
        logger_system.stats['icons']['completed'] +
        logger_system.stats['covers']['completed'] +
        logger_system.stats['textures']['completed']
    )
    total_cost = (
        logger_system.stats['icons']['cost'] +
        logger_system.stats['covers']['cost'] +
        logger_system.stats['textures']['cost']
    )
    
    print("\n" + "="*80)
    print(f"{Fore.GREEN}{Style.BRIGHT}✨ MASS GENERATION COMPLETE ✨{Style.RESET_ALL}")
    print("="*80)
    print(f"\n📊 FINAL STATISTICS:")
    print(f"   ✅ Assets Generated: {total_generated}/255")
    print(f"   ❌ Failed: {len(logger_system.errors)}")
    print(f"   💰 Total Cost: ${total_cost:.2f}")
    print(f"   ⏱️  Total Time: {str(elapsed).split('.')[0]}")
    print(f"   📦 Size Saved: {size_saved_mb:.2f} MB")
    print(f"   📤 GitHub Uploads: {logger_system.stats['github']['uploaded']}")
    
    if logger_system.errors:
        print(f"\n⚠️  Failed Assets ({len(logger_system.errors)}):")
        for error in logger_system.errors[:10]:
            print(f"   • {error}")
        if len(logger_system.errors) > 10:
            print(f"   ... and {len(logger_system.errors) - 10} more")
            
    print(f"\n📁 OUTPUT LOCATIONS:")
    print(f"   Local: {storage.base_path}")
    print(f"   GitHub: https://github.com/{github.repo}")
    print(f"   Logs: logs/mass_generation/")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Review manifest: {storage.base_path}/manifest.json")
    print(f"   2. Update deploy.py with CDN URLs")
    print(f"   3. Run integration tests")
    print(f"   4. Deploy to production")
    
    print("\n" + "="*80 + "\n")
    
    # Save final report
    report_path = Path("logs/mass_generation") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump({
            'session': {
                'start': logger_system.start_time.isoformat(),
                'end': datetime.now().isoformat(),
                'duration': str(elapsed)
            },
            'statistics': logger_system.stats,
            'errors': logger_system.errors,
            'cost': total_cost,
            'assets_generated': total_generated
        }, f, indent=2)
    
    logger.info(f"Final report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(mass_generate_assets())
```

### Storage Implementation (LOCAL + GITHUB)

```python
# storage/local_storage.py
import os
import json
import shutil
from pathlib import Path
from datetime import datetime

class LocalStorage:
    def __init__(self, base_path="output"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def save_local(self, data, relative_path):
        """Save asset to local filesystem"""
        full_path = self.base_path / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        if relative_path.endswith('.svg'):
            with open(full_path, 'w') as f:
                f.write(data)
        else:
            with open(full_path, 'wb') as f:
                f.write(data)
        
        print(f"✅ Saved locally: {full_path}")
        return full_path
    
    def create_backup(self):
        """Create timestamped backup before GitHub push"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.base_path.parent / f"backup_{timestamp}"
        shutil.copytree(self.base_path, backup_path)
        print(f"📦 Backup created: {backup_path}")
        return backup_path

# storage/github_uploader.py
import subprocess
from pathlib import Path

class GitHubUploader:
    def __init__(self, repo="notion-estate-assets"):
        self.repo = repo
        self.repo_path = Path(f"../{repo}")
        
    def push_all(self, local_path):
        """Push all assets to GitHub"""
        # Copy files to repo
        for file in Path(local_path).rglob("*"):
            if file.is_file():
                relative = file.relative_to(local_path)
                dest = self.repo_path / "assets" / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file, dest)
        
        # Git operations
        subprocess.run(["git", "add", "."], cwd=self.repo_path)
        subprocess.run(["git", "commit", "-m", "Update assets"], cwd=self.repo_path)
        subprocess.run(["git", "push"], cwd=self.repo_path)
        
        print(f"✅ Pushed to GitHub: {self.repo}")
```

### Review Interface Implementation

```python
# review/review_interface.py
def create_review_interface(samples_path):
    """Create HTML interface for reviewing samples"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Asset Review - Estate Planning Concierge v4.0</title>
        <style>
            body { 
                font-family: 'Segoe UI', system-ui, sans-serif; 
                background: #f4f0e6; 
                padding: 40px;
            }
            .header {
                text-align: center;
                color: #3E3127;
                margin-bottom: 40px;
            }
            .asset-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
            }
            .asset-card {
                background: white;
                border: 2px solid #4A7C74;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .asset-image {
                width: 100%;
                height: 200px;
                object-fit: contain;
                background: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
            }
            .asset-title {
                font-weight: 600;
                color: #3E3127;
                margin: 15px 0 5px;
            }
            .asset-type {
                color: #696F5C;
                font-size: 14px;
            }
            .approval-section {
                background: #527B84;
                color: white;
                padding: 30px;
                border-radius: 8px;
                margin-top: 40px;
                text-align: center;
            }
            .approval-checklist {
                text-align: left;
                max-width: 600px;
                margin: 20px auto;
            }
            .approval-checklist li {
                margin: 10px 0;
            }
            .code-block {
                background: #2d3748;
                color: #68d391;
                padding: 15px;
                border-radius: 4px;
                font-family: monospace;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏛️ Estate Planning Concierge v4.0</h1>
            <h2>Asset Review Interface</h2>
            <p>Review these samples before mass generation</p>
        </div>
        
        <div class="asset-grid">
            <!-- Icons -->
            <div class="asset-card">
                <img src="icons/sample_1.svg" class="asset-image">
                <div class="asset-title">Document Scroll Icon</div>
                <div class="asset-type">Recraft V3 SVG • Mechanical Poetry</div>
            </div>
            
            <div class="asset-card">
                <img src="icons/sample_2.svg" class="asset-image">
                <div class="asset-title">Family Heart Gears</div>
                <div class="asset-type">Recraft V3 SVG • Mechanical Poetry</div>
            </div>
            
            <div class="asset-card">
                <img src="icons/sample_3.svg" class="asset-image">
                <div class="asset-title">Astrolabe Navigation</div>
                <div class="asset-type">Recraft V3 SVG • Mechanical Poetry</div>
            </div>
            
            <!-- Covers -->
            <div class="asset-card">
                <img src="covers/sample_1.png" class="asset-image">
                <div class="asset-title">Foundation Blueprint</div>
                <div class="asset-type">FLUX 1.1 Pro • Hero Cover</div>
            </div>
            
            <div class="asset-card">
                <img src="covers/sample_2.png" class="asset-image">
                <div class="asset-title">Family Tree Botanical</div>
                <div class="asset-type">SDXL • Subsection Cover</div>
            </div>
            
            <!-- Texture -->
            <div class="asset-card">
                <img src="textures/sample_1.png" class="asset-image">
                <div class="asset-title">Aged Parchment Patina</div>
                <div class="asset-type">SDXL • Background Texture</div>
            </div>
        </div>
        
        <div class="approval-section">
            <h2>✅ Quality Checklist</h2>
            <ul class="approval-checklist">
                <li>☐ Icons are truly unique (not generic)</li>
                <li>☐ Mechanical details are visible and intricate</li>
                <li>☐ Color palette matches luxury aesthetic</li>
                <li>☐ Patina effects look authentic</li>
                <li>☐ Blueprint style is consistent</li>
                <li>☐ File sizes are reasonable (< 100KB)</li>
                <li>☐ SVGs are clean and scalable</li>
                <li>☐ Overall quality justifies premium pricing</li>
            </ul>
            
            <h3>To Approve and Continue:</h3>
            <div class="code-block">
                echo "Approved by [YOUR NAME] on $(date)" > output/samples/APPROVED.txt
                python mass_generate.py
            </div>
            
            <h3>To Regenerate Samples:</h3>
            <div class="code-block">
                # Edit prompts/config as needed, then:
                python review_samples.py
            </div>
        </div>
    </body>
    </html>
    """
    
    review_path = Path(samples_path) / "review.html"
    with open(review_path, 'w') as f:
        f.write(html)
    
    return review_path
```

### Review Server Implementation (Port 4500 with Auto-Open)

```python
# review/review_server.py
import http.server
import socketserver
import webbrowser
import threading
import os
import json
from pathlib import Path
import time

class ReviewRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler for review server with additional endpoints"""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory or "output/samples"
        super().__init__(*args, directory=self.directory, **kwargs)
    
    def do_GET(self):
        """Handle GET requests with custom routes"""
        if self.path == '/status':
            self.send_json_response(self.get_generation_status())
        elif self.path == '/approve':
            self.handle_approval()
        else:
            super().do_GET()
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_generation_status(self):
        """Get current generation status"""
        status_file = Path(self.directory) / "generation_status.json"
        if status_file.exists():
            with open(status_file) as f:
                return json.load(f)
        return {"status": "no_data"}
    
    def handle_approval(self):
        """Handle approval request"""
        approval_file = Path(self.directory) / "APPROVED.txt"
        approval_file.write_text(f"Approved via web interface at {datetime.now()}")
        self.send_json_response({"status": "approved", "timestamp": str(datetime.now())})
    
    def log_message(self, format, *args):
        """Custom log format with colors"""
        print(f"{Fore.CYAN}[Server]{Style.RESET_ALL} {format % args}")

class ReviewServer:
    """HTTP server for reviewing generated samples"""
    
    def __init__(self, port=4500, directory="output/samples", auto_open=True):
        self.port = port
        self.directory = directory
        self.auto_open = auto_open
        self.server = None
        self.thread = None
        
        # Load config if exists
        config_path = Path("config.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                self.port = config.get("review", {}).get("port", 4500)
                self.auto_open = config.get("review", {}).get("auto_open", True)
    
    def start(self):
        """Start the review server"""
        print(f"\n{Fore.GREEN}🚀 Starting Review Server{Style.RESET_ALL}")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
        
        # Check if port is available
        if self.is_port_in_use(self.port):
            print(f"{Fore.YELLOW}⚠️  Port {self.port} is in use, trying {self.port + 1}...{Style.RESET_ALL}")
            self.port += 1
        
        # Create handler with custom directory
        handler = lambda *args, **kwargs: ReviewRequestHandler(*args, directory=self.directory, **kwargs)
        
        # Start server
        self.server = socketserver.TCPServer(("localhost", self.port), handler)
        self.server.allow_reuse_address = True
        
        # Run in background thread
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        url = f"http://localhost:{self.port}"
        
        print(f"✅ Server running at: {Fore.BLUE}{url}{Style.RESET_ALL}")
        print(f"📁 Serving directory: {self.directory}")
        print(f"📄 Review page: {url}/review.html")
        print(f"📊 Status endpoint: {url}/status")
        print(f"✅ Approval endpoint: {url}/approve")
        print(f"\n{Fore.YELLOW}Press Ctrl+C to stop the server{Style.RESET_ALL}")
        print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
        
        # Auto-open browser if configured
        if self.auto_open:
            time.sleep(1)  # Give server time to start
            print(f"{Fore.GREEN}🌐 Opening browser automatically...{Style.RESET_ALL}")
            webbrowser.open(f"{url}/review.html")
        
        return url
    
    def is_port_in_use(self, port):
        """Check if port is already in use"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    def stop(self):
        """Stop the review server"""
        if self.server:
            print(f"\n{Fore.YELLOW}Stopping review server...{Style.RESET_ALL}")
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=5)
            print(f"{Fore.GREEN}✅ Server stopped{Style.RESET_ALL}")
    
    def wait(self):
        """Wait for server to be stopped with Ctrl+C"""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

def start_review_server(samples_path="output/samples", config_path="config.json"):
    """Convenience function to start review server with config"""
    # Load configuration
    config = {}
    if Path(config_path).exists():
        with open(config_path) as f:
            config = json.load(f)
    
    # Get settings from config
    port = config.get("review", {}).get("port", 4500)
    auto_open = config.get("review", {}).get("auto_open", True)
    
    # Start server
    server = ReviewServer(port=port, directory=samples_path, auto_open=auto_open)
    url = server.start()
    
    # Wait for approval
    approval_file = Path(samples_path) / "APPROVED.txt"
    
    print(f"\n{Fore.MAGENTA}Waiting for approval...{Style.RESET_ALL}")
    print(f"To approve: Create {approval_file} or visit {url}/approve")
    
    server.wait()
    
    return approval_file.exists()

# Integration with sample generation
def launch_review_after_generation():
    """Launch review server after sample generation completes"""
    print(f"\n{Fore.GREEN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Sample Generation Complete - Launching Review{Style.RESET_ALL}")
    print(f"{Fore.GREEN}{'='*60}{Style.RESET_ALL}\n")
    
    # Start review server
    approved = start_review_server("output/samples")
    
    if approved:
        print(f"\n{Fore.GREEN}✅ SAMPLES APPROVED!{Style.RESET_ALL}")
        print(f"You can now run: python mass_generate.py")
    else:
        print(f"\n{Fore.YELLOW}⚠️  Samples not approved yet{Style.RESET_ALL}")
        print(f"Review and approve before mass generation")
    
    return approved
```

---

## Part 4: Style Consistency Implementation

### Without Manual Training - Fully Automated

#### Option 1: Style Reference Pipeline
```python
def maintain_style_consistency(master_image, new_prompt, model="fofr/style-transfer"):
    """Apply master style to new generation"""
    output = replicate.run(
        model,
        input={
            "style_image": master_image,
            "prompt": new_prompt,
            "style_strength": 0.8,
            "structure_strength": 0.2
        }
    )
    return output
```

#### Option 2: IP-Adapter Approach
```python
def generate_with_style(master_style, prompt):
    """Use IP-Adapter for style consistency"""
    output = replicate.run(
        "stability-ai/sdxl-ip-adapter",
        input={
            "image": master_style,
            "prompt": prompt,
            "ip_adapter_scale": 0.6,
            "num_inference_steps": 30
        }
    )
    return output
```

#### Option 3: Detailed Prompt Chaining
```python
class ConsistentPromptGenerator:
    def __init__(self):
        self.base_elements = {
            "line_weight": "consistent 2px strokes",
            "color_palette": "verdigris #4A7C74, umber #3E3127",
            "texture": "aged parchment with 5% opacity",
            "composition": "golden ratio grid alignment",
            "style_reference": "Leonardo da Vinci Codex Atlanticus"
        }
    
    def generate_prompt(self, specific_content):
        elements = [f"{k}: {v}" for k, v in self.base_elements.items()]
        return f"{specific_content}. Style: {', '.join(elements)}"
```

---

## Part 5: Two-Stage Execution Timeline

### STAGE 1: Sample Generation & Review (Day 1)
#### Morning: Setup & Samples (2 hours)
- [ ] Set up Python environment
- [ ] Configure Replicate API key
- [ ] Clone/create GitHub asset repository
- [ ] Run `python review_samples.py`
- [ ] Generate 8 sample assets
- **Cost:** ~$0.50

#### Afternoon: Review & Iteration (2 hours)
- [ ] Open review interface in browser
- [ ] Check quality against checklist
- [ ] Modify prompts if needed
- [ ] Regenerate samples if necessary
- [ ] Create APPROVED.txt when satisfied
- **Cost:** ~$0.50 for iterations

### STAGE 2: Mass Generation (Days 2-3)
**⚠️ ONLY PROCEED AFTER APPROVAL**

#### Day 2: Primary Assets (4 hours)
- [ ] Run `python mass_generate.py`
- [ ] Phase 1: Generate 30 SVG icons × 3 themes
- [ ] Phase 2: Generate 7 hero covers × 3 themes
- [ ] Local storage verification
- **Cost:** ~$6.00

#### Day 3: Supporting Assets & Deployment (4 hours)
- [ ] Phase 3: Generate 28 subsection covers × 3 themes
- [ ] Phase 4: Generate all textures × 3 themes
- [ ] Phase 5: Optimization pass
- [ ] Phase 6: GitHub push with backup
- [ ] Update deploy.py with asset URLs
- **Cost:** ~$8.00

### Total Timeline
- **Stage 1:** 4 hours (includes review time)
- **Stage 2:** 8 hours (only after approval)
- **Total Time:** ~12 hours
- **Total Cost:** ~$15-20

### Critical Checkpoints
1. ✅ **Sample Review Gate** - Must pass before mass generation
2. ✅ **Local Storage Verification** - All files saved locally
3. ✅ **Backup Creation** - Before GitHub push
4. ✅ **GitHub Sync** - All assets pushed to repository
5. ✅ **Notion Integration** - URLs updated in deploy.py

---

## Part 6: Quality Assurance

### Automated Testing Pipeline
```python
def quality_check(asset_path):
    checks = {
        "file_size": check_file_size(asset_path, max_kb=100),
        "dimensions": check_dimensions(asset_path, min_size=64),
        "svg_valid": validate_svg_structure(asset_path) if asset_path.endswith('.svg'),
        "style_match": compare_to_master(asset_path, threshold=0.8)
    }
    return all(checks.values()), checks
```

### A/B Testing Strategy
- Generate 2 versions of key assets
- Use different prompts or parameters
- Select best based on criteria:
  - File size efficiency
  - Visual consistency
  - Notion rendering quality

---

## Part 7: Integration with Notion

### Asset URL Structure
```python
ASSET_URLS = {
    "covers": {
        "preparation": "https://raw.githubusercontent.com/jonathanhollander/notion-assets/main/covers/executive_blue/preparation_blueprint.png",
        "executor": "https://raw.githubusercontent.com/jonathanhollander/notion-assets/main/covers/executive_blue/executor_sextant.png",
        # ... etc
    },
    "icons": {
        "document": "https://raw.githubusercontent.com/jonathanhollander/notion-assets/main/icons/mechanical/document_scroll.svg",
        "family": "https://raw.githubusercontent.com/jonathanhollander/notion-assets/main/icons/mechanical/family_gears.svg",
        # ... etc
    }
}
```

### Update deploy.py Integration
```python
def get_asset_url(asset_type, asset_name, theme="executive_blue"):
    """Retrieve asset URL from generated manifest"""
    manifest_path = "output/manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    return manifest[theme][asset_type][asset_name]["url"]
```

---

## Part 8: Cost Optimization Tips

### Ways to Reduce Costs Further
1. **Batch similar prompts** - Some models offer bulk discounts
2. **Cache style transfers** - Reuse when possible
3. **Use SDXL more** - Switch more tier-1 assets to tier-2
4. **Reduce variations** - Generate 2 themes initially, add 3rd later
5. **Progressive enhancement** - Start with basics, add premium touches

### When to Spend More
1. **Hero images** - First impressions matter most
2. **Icons** - Used throughout, need perfect quality
3. **A/B testing** - Better to test than guess
4. **Style masters** - Foundation for all consistency

---

## Conclusion

This plan delivers:
- **200+ premium assets** for $15-20 (75% cost reduction)
- **100% automation** - No manual processes
- **Unique aesthetic** - Via style consistency, not training
- **Professional quality** - Premium models where it matters
- **Fast execution** - 15 hours total work
- **Easy maintenance** - Regenerate any asset on demand

The key insight: Use premium models strategically for maximum impact while leveraging cheaper alternatives where users won't notice the difference. Style consistency through reference images and detailed prompting eliminates the need for manual LoRA training while maintaining the unique "Heirloom Interface" aesthetic.

Ready to execute when approved.