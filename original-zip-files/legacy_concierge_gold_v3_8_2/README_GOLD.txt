Legacy Concierge — GOLD v3.7.9
=================================
This bundle includes:
 • deploy/deploy.py — single-script deployer (preview + y/n), recursive idempotency markers, SYNC_KEY-based synced blocks, rollout summary.
 • split_yaml/ — all pages & databases (core + patches 08–19).

How to run on a fresh laptop:
 1) Ensure Python 3.10+
 2) Create a .env with:
    NOTION_TOKEN=secret_xxx
    NOTION_VERSION=2022-06-28
    ASSET_BASE_URL=https://yourdomain.github.io/notion-assets   # optional but recommended
    ADMIN_HELP_URL=https://yourdomain.github.io/help            # optional
 3) Install dependencies (requests, python-dotenv if used)
 4) Run:
    python deploy/deploy.py --dir split_yaml
 5) Review preview → type 'y' to proceed.
 6) Complete Admin steps (if any), then delete Admin pages before sharing.

Bundled on: 2025-08-30T08:09:12Z

Audit-Pass Features in v3.8.2:
 - Full preflight (assets/slugs/relations/formulas/rollups/placeholders)
 - Slug-based relations and Pages Index enforcement
 - Deployment Ledger (JSON + Admin DB)
 - Throttled requests (~2.5 RPS) + retries
 - Basic rollback on failure
 - Synced block self-healing (ledgers, guarded)
 - Blueprints tracked in Admin DBs (Views/Rollups)
 - Artifacts in ./artifacts for auditor verification
