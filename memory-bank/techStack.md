
## Tech Stack

[2025-09-01 02:21:24] - # Estate Planning v4.0 Asset Generation - Technical Stack

## Core Technologies
- **Python 3.9+** - Primary language with type hints
- **asyncio** - Asynchronous I/O for concurrent API calls
- **aiohttp** - Async HTTP client for API interactions

## AI Integration
- **OpenRouter API** - Unified gateway to multiple AI models
- **Claude 3.5 Sonnet** - Anthropic's model for creative content
- **GPT-4** - OpenAI's model for versatile generation
- **Gemini** - Google's model for balanced output

## Architecture Patterns
- **Competitive Generation** - 3 models compete per asset
- **Dynamic Prompt Loading** - Runtime configuration via master_prompt.txt
- **5-Tier Visual Hierarchy** - Structured content organization
- **Async Orchestration** - Parallel processing with asyncio.gather()

## File Processing
- **YAML** - PyYAML for configuration management
- **JSON** - Structured data and API responses
- **Markdown** - Documentation and report generation

## Key Modules
- openrouter_orchestrator.py - Central API management
- asset_generator.py - Asset creation logic
- prompt_templates.py - Dynamic template system
- emotional_elements.py - Context-aware content
- visual_hierarchy.py - 5-tier implementation
- quality_scorer.py - Output evaluation

## Performance Features
- Concurrent API calls to 3 models
- Rate limiting with exponential backoff
- Idempotent retry mechanisms
- Structured logging with rotation
