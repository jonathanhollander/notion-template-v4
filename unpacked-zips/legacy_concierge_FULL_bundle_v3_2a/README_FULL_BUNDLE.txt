Legacy Concierge — FULL bundle v3.2a
Generated: 2025-08-30T01:46:37.483013Z

Folders
- split_yaml/   : meta.yaml, globals.yaml, databases.yaml, pages.yaml, subpages.yaml, diagnostics.yaml, acceptance.yaml, README_v3_2a_split.txt, PARSER_UPDATE_NOTES.md
- yaml_addons/  : admin.yaml, addons.yaml, README_ADMIN.txt
- deploy/       : deploy_v3_2a.py, requirements.txt, README_DEPLOY.md, .env.example

Usage
1) Review split_yaml/ for content; keep QR Codes Reference untouched as requested.
2) (Optional) Edit yaml_addons/admin.yaml and addons.yaml.
3) Install deps:  pip install -r deploy/requirements.txt
4) Preview:       python deploy/deploy_v3_2a.py --dir split_yaml --dry-run
5) Deploy:        python deploy/deploy_v3_2a.py --dir split_yaml --deploy

Admin branch note
- Admin adds 11 sub-pages under ⚙️ Admin / Rollout Cockpit (10 admin DBs + Cleanup Notes page). All marked is_admin: true and ignored by diagnostics.
- Delete the entire Admin branch before shipping.

