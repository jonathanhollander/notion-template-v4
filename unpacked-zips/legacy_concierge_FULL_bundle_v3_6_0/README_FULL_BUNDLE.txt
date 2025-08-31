Legacy Concierge – Full Bundle v3.6.0

What this bundle does
- Creates all pages from split YAML with icons, descriptions, disclaimers.
- Adds collapsed, step-by-step "⚠️ Setup Helper" toggles for manual actions (nesting, DB views, icons).
- Creates the unified "Setup & Acceptance" database and seeds Acceptance rows for every page & subpage with realistic time estimates.
- Creates content databases (Accounts, Property, Insurance, Contacts, Subscriptions, Keepsakes, Letters Index) and seeds example rows.
- Generates Letters as subpages with sample bodies.
- Adds a Release Notes page with full version history.
- Writes a live Rollout Summary (section subtotals + total time).

How to run
1) pip install -r deploy/requirements.txt
2) cp deploy/.env.example .env
3) Set NOTION_TOKEN and NOTION_PARENT_PAGEID (and optionally ICON_BASE_URL for hosted icons)
4) Preview: python deploy/deploy_v3_5.py --dir split_yaml --dry-run
5) Deploy:  python deploy/deploy_v3_5.py --dir split_yaml --deploy
6) Update:  python deploy/deploy_v3_5.py --dir split_yaml --update

Notes
- Notion API cannot create saved views; the script adds hub-level helper toggles with exact steps to add them manually.
- Manual nesting: pages are created under the provided parent; helper toggles instruct you to drag them into their hubs.
- Delete helpers once complete—rows auto-flip to Done in the unified DB on the next --update.
