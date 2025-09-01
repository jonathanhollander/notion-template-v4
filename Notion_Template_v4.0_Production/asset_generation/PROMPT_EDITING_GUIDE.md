# Prompt Editing and Regeneration Guide

## Overview
The Estate Planning Asset Generator now includes comprehensive prompt editing and regeneration capabilities, allowing you to refine and perfect your image generation prompts during the review stage.

## Key Features

### 1. Prompt Visibility
- **See Every Prompt**: During the review stage, each asset displays its generation prompt in an editable textarea
- **Page Context**: View the page title and description alongside each prompt
- **Metadata Display**: Understand which page each asset belongs to

### 2. Real-Time Editing
- **Edit in Browser**: Modify prompts directly in the review interface
- **Save Changes**: Click the 💾 Save button to persist your edits
- **Visual Feedback**: Green border confirms successful save

### 3. Selective Regeneration
- **Queue Assets**: Mark specific assets for regeneration with improved prompts
- **Batch Processing**: Process all queued regenerations at once
- **Cost Tracking**: Monitor regeneration costs separately

## Workflow

### Step 1: Initial Generation
```bash
python asset_generator.py
```
- Generates sample assets using prompts from YAML
- Saves prompts to `prompts.json` for editing
- Launches review server on port 4500

### Step 2: Review and Edit
1. **Browser Opens Automatically** to http://localhost:4500
2. **Review Each Asset**:
   - See the generated placeholder (icon/cover/texture)
   - Read the current prompt in the textarea
   - View page title and description for context

3. **Edit Prompts**:
   - Modify any prompt directly in the textarea
   - Click 💾 Save to persist changes
   - Changes are saved to `prompts.json`

### Step 3: Queue for Regeneration
- Click 🔄 Regenerate for assets needing new generation
- Assets are added to regeneration queue
- Queue persists across sessions

### Step 4: Process Regenerations
```bash
# Process queued regenerations
python asset_generator.py --regenerate

# Or continue after approval
# (Regenerations process automatically after approval)
```

## Command Line Options

### Normal Flow
```bash
python asset_generator.py
```
Standard workflow: Generate → Review → Approve → Mass Production → Auto-commit to Git

### Regeneration Only
```bash
python asset_generator.py --regenerate
```
Process any assets queued for regeneration

### Edit Prompts Only
```bash
python asset_generator.py --edit-prompts
```
Launch review interface without generating new assets

### Skip Review
```bash
python asset_generator.py --skip-review
```
Generate samples without launching review server

### Mass Production
```bash
python asset_generator.py --mass-production
```
Run mass production (requires prior approval)

### Manual Git Control
```bash
# Skip automatic Git commit
python asset_generator.py --no-commit

# Preview Git operations without executing
python asset_generator.py --dry-run
```

## File Structure

### prompts.json
Central storage for all prompts and editing history:
```json
{
  "prompts": {
    "icons": {
      "Preparation Hub": {
        "original": "Original prompt...",
        "current": "Edited prompt...",
        "metadata": {
          "prompt_history": ["v1", "v2", "v3"]
        }
      }
    }
  },
  "edited_prompts": {
    "icons": {
      "Preparation Hub": {
        "old": "Original",
        "new": "Edited",
        "edited_at": "2024-01-15T10:30:00"
      }
    }
  },
  "regeneration_queue": [
    {
      "type": "icons",
      "page_title": "Preparation Hub",
      "filename": "icons_001.png",
      "prompt": "New improved prompt"
    }
  ]
}
```

### manifest.json
Enhanced with metadata for review interface:
```json
{
  "samples": [
    {
      "type": "icons",
      "filename": "icons_001.png",
      "prompt": "Current prompt",
      "metadata": {
        "page_title": "Preparation Hub",
        "page_description": "Your starting place",
        "editable": true,
        "prompt_history": ["v1", "v2"]
      },
      "regeneration": {
        "can_regenerate": true,
        "asset_type": "icons",
        "page_index": 0
      }
    }
  ],
  "editable_prompts": true,
  "prompt_file": "prompts.json"
}
```

## Prompt Engineering Tips

### For Icons
- Keep prompts concise and symbolic
- Focus on "readable at 24px"
- Use terms like "minimalist", "geometric", "clean lines"
- Example: "Technical drawing icon for 'Estate Planning': minimalist briefcase with document, mechanical poetry style, readable at 24px"

### For Covers
- Emphasize composition and mood
- Include "architectural drawing style" for consistency
- Mention "golden ratio grid" for balanced layouts
- Example: "Blueprint cover for 'Financial Overview': architectural drawing of bank columns and ledger, golden ratio composition, technical precision"

### For Textures
- Focus on seamless patterns
- Specify "tileable" for proper repetition
- Use "technical drawing style" for consistency
- Example: "Seamless texture pattern: grid paper with subtle compass marks, technical drawing style, tileable"

## Best Practices

1. **Edit Before Regenerating**: Always save your prompt edits before queuing for regeneration
2. **Batch Similar Edits**: Edit all similar assets (e.g., all icons) before processing
3. **Test One First**: Regenerate one asset to test your prompt improvements
4. **Track Changes**: The system maintains full prompt history for rollback if needed
5. **Cost Awareness**: Each regeneration costs $0.04 - batch wisely

## Troubleshooting

### Prompts Not Saving
- Ensure `prompts.json` exists in the asset_generation directory
- Check file permissions
- Verify the review server is running from the correct directory

### Regeneration Not Working
- Check if assets are properly queued in `prompts.json`
- Verify REPLICATE_API_KEY is set
- Review logs in `logs/asset_generation.log`

### Review Interface Issues
- Port 4500 might be in use - system will auto-select next available
- Clear browser cache if interface doesn't update
- Check browser console for JavaScript errors

## Advanced Usage

### Bulk Prompt Updates
Edit `prompts.json` directly for mass updates:
```bash
# Edit prompts in your favorite editor
vim prompts.json

# Then regenerate all
python asset_generator.py --regenerate
```

### Prompt Templates
The system includes template support in `prompts.json`:
```json
"prompt_templates": {
  "icons": {
    "base_template": "Technical drawing icon for '{title}': {description}",
    "style_modifiers": ["minimalist", "geometric", "clean"]
  }
}
```

### Integration with Deploy.py
```bash
# Generate assets with deployment
python deploy.py --generate-assets

# Assets only
python deploy.py --assets-only
```

## Git Automation

### Automatic Commits
After successful asset generation, the system automatically:
1. **Stages** all files in the `assets/` directory
2. **Creates** a descriptive commit with generation statistics
3. **Pushes** to the remote repository (if configured)

### Commit Message Format
```
feat(assets): Generate 45 production assets

Generated on: 2024-01-15 14:30:00
Mode: Production

Assets generated:
  - Icons: 21
  - Covers: 21
  - Textures: 3
  - Total: 45

Cost: $8.00
Files changed: 45
```

### Manual Control Options
```bash
# Skip automatic commit (manage Git manually)
python asset_generator.py --no-commit

# Preview what would be committed without actually doing it
python asset_generator.py --dry-run

# Both options together for full manual control
python asset_generator.py --no-commit --dry-run
```

### Git Requirements
- Repository must be initialized (`git init`)
- For auto-push: Remote must be configured (`git remote add origin ...`)
- Clean working directory recommended (uncommitted changes are preserved)

### Error Handling
- If not in a Git repo: Warning logged, generation continues
- If push fails: Commit is created locally, manual push required
- If staging fails: Assets remain uncommitted, manual `git add` required

## Summary

The prompt editing system provides complete control over asset generation:
- ✅ **See** all prompts during review
- ✅ **Edit** prompts in real-time
- ✅ **Save** changes persistently
- ✅ **Queue** selective regeneration
- ✅ **Track** full edit history
- ✅ **Process** regenerations efficiently
- ✅ **Commit** automatically to Git

This ensures you can iteratively refine your assets until they perfectly match your vision, all while maintaining cost control, workflow efficiency, and version control.