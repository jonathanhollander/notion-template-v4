
v3.5.9 PATCH KIT (use if you can't replace your whole bundle):
- Unified Setup & Acceptance DB (Helper + Acceptance) with collapsed step-by-step helper toggles.
- Helper rows auto-mark Done when toggles removed; Rollout totals from live DB.
- Hub pages get a toggle explaining how to add saved views.
- Preflight summary at startup.
Drop deploy/deploy_v3_5.py over your existing bundle. Put zz_acceptance_rows.yaml in split_yaml/.
