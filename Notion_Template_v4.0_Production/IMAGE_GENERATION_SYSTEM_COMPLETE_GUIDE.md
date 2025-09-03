# Estate Planning v4.0 Image Generation System - Complete Guide

## System Overview
The Estate Planning Concierge v4.0 is a sophisticated web-based AI image generation system for creating luxury estate planning marketing materials. It generates icons, covers, textures, letter headers, and database icons using multiple AI models through Replicate and OpenRouter APIs.

## Core Components

### 1. Web Interface System

#### Main Entry Point
- **File**: `asset_generation/review_dashboard.py`
- **Launch**: `python3 review_dashboard.py`
- **Port**: 4500 (auto-increments if busy)
- **Purpose**: Web-based review and approval dashboard with master prompt editing

#### HTML Templates
- **Dashboard**: `asset_generation/templates/dashboard.html`
- **Features**:
  - Master prompt editor (textarea for editing AI instructions)
  - Authentication section (API token, reviewer name)
  - Real-time status display with live logging
  - Session status display
  - Progress tracking
  - Prompt review interface
  - Decision recording system

#### JavaScript/CSS
- **JS**: `asset_generation/static/js/dashboard.js`
  - WebSocket client for real-time updates
  - Master prompt editing handlers
  - API calls, session management, progress updates
  - Keyboard shortcuts for efficiency
- **CSS**: `asset_generation/static/css/dashboard.css`
  - Luxury estate planning theme
  - Status panel styling
  - Log stream display
  - Responsive design for mobile/tablet

### 2. Master Prompt System

#### Location & Purpose
- **File**: `meta_prompts/master_prompt.txt`
- **Size**: ~3,752 characters
- **Purpose**: Controls AI behavior for all image generation
- **Content**: Luxury branding guidelines, visual hierarchy, emotional sensitivity
- **Web Editable**: Yes, via web interface at `/edit-master-prompt`

#### How It Works
1. User edits master prompt in web interface
2. Changes saved to `meta_prompts/master_prompt.txt`
3. OpenRouter orchestrator loads updated prompt on next generation
4. Master prompt is combined with page context data
5. AI models generate prompts following master prompt instructions
6. Multiple models compete to create best prompts

### 3. Real-Time Status System

#### WebSocket Integration
- **Protocol**: Socket.IO for bidirectional communication
- **Events**:
  - `generation_status`: Progress updates during generation
  - `prompt_generation`: Updates during AI prompt creation
  - `image_generation`: Updates during image creation
  - `circuit_breaker_status`: API health monitoring
  - `generation_error`: Error notifications

#### Status Display Components
- **Current Phase Indicator**: Shows what's happening now
- **Progress Bar**: Visual representation of completion
- **Live Log Stream**: Real-time activity feed
- **Metrics Panel**: Prompts generated, images created, cost, API status

### 4. Asset Generation Pipeline

#### Main Generator
- **File**: `asset_generation/asset_generator.py`
- **Class**: `AssetGenerator`
- **Web Trigger**: Via `/api/start-generation` endpoint
- **Commands**:
  ```bash
  # Sample generation (3-10 images)
  python3 asset_generator.py
  
  # Mass production (490+ images, ~$20)
  python3 asset_generator.py --mass-production
  
  # Edit prompts only
  python3 asset_generator.py --edit-prompts
  
  # Process regeneration queue
  python3 asset_generator.py --regenerate
  ```

#### Key Modules
- **OpenRouter Orchestrator** (`openrouter_orchestrator.py`)
  - Manages AI model calls (Claude, GPT-4, Gemini)
  - Implements master prompt system
  - Generates competitive prompts
  - Broadcasts status via WebSocket

- **Sample Generator** (`sample_generator.py`)
  - Creates test images for review
  - Manages budget limits
  - Tracks generation progress
  - Sends real-time updates

- **Generation Manager** (`generation_manager.py`)
  - Background job management
  - Integrates with review dashboard
  - Handles async operations
  - WebSocket status broadcasting

### 5. Configuration System

#### Main Config
- **File**: `asset_generation/config.json`
- **Key Settings**:
  ```json
  {
    "replicate": {
      "api_key": "${REPLICATE_API_KEY}",
      "models": {
        "icons": "black-forest-labs/recraft-v3-svg",
        "covers": "black-forest-labs/flux-1.1-pro"
      }
    },
    "review": {
      "port": 4500,
      "auto_open": true
    },
    "budget": {
      "sample_generation": {
        "max_cost": 1.00,
        "items": 10
      },
      "mass_generation": {
        "max_cost": 25.00,
        "items": "dynamic"
      }
    }
  }
  ```

#### Environment Variables
- **REPLICATE_API_TOKEN**: For image generation (NOT REPLICATE_API_KEY!)
- **OPENROUTER_API_KEY**: For AI prompt generation
- **Other API keys**: ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.

### 6. YAML Data Source

#### Location
- **Directory**: `split_yaml/`
- **Files**: 21 YAML files with page definitions
- **Test File**: `split_yaml/test_minimal.yaml` (3 pages for testing)

#### Structure
```yaml
pages:
  - title: "Preparation Hub"
    icon: "emoji:🏠"
    cover: "mahogany desk with estate planning documents"
    description: "Your starting place for estate planning"
    page_category: "HUB"
```

### 7. Safety & Security Systems

#### Path Validator
- **File**: `utils/path_validator.py`
- **Purpose**: Prevents directory traversal attacks
- **Note**: Fixed to allow spaces in paths like "AI Code"

#### Circuit Breaker
- **File**: `utils/transaction_safety.py`
- **Purpose**: Prevents API overload, manages retries
- **States**: CLOSED (working), OPEN (failing), HALF_OPEN (testing)
- **Web Display**: Real-time status shown in UI

#### Database Manager
- **File**: `utils/database_manager.py`
- **Database**: `estate_planning_assets.db`
- **Tracks**: Assets, costs, prompts, approvals

### 8. Web-Based Workflow

#### Complete User Journey
1. **Launch Web Interface**
   ```bash
   cd asset_generation
   python3 review_dashboard.py
   ```
   Browser opens to http://localhost:4500

2. **Edit Master Prompt**
   - Navigate to master prompt editor
   - See current prompt in large textarea
   - Make desired changes
   - Click "Save Changes"

3. **Start Generation**
   - Click "Start Test Generation (3 images)"
   - Watch real-time status updates
   - See live log stream
   - Monitor progress bar

4. **Review & Approve**
   - Automatic redirect to review interface
   - Compare AI-generated prompts
   - Select best options
   - Record decisions

5. **Optional Mass Production**
   - After approval, option for full generation
   - Clear cost warning ($20)
   - Real-time progress for 490+ images

### 9. Real-Time Status Messages

#### During Prompt Generation
```
[10:30:15] 🚀 Starting sample generation (3 images)
[10:30:16] 📄 Loading master prompt (3,752 characters)
[10:30:17] 🤖 Claude-3.5: Generating luxury perspective...
[10:30:19] ✅ Claude response received (1.2s)
[10:30:19] 🤖 GPT-4: Generating technical perspective...
[10:30:21] ✅ GPT-4 response received (2.1s)
[10:30:21] 🤖 Gemini-2.5: Generating emotional perspective...
[10:30:22] ✅ Gemini response received (0.8s)
[10:30:23] 🏆 Winner selected: Claude-3.5 (score: 8.7/10)
```

#### During Image Generation
```
[10:30:24] 🎨 Image 1/3: Preparation Hub Icon
[10:30:25] 📡 Calling Replicate API...
[10:30:30] ✅ Image generated successfully
[10:30:30] 💾 Saved: output/samples/icons_001.svg
[10:30:30] 💰 Cost: $0.04 (Total: $0.04)
```

#### Error Handling
```
[10:30:45] ⚠️ API rate limit approaching
[10:30:46] 🔄 Circuit breaker: HALF_OPEN state
[10:30:47] ⏸️ Pausing for 5 seconds...
[10:30:52] ✅ Resuming generation
```

### 10. Database Schema

```sql
-- Main assets table
CREATE TABLE assets (
    id INTEGER PRIMARY KEY,
    filename TEXT UNIQUE,
    asset_type TEXT,
    prompt TEXT,
    cost REAL,
    created_at TIMESTAMP
);

-- Prompt competitions
CREATE TABLE prompt_competitions (
    id INTEGER PRIMARY KEY,
    page_title TEXT,
    asset_type TEXT,
    winning_prompt TEXT,
    winning_model TEXT
);

-- Generation sessions
CREATE TABLE generation_sessions (
    id INTEGER PRIMARY KEY,
    session_id TEXT UNIQUE,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    total_cost REAL,
    status TEXT
);
```

### 11. File Structure

```
asset_generation/
├── review_dashboard.py          # Web interface with WebSocket
├── asset_generator.py           # Main generation with status emit
├── sample_generator.py          # Sample image creator
├── generation_manager.py        # Background job manager
├── openrouter_orchestrator.py   # AI model coordinator
├── config.json                  # Configuration
├── templates/
│   └── dashboard.html          # Enhanced web UI template
├── static/
│   ├── js/dashboard.js        # WebSocket client & handlers
│   └── css/dashboard.css      # Enhanced styling
├── meta_prompts/
│   └── master_prompt.txt      # Master AI instructions (web editable)
├── split_yaml/                 # Page definitions (21 files)
├── output/
│   ├── samples/               # Test images
│   └── production/            # Final images
└── utils/
    ├── path_validator.py      # Security
    ├── transaction_safety.py  # Circuit breaker
    └── database_manager.py    # Database operations
```

## Key Features

### What's New in This Implementation

1. **Master Prompt Web Editor**
   - Edit AI instructions directly in browser
   - Save changes without file access
   - Instant feedback on changes

2. **One-Click Generation**
   - "Start Generation" button in web UI
   - No command line required
   - Choice between test (3 images) and production (490 images)

3. **Real-Time Status Display**
   - Live log streaming via WebSocket
   - Progress bars for all operations
   - Cost tracking in real-time
   - API health monitoring

4. **Complete Web Workflow**
   - Everything accessible from browser
   - No terminal interaction needed
   - Seamless flow from editing to generation to review

### Security Considerations
- API tokens in environment variables only
- CSRF protection on all POST requests
- Session management for authentication
- Path validation prevents attacks
- Circuit breaker prevents API abuse

### Cost Management
- Test mode: 3 images (~$0.12)
- Sample generation: 10 images (~$0.40)
- Full production: 490 images (~$20)
- Real-time cost display
- Budget limits enforced

### Error Recovery
- Automatic retry with backoff
- Circuit breaker protection
- Graceful degradation
- Clear error messages in UI
- Recovery suggestions displayed

## How to Use

### Quick Start
```bash
# Set environment variables
export REPLICATE_API_TOKEN="your_token_here"
export OPENROUTER_API_KEY="your_key_here"

# Launch web interface
cd asset_generation
python3 review_dashboard.py

# Browser opens automatically
# 1. Edit master prompt if desired
# 2. Click "Start Test Generation"
# 3. Watch real-time progress
# 4. Review and approve
# 5. Optionally run full production
```

### Web Interface URLs
- Main Dashboard: http://localhost:4500
- Master Prompt Editor: http://localhost:4500/edit-master-prompt
- Status Dashboard: Integrated in main interface
- API Endpoints:
  - GET `/api/get-master-prompt`
  - POST `/api/save-master-prompt`
  - POST `/api/start-generation`
  - WebSocket `/socket.io/`

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if port 4500 is available
   - Verify flask-socketio is installed
   - Check browser console for errors

2. **Generation Not Starting**
   - Verify API keys are set
   - Check budget limits in config.json
   - Review logs in browser status panel

3. **No Real-Time Updates**
   - Ensure WebSocket connection is active
   - Check network tab in browser
   - Verify no firewall blocking

4. **Master Prompt Not Saving**
   - Check file permissions on meta_prompts/
   - Verify CSRF token is valid
   - Check browser console for errors

## Summary

This implementation provides a complete web-based image generation system with:
- ✅ Master prompt editing in browser
- ✅ One-click generation trigger
- ✅ Real-time status display
- ✅ Live log streaming
- ✅ Progress tracking
- ✅ Cost monitoring
- ✅ Error handling
- ✅ Test mode (3 images)
- ✅ Production mode (490 images)
- ✅ Complete web workflow

The system is now fully accessible via web interface without any command-line interaction required.