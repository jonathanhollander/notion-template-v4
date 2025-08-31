README — deploy_v3_2a.py (Multi-YAML, Centralized Strings)
Generated: 2025-08-30T01:43:19.013017Z

What this script does
- Loads split YAML files (meta/globals/databases/pages/subpages/diagnostics/acceptance/addons/admin)
- Resolves 'use_global.strings.pages.<slug>.*' into real text for headings, descriptions, instructions, prompts, disclaimers
- Creates databases first (then seeds rows), then creates pages and subpages
- Stores the parent page id in .deploy_state.json for next runs
- Runs in dry-run by default (unless you pass --deploy)

Quick start
1) pip install -r requirements.txt
2) Set env:
   - NOTION_TOKEN=secret_api_token
   - (optional) NOTION_VERSION=2022-06-28
   - (optional) NOTION_PARENT_PAGEID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
3) Run preview:
   python deploy_v3_2a.py --dir ../your/split/yaml --dry-run
4) Deploy:
   python deploy_v3_2a.py --dir ../your/split/yaml --deploy

Notes
- Views (filters/sorts/layout) still must be created manually in Notion. We include 'view_recipes' in admin/addons to guide you.
- Icons & covers are pulled from globals.icons_map and addons.assets.* (emoji and external URLs).
- To re-run in a new workspace, delete .deploy_state.json or pass NOTION_PARENT_PAGEID.
