# Image Forge Transformation Guide
## From Estate Planning v4.0 to Flexible Image Generation Platform

## The Transformation Strategy

### What Changes vs What Stays

#### Keep As-Is (80% of code)
- `emotional_elements.py` - Perfect emotional AI system
- `openrouter_orchestrator.py` - Multi-model competition works
- `quality_scorer.py` - Scoring logic is solid
- `visual_hierarchy.py` - 5-tier system is flexible

#### Transform (15% modification)
- `asset_generator.py` → Add web endpoints
- Console output → WebSocket messages
- File saves → Return URLs
- Batch processing → Queue system
- Fixed prompts → Dynamic inputs

#### Add New (5% new code)
- FastAPI wrapper
- HTML/JS interface
- WebSocket handler
- SQLite for user data
- API authentication

## Step-by-Step Transformation

### Step 1: Project Setup (30 minutes)
```bash
# 1. Copy existing code
cp -r asset_generation/ image_forge/
cd image_forge/

# 2. Create new structure
mkdir -p api web data tests
touch api/app.py api/endpoints.py
touch web/index.html web/app.js
```

### Step 2: Wrap Asset Generator (2 hours)

**File**: `api/app.py`

Key changes to `asset_generator.py`:
1. Remove `if __name__ == "__main__"` block
2. Change file outputs to return URLs
3. Replace print statements with logger
4. Make methods async where needed

```python
# Import existing code
from core_engine.asset_generator import AssetGenerator
from core_engine.emotional_elements import EmotionalElementsManager
from core_engine.openrouter_orchestrator import OpenRouterOrchestrator

# Wrap in FastAPI
app = FastAPI()
generator = AssetGenerator()  # Your existing class!
```

### Step 3: Create Endpoints (2 hours)

Transform existing methods to endpoints:

| Existing Method | New Endpoint | Purpose |
|----------------|--------------|----------|
| `generate_single()` | POST /generate | Single image |
| `generate_batch()` | POST /batch | Multiple images |
| `get_config()` | GET /config | Settings |
| `sync_yaml()` | POST /sync | Update config |

### Step 4: Add WebSocket (1 hour)

Replace console progress bars with WebSocket:

**Before** (in existing code):
```python
for item in tqdm(items, desc="Generating"):
    # process
```

**After** (simple change):
```python
for i, item in enumerate(items):
    await websocket.send_json({
        "progress": i / len(items) * 100
    })
    # process
```

### Step 5: Simple UI (2 hours)

Create minimal interface:
- Input field (textarea)
- Generate button
- Image display area
- Progress bar
- Settings panel (hidden by default)

## Configuration Migration

### From YAML to Dynamic

**Current** (estate_planning_v4.yaml):
```yaml
estate_planning_hub:
  tier: 1
  emotional_elements:
    comfort_symbols: [oak desk, family photos]
```

**Transform to** (presets.json):
```json
{
  "id": "estate_planning",
  "name": "Estate Planning",
  "editable": true,
  "components": {
    "hub": {
      "tier": 1,
      "emotional_elements": {
        "comfort_symbols": ["oak desk", "family photos"]
      }
    }
  }
}
```

## Code Reuse Map

### Direct Imports (No Changes)
```python
# These work perfectly as-is
from emotional_elements import EmotionalElementsManager
from visual_hierarchy import VisualHierarchy, VisualTier
from quality_scorer import QualityScorer
```

### Minor Adaptations
```python
# asset_generator.py - Small changes
class AssetGenerator:
    def generate_single(self, prompt, **kwargs):
        # Existing logic
        result = self._generate(prompt)
        
        # Changed: Instead of saving file
        # return result['url']  # New
        # self.save_file(result)  # Old
```

### New Additions
```python
# New files to create
api/
  app.py         # 100 lines - FastAPI setup
  endpoints.py   # 150 lines - Route handlers
  websocket.py   # 50 lines - Real-time updates
web/
  index.html     # 200 lines - Simple UI
  app.js         # 150 lines - Client logic
```

## Migration Checklist

### Phase 0: Monday Demo
- [ ] Copy asset_generation to new folder
- [ ] Install FastAPI, uvicorn
- [ ] Create app.py importing existing code
- [ ] Add /generate endpoint
- [ ] Create basic HTML interface
- [ ] Test with existing Replicate API key
- [ ] Generate 5 test images

### Phase 1: Enhancements
- [ ] Add user presets (extend prompts.json)
- [ ] Add transparency (hook into orchestrator)
- [ ] Add learning (simple SQLite)
- [ ] Add batch support
- [ ] Add export options

## Common Pitfalls & Solutions

### Pitfall 1: Trying to Refactor Everything
**Don't**: Rewrite emotional_elements.py
**Do**: Import and use as-is

### Pitfall 2: Complex UI First
**Don't**: Build React app with 50 components
**Do**: Single HTML file with vanilla JS

### Pitfall 3: Over-Engineering API
**Don't**: GraphQL, microservices, Kubernetes
**Do**: Simple FastAPI with 5 endpoints

### Pitfall 4: Changing Core Logic
**Don't**: Modify the generation algorithms
**Do**: Keep core logic, change I/O only

## Testing Migration

### Quick Validation Tests
```bash
# 1. Test existing code still works
python asset_generator.py --test

# 2. Test API wrapper
curl -X POST localhost:8080/generate \
  -d '{"prompt": "test image"}'

# 3. Test WebSocket
wscat -c ws://localhost:8080/ws

# 4. Test UI
open http://localhost:8080
```

## Performance Comparison

| Metric | Original | Transformed | Impact |
|--------|----------|-------------|---------|
| Generation Speed | 5-10s | 5-10s | No change |
| Memory Usage | 500MB | 550MB | +10% for web |
| Code Lines | 5,000 | 5,500 | +10% wrapper |
| Dependencies | 15 | 20 | +5 for web |

## File Mapping

| Original File | New Location | Changes |
|--------------|--------------|---------|
| asset_generator.py | api/generator.py | Add async, remove main |
| emotional_elements.py | core/emotional.py | None |
| openrouter_orchestrator.py | core/orchestrator.py | None |
| config.json | config/config.json | None |
| prompts.json | config/presets.json | Rename fields |

## The 80/20 Rule

**80% of value from 20% effort:**
1. Web interface (biggest impact)
2. Real-time updates (user experience)
3. Preset management (flexibility)
4. API endpoints (integration)
5. Simple auth (multi-user)

**Don't spend time on:**
- Refactoring working code
- Complex architectures
- Advanced features initially
- Perfect UI design
- Comprehensive testing

## Monday Success Criteria

If you can:
1. Open browser to localhost:8080
2. Type a prompt
3. Click generate
4. See progress updates
5. View generated image

**You've succeeded!**

## Remember

- Your code is 95% complete
- Focus on web wrapper, not core refactor
- Working demo > perfect architecture
- Existing code = proven code
- Ship Monday, iterate Tuesday

The transformation is simpler than it seems. Your existing code is gold - just make it accessible via web!