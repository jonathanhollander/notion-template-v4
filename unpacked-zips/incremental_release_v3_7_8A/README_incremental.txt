INCREMENTAL RELEASE v3.7.8A
---------------------------
This package contains two YAML patches to elevate the workspace toward ultra-premium while keeping all auditor fixes intact.

FILES
 • 08_ultra_premium_db_patch.yaml
   - Adds master–detail DBs (Transactions, Maintenance Logs, Insurance Claims)
   - Adds Estate Analytics DB (formula-driven; rollup-ready)
   - Adds Archive/Progress formulas to core DBs
   - Seeds realistic example rows
 • 09_admin_rollout_setup.yaml
   - Admin-only Rollout branch with step-by-step guides for UI rollups and saved views
   - Admin QA checklist
   - Acceptance tasks so the Rollout Summary reflects progress

HOW TO APPLY
1) Copy both YAML files into your project’s split_yaml/ directory.
2) Run a dry run to preview:
   python deploy/deploy_v3_5.py --dir split_yaml --dry-run
3) Deploy:
   python deploy/deploy_v3_5.py --dir split_yaml --deploy
4) Complete the Admin steps, verify Rollout Summary → 100%, then delete the "Admin – Rollout" page.

NOTES
- These patches rely on v3.7.8 deployer (Pages Index DB, relation idempotency, markers).
- No OAuth or external systems required.
- All additions are idempotent and safe to re-run.
