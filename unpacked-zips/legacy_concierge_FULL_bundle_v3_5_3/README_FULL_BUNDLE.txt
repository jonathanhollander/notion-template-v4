Legacy Concierge — FULL bundle v3.5
Complete build with split YAML and a loader that merges multiple files.

Includes:
- All pages (~60) with covers, icons, compassionate descriptions, and disclaimers where needed.
- Letters library (17) standardized with disclaimers.
- Databases with schemas + seed rows (no blank states).
- Diagnostics rules with severity levels; Acceptance criteria by role and page.
- Builder’s Console (admin) with diagnostics overview.
- Gradient diamond icon set (SVG + PNG) embedded.
- Deploy script supports split YAML, dry-run preview, caching Notion parent page ID.


Tip: To use custom diamond icons instead of emoji, host /assets/icons/* publicly and set ICON_BASE_URL in .env.


v3.5.2: Launch script shows a full CHANGE PLAN (create/update) and requires explicit y/N before any changes.
Use --deploy (create new) and/or --update (patch existing). Diagnostics are populated from YAML rules.


v3.5.3: Inline “⚠️ Setup Helper” notes are inserted where the API falls short (manual nesting, DB views/templates).
The Rollout Summary page lists direct links to every page that still has a helper note. Delete the note on the page, then run --update to refresh the list.
