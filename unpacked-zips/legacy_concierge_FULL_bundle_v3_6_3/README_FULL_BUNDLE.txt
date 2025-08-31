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

v3.6.1 (no new features — gap closure)
- Restored helper upsert + auto-Done and live DB-driven Rollout (regression fix from 3.5.9).
- Added hub saved-view helper toggles to each hub (manual steps, collapsed).
- Expanded page inventory (~100+ with executor tasks, digital assets guides, agency guides).
- Introduced centralized copy registry (00_copy_registry.yaml); pages can reference by slug.
- Expanded letters catalog (SSA, IRS, DMV, USPS, mortgage, landlord/HOA, pension/401k, brokerage, credit bureaus) + QR pack cover letters.
- Beefed up DB seeds with more varied examples.
- Refined time estimates for specific page types (digital assets, executor tasks, guides, QR pages).
- Moved Release Notes into an Admin branch (“Admin – Release Notes”).

v3.6.2 (gap-closure, no new features)
- Compassionate, page-specific helper instructions across the template.
- Acceptance rows carry unique checks and refined time estimates.
- Letters pages include draft + disclaimer + AI prompt.
- Legal sample documents include structured sections + disclaimers + AI prompt.
- Tailored DB helper pages created; acceptance items added for each.
- Admin branch completed with Rollout Cockpit and Diagnostics.
- Emoji icons preserved; optional hosted icon filenames supported via ICON_BASE_URL.

v3.6.3 Visual Cohesion Patch
- Bundled semantic-named placeholder assets in /assets/icons and /assets/covers (SVG).
- YAML references these filenames via icon_file / cover_file.
- IMPORTANT: Notion API requires public URLs for icons/covers. Set ASSET_BASE_URL (or ICON_BASE_URL) to the public folder where you host /assets/ so the deployer can attach them.
  - Example: ASSET_BASE_URL=https://yourdomain.com/notion-assets
  - Then /assets/icons/preparation-hub-icon.svg will resolve to https://yourdomain.com/notion-assets/assets/icons/preparation-hub-icon.svg
- Until you host assets, emoji icons remain the fallback, and covers may remain default.
