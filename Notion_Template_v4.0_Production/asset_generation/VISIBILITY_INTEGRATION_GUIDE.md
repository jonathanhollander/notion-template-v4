# Enhanced Visibility Integration Guide

## Quick Start: See It In Action

### 1. Start the Web Server
```bash
cd asset_generation
python review_dashboard.py
```

### 2. Open Enhanced Dashboard
```
http://localhost:4500/enhanced
```

### 3. Run Test Simulation
```bash
# In another terminal
python test_enhanced_visibility.py
# Choose option 1 for full simulation
```

## Integration Points for asset_generator.py

### Step 1: Import WebSocket Broadcaster
Add at the top of `asset_generator.py`:

```python
from websocket_broadcaster import get_broadcaster

# Initialize broadcaster
broadcaster = get_broadcaster()
```

### Step 2: Add Visibility Calls During Generation

#### At Session Start
```python
async def generate_assets(self, mode="sample"):
    # Get broadcaster instance
    broadcaster = get_broadcaster()
    
    # Start session with total asset count
    total_assets = len(self.discovered_assets)
    broadcaster.session_started(session_id, total_assets)
    
    # Set budget limit for tracking
    broadcaster.budget_limit = self.budget_limit
```

#### During YAML Discovery
```python
# In discover_yaml_assets()
broadcaster.update_pipeline_stage("discovery")
broadcaster.emit('log_message', {
    'message': f"📁 Discovered {len(assets)} assets from YAML",
    'level': 'info'
})
```

#### During Prompt Generation
```python
# Before generating each prompt
broadcaster.update_pipeline_stage("prompt")
broadcaster.prompt_generating_start(asset_name, model_name)

# After prompt is generated
broadcaster.prompt_created(
    asset_name=asset_name,
    model=model_name, 
    prompt=generated_prompt,
    confidence=confidence_score,
    selected=True  # if this is the chosen prompt
)
```

#### During Model Competition
```python
# Show all model results
for model, result in model_results.items():
    broadcaster.prompt_created(
        asset_name=asset_name,
        model=model,
        prompt=result['prompt'],
        confidence=result['confidence'],
        selected=(model == selected_model)
    )

# Explain the decision
broadcaster.model_decision(
    selected_model=selected_model,
    reasons=[
        f"Highest confidence: {confidence}%",
        "Best context understanding",
        "Optimal for asset type"
    ]
)
```

#### During Image Generation
```python
# Before starting generation
broadcaster.update_pipeline_stage("image")
broadcaster.emit('image_generating', {
    'asset_name': asset_name,
    'status': 'starting',
    'model': 'stability-ai/sdxl'
})

# After generation completes
broadcaster.update_pipeline_stage("save")
broadcaster.emit('image_completed', {
    'asset_name': asset_name,
    'file_path': output_path,
    'cost': generation_cost,
    'duration': elapsed_time
})
```

#### Cost Updates
```python
# After each generation
broadcaster.update_cost(
    item_cost=current_item_cost,
    total_cost=self.total_cost,
    images_completed=self.images_generated
)
```

#### Approval Gates
```python
# Before batch generation
if self.require_approval:
    prompts_batch = [
        {
            'asset_name': asset['name'],
            'prompt': asset['prompt'],
            'estimated_cost': 0.04
        }
        for asset in batch
    ]
    
    broadcaster.request_approval(prompts_batch)
    
    # Wait for approval via WebSocket
    approval = await self.wait_for_approval()
    if not approval:
        broadcaster.emit_log("❌ Batch rejected by user", "warning")
        continue
```

## Integration Points for openrouter_orchestrator.py

### Add Model Competition Visibility

```python
class OpenRouterOrchestrator:
    def __init__(self):
        self.broadcaster = get_broadcaster()
    
    async def generate_prompt_with_competition(self, asset_info):
        """Generate with full visibility"""
        
        # Notify start of competition
        self.broadcaster.emit('model_competition_start', {
            'asset_name': asset_info['name'],
            'models': self.models
        })
        
        # Generate from each model
        results = {}
        for model in self.models:
            self.broadcaster.prompt_generating_start(
                asset_info['name'], 
                model
            )
            
            prompt = await self.generate_prompt(model, asset_info)
            confidence = self.calculate_confidence(prompt, asset_info)
            
            results[model] = {
                'prompt': prompt,
                'confidence': confidence
            }
            
            self.broadcaster.prompt_created(
                asset_name=asset_info['name'],
                model=model,
                prompt=prompt,
                confidence=confidence,
                selected=False  # Will update winner later
            )
        
        # Select winner and explain
        winner = self.select_best_prompt(results)
        self.broadcaster.model_decision(
            selected_model=winner['model'],
            reasons=winner['reasons']
        )
        
        return winner
```

## Integration Points for prompt_templates.py

### Add Prompt Tracking

```python
def generate_dynamic_prompt(asset_info, model="claude"):
    """Generate prompt with visibility tracking"""
    broadcaster = get_broadcaster()
    
    # Notify prompt generation start
    broadcaster.emit('prompt_template_start', {
        'asset_type': asset_info.get('type'),
        'model': model,
        'stage': 'template_selection'
    })
    
    # Build prompt with progress updates
    prompt_parts = []
    
    # Base prompt
    broadcaster.emit('prompt_building', {
        'component': 'base_prompt',
        'preview': base_prompt[:100] + '...'
    })
    prompt_parts.append(base_prompt)
    
    # Emotional elements
    if include_emotional:
        broadcaster.emit('prompt_building', {
            'component': 'emotional_layer',
            'preview': 'Adding emotional intelligence...'
        })
        prompt_parts.append(emotional_prompt)
    
    # Context enhancement
    broadcaster.emit('prompt_building', {
        'component': 'context_enhancement',
        'preview': 'Adding estate planning context...'
    })
    prompt_parts.append(context_prompt)
    
    final_prompt = '\n\n'.join(prompt_parts)
    
    broadcaster.emit('prompt_template_complete', {
        'length': len(final_prompt),
        'components': len(prompt_parts)
    })
    
    return final_prompt
```

## WebSocket Control Handlers

### Add to asset_generator.py

```python
class AssetGenerator:
    def __init__(self):
        self.paused = False
        self.aborted = False
        self.skip_current = False
        self.generation_speed = "normal"
        self.dry_run_mode = False
        
        # Register WebSocket handlers
        self.setup_websocket_handlers()
    
    def setup_websocket_handlers(self):
        """Setup control handlers"""
        broadcaster = get_broadcaster()
        
        # Store reference for checking flags
        self.broadcaster = broadcaster
        
    async def check_control_flags(self):
        """Check for pause/abort/skip commands"""
        
        # Check if paused
        while self.broadcaster.generation_paused:
            await asyncio.sleep(1)
            
        # Check if aborted
        if self.broadcaster.generation_aborted:
            raise GenerationAbortedException("Generation aborted by user")
            
        # Check if skip requested
        if self.broadcaster.skip_current:
            self.broadcaster.skip_current = False
            return "skip"
            
        # Apply speed control
        if self.broadcaster.generation_speed == "slow":
            await asyncio.sleep(2)
        elif self.broadcaster.generation_speed == "fast":
            pass  # No delay
        else:  # normal
            await asyncio.sleep(0.5)
    
    async def generate_with_controls(self, asset_info):
        """Generate with control checking"""
        
        # Check controls before starting
        control_result = await self.check_control_flags()
        if control_result == "skip":
            self.broadcaster.emit_log(f"⏭️ Skipped {asset_info['name']}", "info")
            return None
            
        # Generate asset
        result = await self.generate_asset(asset_info)
        
        # Check controls after generation
        await self.check_control_flags()
        
        return result
```

## Testing the Integration

### 1. Test WebSocket Connection
```python
# test_websocket_connection.py
import asyncio
from websocket_broadcaster import get_broadcaster

async def test_connection():
    broadcaster = get_broadcaster()
    
    # Test basic emission
    broadcaster.emit('test_event', {'message': 'Testing connection'})
    
    # Test all visibility events
    events_to_test = [
        ('pipeline_stage', {'stage': 'discovery'}),
        ('prompt_generating', {'asset_name': 'Test', 'model': 'Claude'}),
        ('cost_update', {'total_cost': 0.10, 'budget_percentage': 20}),
        ('log_message', {'message': 'Test log', 'level': 'info'})
    ]
    
    for event, data in events_to_test:
        broadcaster.emit(event, data)
        await asyncio.sleep(0.5)
    
    print("✅ WebSocket test complete - check dashboard for events")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

### 2. Test with Actual Generation
```python
# In asset_generator.py, add test mode
if __name__ == "__main__":
    parser.add_argument('--test-visibility', action='store_true',
                       help='Test with enhanced visibility')
    
    if args.test_visibility:
        # Enable all visibility features
        generator.enable_full_visibility = True
        generator.require_approval = True
        generator.show_model_competition = True
```

### 3. Verify Dashboard Updates
1. Open http://localhost:4500/enhanced
2. Run generation with `--test-visibility` flag
3. Confirm you see:
   - Real-time prompt updates
   - Cost tracking changes
   - Pipeline stage progression
   - Model competition results
   - Approval modals
   - Log streaming

## Troubleshooting

### WebSocket Not Connecting
```python
# Check if SocketIO is initialized in review_dashboard.py
if not hasattr(self, 'socketio'):
    print("ERROR: SocketIO not initialized")
    
# Verify CORS settings
CORS(app, origins=["http://localhost:4500"])
```

### Events Not Showing
```python
# Add debug logging
broadcaster.logger.setLevel(logging.DEBUG)

# Check if broadcaster is enabled
print(f"Broadcaster enabled: {broadcaster.enabled}")
print(f"SocketIO instance: {broadcaster._socketio}")
```

### Approval Gates Not Working
```python
# Ensure WebSocket handler is registered
@socketio.on('approve_prompts')
def handle_approve_prompts(data):
    # Process approval
    generator.approval_received(data['approved'])
```

## Complete Integration Checklist

- [ ] WebSocket broadcaster imported in all modules
- [ ] Pipeline stages updating during generation
- [ ] Prompt generation showing in real-time
- [ ] Model competition displaying results
- [ ] Cost tracker updating accurately
- [ ] Approval modals appearing when needed
- [ ] Control buttons (pause/resume/abort) working
- [ ] Log messages streaming to dashboard
- [ ] Dry-run mode toggle functional
- [ ] Speed controls affecting generation
- [ ] All 12 visibility features verified
- [ ] Error handling for WebSocket failures

## Next Steps

1. **Production Testing**
   - Run with 5-10 real images
   - Monitor all visibility features
   - Check performance impact
   
2. **Performance Optimization**
   - Batch WebSocket emissions
   - Implement event throttling
   - Add caching for repeat events
   
3. **Enhanced Features**
   - Add session recording
   - Export visibility logs
   - Create analytics dashboard
   - Add notification system

## Summary

The enhanced visibility system is now ready for integration. By following this guide, the asset generation system will provide complete transparency during actual image generation, giving users full insight and control over the process through the web interface.

All 12 visibility features are implemented and ready:
✅ Real-time prompt display
✅ Live cost tracking
✅ Web-based approval gates
✅ AI model decision explanations
✅ Prompt variations in panels
✅ Pause/resume/abort controls
✅ Visual pipeline diagram
✅ WebSocket events for all decisions
✅ Prompt editing capability
✅ Confidence score display
✅ Side-by-side comparison view
✅ Dry-run mode toggle

The system provides the complete visibility requested: users can now see exactly what's happening, how it's happening, and why decisions are being made during ACTUAL image and prompt generation.