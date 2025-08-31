Admin & Setup Add-ons — v3.2a
Generated: 2025-08-30T01:39:30.358806Z

Included:
- admin.yaml   : Top-level Admin/Rollout branch (Cockpit page + 10 admin databases + Cleanup Notes subpage).
- addons.yaml  : 20 YAML add-ons for smoother setup (ordering, runbook hints, nav, assets manifest, placeholders policy,
                 tone/style guards, audience hints, view/share recipes, diagnostics config, safety/merge rules,
                 readability checks, purpose blurbs, redaction reminders, disclaimers map, status tags, slug registry,
                 CLI verbosity strings, finalize sweep).

Admin sub-pages added (under Admin / Rollout Cockpit):
1) Rollout Tasks (DB) — your running Kanban/list by Phase & Status; drives real-time completion %.
2) Assets Inventory (DB) — tracks icons, covers, headers; what's missing or final.
3) View Recipes (DB) — the manual Notion view configurations the API cannot create.
4) Share Recipes (DB) — repeatable instructions on who to share with and how.
5) Risk & Issues (DB) — blockers with severity and owners.
6) Change Log (DB) — what changed, when, and why (audit trail).
7) Open Questions / Parking Lot (DB) — decisions needed, owners, outcomes.
8) Strings Audit (DB) — pages whose compassionate copy needs polish; assign a reviewer.
9) QR Audit (DB) — quick check for QR placeholders or linked images (reference only).
10) Post-Deploy QA (DB) — checklist of checks for mobile/print/links/assets after creation.
11) Cleanup Notes (page) — exact deletion steps; remove entire Admin branch before shipping.

All Admin items are marked is_admin: true, and diagnostics ignore them by default.
