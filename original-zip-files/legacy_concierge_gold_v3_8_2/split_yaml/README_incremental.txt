INCREMENTAL YAML POLISH v3.7.9B
-------------------------------
This pack addresses the audit's UX/content items without requiring script changes.

WHAT'S INSIDE
 • 16_letters_database.yaml — New Letters database with realistic seeds, plus a parallel 'Letters – Library (Pages)' branch.
 • 17_hub_copy_polish.yaml — Warmer, action-forward hub copy (Preparation, Executor, Family).
 • 18_admin_helpers_expanded.yaml — Guided helpers with screenshot/link placeholders (uses ADMIN_HELP_URL).
 • 19_assets_standardize_patch.yaml — Enforces single asset host and consistent naming (Admin checklist).

HOW TO APPLY
1) Place these files in split_yaml/ alongside your existing YAML.
2) Run the deployer (v3.7.8C or newer):
   python deploy/deploy.py --dir split_yaml
3) Complete any Admin tasks and delete Admin pages before sharing.

NOTES
- Letters exist both as a Database **and** as individual pages, satisfying “DB-first but still subpages” intent.
- All content is idempotent-safe because deployer injects with markers for long bodies/disclaimers.
