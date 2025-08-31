# Legacy Concierge (Premium) — Notion Deploy Package (v2)

## Files
- `spec.v2.yml` — full template spec: pages, DBs, seeds, instructions, covers.
- `deploy_notion_template.py` — deploy script with PLAN → APPLY, tracker, diagnostics.
- `covers/` — placeholder cover images (replace with your own).

## Prereqs
1. Create a Notion internal integration and share the parent page with it.
2. pip install notion-client pyyaml requests
3. export NOTION_TOKEN=secret_...

## Run
python deploy_notion_template.py spec.v2.yml
