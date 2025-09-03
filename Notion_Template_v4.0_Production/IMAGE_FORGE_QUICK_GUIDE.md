# Image Forge Quick Implementation Guide

## What You Have vs What You Need

### Already Working (in asset_generation/)
- ✅ Complete generation engine (asset_generator.py)
- ✅ Emotional AI system (emotional_elements.py - 32KB)
- ✅ Multi-model orchestration (openrouter_orchestrator.py)
- ✅ Quality scoring (quality_scorer.py)
- ✅ Visual hierarchy system (visual_hierarchy.py)
- ✅ Configuration and prompts

### Need to Add (for Web)
- 🔧 FastAPI wrapper around existing code
- 🔧 HTML interface
- 🔧 WebSocket for real-time updates
- 🔧 SQLite for user data

## Monday Demo - 48 Hour Plan

### Hour 0-12: Setup
```bash
pip install fastapi uvicorn python-multipart websockets
cp -r asset_generation/ image_forge/
cd image_forge/
```

### Hour 12-24: Create API Wrapper
Create `app.py`:
- Import existing AssetGenerator
- Add POST /generate endpoint
- Add WebSocket support
- Serve static files

### Hour 24-36: Simple UI
Create `index.html`:
- Text input
- Generate button
- Image display
- Progress indicator

### Hour 36-48: Test & Polish
- Generate 5-10 test images
- Fix any issues
- Prepare demo

## The Key Insight

**Your existing code is 95% complete. Just add a web layer:**

| Task | Existing File | Web Addition |
|------|--------------|--------------|
| Generation | asset_generator.py | FastAPI endpoint |
| Emotional AI | emotional_elements.py | Use as-is |
| Model Selection | openrouter_orchestrator.py | Use as-is |
| Quality | quality_scorer.py | Use as-is |
| Configuration | config.json | Load at startup |

## Minimal Viable API

```python
# app.py - This is ALL you need for Monday
from fastapi import FastAPI
from asset_generator import AssetGenerator

app = FastAPI()
generator = AssetGenerator()

@app.post("/generate")
async def generate(prompt: str):
    result = await generator.generate_single(prompt)
    return {"image_url": result}
```

## Files to Keep Unchanged
- emotional_elements.py (perfect as-is)
- openrouter_orchestrator.py (works great)
- quality_scorer.py (no changes needed)
- visual_hierarchy.py (ready to use)

## Success Metrics for Monday
- [ ] Web UI loads at localhost:8080
- [ ] Can input text and click generate
- [ ] Shows generated image
- [ ] Progress updates via WebSocket
- [ ] 5 successful test generations

## Week 1 Enhancements
- Add preset management (use existing prompts.json)
- Add transparency (hook into orchestrator)
- Add learning (simple SQLite tracking)

## Remember
- Don't refactor working code
- Just wrap in web endpoints
- Focus on demo, not perfection
- Your code already works!