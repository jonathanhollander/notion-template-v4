HOW_TO_MERGE.md
Generated: 2025-08-30T01:45:04.262750Z

Folder structure
- deploy/        → deploy_v3_2a.py, requirements.txt, README_DEPLOY.md, .env.example
- yaml_addons/   → admin.yaml, addons.yaml, README_ADMIN.txt (and any notes)

How to use
1) Place your existing split YAML bundle (meta.yaml, globals.yaml, databases.yaml, pages.yaml, subpages.yaml, diagnostics.yaml, acceptance.yaml)
   in a directory, e.g.:  /path/to/split_yaml/

2) Copy the two add-on files into that same directory:
   - yaml_addons/admin.yaml
   - yaml_addons/addons.yaml

3) Run the deploy script in dry-run from the deploy folder:
   python deploy/deploy_v3_2a.py --dir /path/to/split_yaml --dry-run

4) If the plan looks correct, deploy:
   python deploy/deploy_v3_2a.py --dir /path/to/split_yaml --deploy

Notes
- The script auto-loads admin.yaml and addons.yaml if present; otherwise it proceeds without them.
- Admin branch is marked is_admin: true and Diagnostics ignores it by default.
- Delete the entire Admin branch before shipping to end users.
