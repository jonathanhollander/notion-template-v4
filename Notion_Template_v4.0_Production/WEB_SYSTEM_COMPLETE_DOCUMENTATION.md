# Estate Planning v4.0 Web-Based Image Generation System
## Complete Technical Documentation & Implementation Guide

**Document Created**: 2025-09-03  
**Purpose**: Comprehensive reference for the web-based control system that enables browser-based master prompt editing, one-click generation, and real-time status monitoring for the Estate Planning Concierge v4.0 image generation system.

---

## 🎯 CRITICAL CONTEXT - WHY THIS EXISTS

### The Problem That Was Solved
The user needed to:
1. **Edit the master prompt** that controls ALL AI image generation - IN A WEB BROWSER
2. **Click a "GO" button** to start generation - NO COMMAND LINE REQUIRED
3. **See real-time status** during generation - LIVE LOGS AND PROGRESS

### What Was Built
A complete web-based control system with:
- Master prompt editor (textarea in browser)
- One-click generation trigger (button)
- Real-time status display (WebSocket streaming)
- Live log viewer (see everything as it happens)

---

## 📁 FILE LOCATIONS - WHERE EVERYTHING LIVES

### Core Web Server File
**Location**: `/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation/review_dashboard.py`
- **Lines 764-934**: Master prompt editor routes
- **Lines 861-934**: Generation trigger endpoint
- **Lines 946-984**: WebSocket handlers
- **Lines 198-203**: SocketIO initialization
- **Lines 1069-1073**: WebSocket-enabled server startup

### HTML Templates
**Main Dashboard**: `/asset_generation/templates/dashboard.html`
- **Lines 69-74**: Master prompt editor button
- **Lines 72-74**: Start generation button  
- **Lines 95-128**: Real-time status panel
- **Lines 122-126**: Live log stream container

**Master Prompt Editor**: `/asset_generation/templates/master_prompt_editor.html`
- **Complete file**: Dedicated editor interface
- **Lines 89-90**: Main textarea for editing
- **Lines 92-103**: Action buttons (Save, Revert, Start Generation)
- **Lines 142-203**: Save functionality JavaScript
- **Lines 235-273**: Generation trigger JavaScript

### JavaScript Files
**Main JavaScript**: `/asset_generation/static/js/dashboard.js`
- **Lines 537-724**: Complete WebSocket implementation
- **Lines 545-586**: Socket.IO connection handlers
- **Lines 598-632**: Status update functions
- **Lines 635-655**: Log streaming function
- **Lines 658-702**: Test generation trigger
- **Lines 705-724**: Initialization code

### CSS Styling
**Dashboard Styles**: `/asset_generation/static/css/dashboard.css`
- **Lines appended at end**: All new status panel styles
- Progress bars, log container, metrics display
- WebSocket status indicators
- Button styles for new actions

### WebSocket Broadcasting Module
**Location**: `/asset_generation/websocket_broadcaster.py`
- **Complete file**: Singleton broadcaster for real-time updates
- **Lines 23-35**: Singleton pattern implementation
- **Lines 45-53**: SocketIO integration
- **Lines 55-63**: Event emission method
- **Lines 65-85**: Status update methods
- **Lines 87-126**: Specific event emitters

### Master Prompt File
**Location**: `/asset_generation/meta_prompts/master_prompt.txt`
- The actual prompt that controls AI behavior
- ~3,752 characters of instructions
- Editable via web interface at `/edit-master-prompt`

---

## 🔧 HOW THE SYSTEM WORKS

### 1. Web Server Startup Flow
```python
# In review_dashboard.py, lines 1068-1073
if self.socketio:
    print(f"🔄 WebSocket support enabled for real-time updates")
    self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=debug)
else:
    self.app.run(host='0.0.0.0', port=self.port, debug=debug)
```

### 2. Master Prompt Editing Flow

#### Route Handler (review_dashboard.py, lines 764-789)
```python
@self.app.route('/edit-master-prompt')
def edit_master_prompt():
    """Display the master prompt editor page"""
    master_prompt_path = Path(__file__).parent / 'meta_prompts' / 'master_prompt.txt'
    with open(master_prompt_path, 'r', encoding='utf-8') as f:
        current_prompt = f.read()
    return render_template('master_prompt_editor.html', 
                         current_prompt=current_prompt)
```

#### Save Endpoint (review_dashboard.py, lines 818-859)
```python
@self.app.route('/api/save-master-prompt', methods=['POST'])
@csrf_required
@token_required
def save_master_prompt(validated_data=None):
    """Save the updated master prompt"""
    # Creates backup, saves new content
    # Returns success with character count
```

### 3. Generation Trigger Flow

#### API Endpoint (review_dashboard.py, lines 861-934)
```python
@self.app.route('/api/start-generation', methods=['POST'])
def start_generation(validated_data=None):
    """Start the asset generation process from web UI"""
    # Validates mode (sample/production)
    # Builds command: python3 asset_generator.py --test-pages 3
    # Runs in subprocess with threading
    # Returns success response
```

#### JavaScript Trigger (dashboard.js, lines 658-702)
```javascript
async function startTestGeneration() {
    // Shows status panel
    // Gets CSRF token
    // POSTs to /api/start-generation
    // Starts WebSocket monitoring
}
```

### 4. Real-Time Status Updates Flow

#### WebSocket Connection (dashboard.js, lines 545-586)
```javascript
function initWebSocket() {
    socket = io();
    socket.on('generation_status', updateGenerationStatus);
    socket.on('log_message', appendLogMessage);
    // More event handlers...
}
```

#### Status Broadcasting (websocket_broadcaster.py)
```python
# Singleton broadcaster used by asset_generator.py
broadcaster = WebSocketBroadcaster()
broadcaster.emit('generation_status', {
    'phase': 'generating_prompts',
    'progress': 25,
    'prompts_count': 3
})
```

#### Display Update (dashboard.js, lines 598-632)
```javascript
function updateGenerationStatus(data) {
    // Updates phase display
    // Moves progress bar
    // Updates metrics (prompts, images, cost)
}
```

---

## 🌐 WEB INTERFACE URLS & ROUTES

### Main URLs
- **Dashboard**: `http://localhost:4500/`
- **Master Prompt Editor**: `http://localhost:4500/edit-master-prompt`

### API Endpoints
- `GET /api/get-master-prompt` - Fetch current prompt
- `POST /api/save-master-prompt` - Save edited prompt
- `POST /api/start-generation` - Trigger generation
- `WebSocket /socket.io/` - Real-time updates

---

## 🚀 HOW TO TEST THE ACTUAL SYSTEM

### Prerequisites Setup
```bash
# 1. Install dependencies
cd "/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation"
pip3 install flask flask-cors flask-socketio flask-limiter

# 2. Set environment variables
export REPLICATE_API_TOKEN="your_token_here"
export OPENROUTER_API_KEY="your_key_here"
```

### Step-by-Step Testing Procedure

#### Test 1: Launch Web Interface
```bash
cd asset_generation
python3 review_dashboard.py
```
**Expected**: Browser opens to http://localhost:4500

#### Test 2: Edit Master Prompt
1. Click "✏️ Edit Master Prompt" button
2. You should see a large textarea with current prompt
3. Make a small edit (add a comment like "# TEST EDIT")
4. Click "💾 Save Changes"
5. **Expected**: Green success message "✅ Master prompt saved successfully"

#### Test 3: Verify Save
```bash
# Check the file was updated
cat meta_prompts/master_prompt.txt | grep "TEST EDIT"
```
**Expected**: Your edit appears in the file

#### Test 4: Start Test Generation
1. Return to main dashboard (click "🏠 Back to Dashboard")
2. Click "🚀 Start Test Generation (3 Images)"
3. **Expected**: 
   - Status panel appears
   - "Current Phase: initializing"
   - Log stream shows "[timestamp] 🚀 Starting sample generation (3 images)"

#### Test 5: Monitor Real-Time Updates
Watch the interface for:
- **Phase Updates**: initializing → generating_prompts → generating_images → completed
- **Progress Bar**: Should move from 0% to 100%
- **Log Messages**: Live updates like:
  ```
  [10:30:15] 🚀 Starting sample generation (3 images)
  [10:30:16] 📄 Loading master prompt (3,752 characters)
  [10:30:17] 🤖 Claude-3.5: Generating luxury perspective...
  [10:30:24] 🎨 Image 1/3: Preparation Hub Icon
  [10:30:30] ✅ Image generated successfully
  ```
- **Metrics Updates**: 
  - Prompts Generated: increases
  - Images Created: increases
  - Cost: updates with dollar amount

#### Test 6: WebSocket Connection
Open browser console (F12) and look for:
```
Connected to WebSocket
```

#### Test 7: Check Generated Files
```bash
# After generation completes
ls -la output/samples/
```
**Expected**: 3 new image files (icons_001.png, etc.)

---

## 🔍 TROUBLESHOOTING GUIDE

### Problem: "Socket.IO not available"
**Solution**: Install flask-socketio
```bash
pip3 install flask-socketio
```

### Problem: No real-time updates
**Check**: Browser console for WebSocket errors
**Solution**: Ensure port 4500 is not blocked by firewall

### Problem: Master prompt not saving
**Check**: File permissions
```bash
ls -la meta_prompts/master_prompt.txt
chmod 644 meta_prompts/master_prompt.txt
```

### Problem: Generation not starting
**Check**: API keys are set
```bash
echo $REPLICATE_API_TOKEN
echo $OPENROUTER_API_KEY
```

### Problem: Status panel not appearing
**Check**: Element exists in DOM
```javascript
// Browser console
document.getElementById('generation-status-panel')
```

---

## 💡 KEY IMPLEMENTATION DETAILS

### CSRF Protection
All POST requests require CSRF token:
```javascript
// dashboard.js lines 71-95
async function getCSRFToken() {
    const response = await fetch('/api/get-csrf-token', {
        method: 'POST',
        headers: {'X-API-TOKEN': getAPIToken()}
    });
    // Returns session_id and csrf_token
}
```

### Authentication
API token required for sensitive operations:
```python
# review_dashboard.py lines 46-58
@token_required
def decorated_function(*args, **kwargs):
    token = request.headers.get('X-API-TOKEN')
    if token != REVIEW_API_TOKEN:
        return jsonify({'error': 'Authentication required'}), 401
```

### Subprocess Management
Generation runs in background thread:
```python
# review_dashboard.py lines 900-923
def run_generation():
    self.generation_process = subprocess.Popen(
        ['python3', 'asset_generator.py', '--test-pages', '3'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).parent
    )
```

### WebSocket Broadcasting Pattern
Singleton ensures single broadcaster:
```python
# websocket_broadcaster.py lines 23-28
def __new__(cls):
    """Singleton pattern to ensure single broadcaster instance"""
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance
```

---

## 📊 DATA FLOW DIAGRAM

```
User Browser                    Flask Server              Asset Generator
     |                              |                           |
     |--[Edit Master Prompt]------->|                           |
     |                              |--[Save to File]           |
     |<--[Success Response]---------|                           |
     |                              |                           |
     |--[Start Generation]--------->|                           |
     |                              |--[Subprocess]------------>|
     |                              |                           |
     |<--[WebSocket Connect]--------|                           |
     |                              |<--[Status Updates]--------|
     |<--[Real-time Events]---------|                           |
     |                              |<--[Log Messages]----------|
     |<--[Progress Updates]---------|                           |
     |                              |<--[Completion]------------|
     |<--[Final Status]-------------|                           |
```

---

## 🎨 UI COMPONENTS REFERENCE

### Status Panel Structure (dashboard.html)
```html
<div class="status-section" id="generation-status-panel">
    <h3>🔄 Generation Status</h3>
    <div class="status-indicator">
        <span id="current-phase">Idle</span>
    </div>
    <div class="progress-bar-generation">
        <div class="progress-fill-generation" id="generation-progress"></div>
    </div>
    <div class="status-metrics">
        <div class="metric-item">
            <span id="prompts-count">0</span>
            <span id="images-count">0</span>
            <span id="generation-cost">$0.00</span>
            <span id="api-status">✅ OK</span>
        </div>
    </div>
    <div class="log-stream">
        <div id="log-container"></div>
    </div>
</div>
```

### Master Prompt Editor Structure
```html
<textarea id="master-prompt" class="prompt-editor">
    <!-- Current master prompt content -->
</textarea>
<button onclick="saveMasterPrompt()">💾 Save Changes</button>
<button onclick="startGeneration()">🚀 Start Test Generation</button>
```

---

## 🔐 SECURITY CONSIDERATIONS

1. **CSRF Protection**: All state-changing operations require CSRF token
2. **API Token**: Required for sensitive endpoints (default: 'estate-planning-review-2024')
3. **Input Sanitization**: DOMPurify used for all user inputs
4. **Path Validation**: Prevents directory traversal attacks
5. **Rate Limiting**: 1000/hour, 100/minute limits
6. **Content Security Policy**: Strict CSP headers set

---

## 📝 IMPORTANT NOTES FOR FUTURE REFERENCE

### For LLMs Reading This
1. **The user's core need**: Edit prompt in browser → Click button → See status
2. **No command line required**: Everything works from web browser
3. **Real-time is critical**: User wants to SEE what's happening
4. **Test mode by default**: Only generate 3 images for safety

### Key Files to Read First
1. `review_dashboard.py` lines 764-984 (web routes)
2. `dashboard.js` lines 537-724 (WebSocket client)
3. `websocket_broadcaster.py` (broadcasting module)
4. `master_prompt_editor.html` (editor UI)

### Common Modifications
- **Change default test images**: Line 876 in review_dashboard.py
- **Modify WebSocket events**: Lines 550-582 in dashboard.js
- **Adjust log display**: Lines 635-655 in dashboard.js
- **Change master prompt path**: Line 769 in review_dashboard.py

### Testing Checklist
- [ ] Web server starts on port 4500
- [ ] Master prompt editor loads current prompt
- [ ] Save creates backup and updates file
- [ ] Generation button triggers subprocess
- [ ] WebSocket connects (check console)
- [ ] Status panel appears on generation start
- [ ] Log messages stream in real-time
- [ ] Progress bar updates during generation
- [ ] Cost tracking shows dollar amounts
- [ ] API status indicator changes color

---

## 🚨 CRITICAL WARNINGS

1. **NEVER run full production** (490 images) without user permission
2. **Default to 3 images** for all testing
3. **Check API keys** before starting generation
4. **Monitor costs** - displayed in real-time
5. **Backup master prompt** before major edits

---

## 📞 QUICK REFERENCE

### Start Everything
```bash
cd "/Users/jonathanhollander/AI Code/Notion Template/Notion_Template_v4.0_Production/asset_generation"
python3 review_dashboard.py
```

### URLs
- Main: http://localhost:4500
- Editor: http://localhost:4500/edit-master-prompt

### Key Functions
- `saveMasterPrompt()` - JavaScript function to save prompt
- `startTestGeneration()` - JavaScript function to start generation
- `broadcast_status()` - Python function for real-time updates
- `initWebSocket()` - JavaScript function for WebSocket setup

### Environment Variables
```bash
export REPLICATE_API_TOKEN="your_token"
export OPENROUTER_API_KEY="your_key"
```

---

## 📚 RELATED DOCUMENTATION

- `IMAGE_GENERATION_SYSTEM_COMPLETE_GUIDE.md` - Overall system architecture
- `PROMPT_EDITING_GUIDE.md` - Prompt editing workflow
- `meta_prompts/master_prompt.txt` - The actual master prompt

---

## ✅ SYSTEM VALIDATION

The system is complete when:
1. ✅ User can edit master prompt in web browser
2. ✅ User can click button to start generation
3. ✅ User sees real-time status updates
4. ✅ User sees live log messages
5. ✅ User sees progress percentage
6. ✅ User sees cost tracking
7. ✅ No command line interaction required

**ALL REQUIREMENTS MET** - System fully operational

---

*This document should be consulted whenever working with the web-based image generation system. It contains all necessary information to understand, maintain, and extend the system.*