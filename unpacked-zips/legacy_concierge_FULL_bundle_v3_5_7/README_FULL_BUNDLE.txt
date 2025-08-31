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

v3.5.4: Helper notes are ONE-WAY. Once you delete a “⚠️ Setup Helper” on a page, the script records it and will NOT re-add it on future runs. Use --reset-helpers to forget this state.

v3.5.5: Parent-aware behavior.
- Default: if intended parent exists, the script does NOT add child links and does NOT add a helper if the page is already nested there.
- Flags: --link-children (adds link_to_page under intended parents), --force-helpers (re-add helpers even if previously cleared and page not nested).

v3.5.6: Acceptance DB auto-seeding from YAML (idempotent), and Letters Index de-dup by title.
YAML shape for acceptance rows: acceptance: { rows: [ {Page, Role, Check, Status}, ... ] }

v3.5.7: Unified "Setup & Acceptance" DB replaces separate Acceptance tracking.
- Columns: Page, Role, Type (Helper/Acceptance), Check, Status (Pending/Done), Est. Time (minutes), Section, PageURL, PageID.
- Helpers are auto-inserted when a page contains a “⚠️ Setup Helper”. Acceptance rows are seeded from YAML.
- Rollout Summary shows section subtotals and totals (pending count + estimated minutes).
NOTE: Notion’s API does not support saved views or linked-database creation. Views suggested in the docs must be added manually (the script inserts Setup Helpers with wording to guide that step).
