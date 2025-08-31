v3.4a Premium-Polish Patch (no new features)
Generated: 2025-08-30T02:32:40.188210Z

What this patch does
- Tightens executor letters into a uniform, professional structure with consistent closings.
- Sharpens executor page descriptions so action is obvious (without being harsh).
- Clarifies disclaimers (gentle but firmer on legal/medical pages).
- Expands diagnostics messages with “why it matters” coaching.
- Makes the closure page more ceremonial and reassuring.
- Adds a content-only Readiness Checklist to the Admin Cockpit (copy these blocks into admin.yaml).

How to apply
1) Open split_yaml/globals.yaml
   - Merge the contents under:
     globals.covers_map
     globals.strings.caution_notes
     globals.strings.pages (only the keys present in this patch)
     globals.diagnostics_text
   This is an overwrite for the listed keys only.

2) Open split_yaml/databases.yaml
   - Under db.seeds.sample_letters, replace Body for matching Title.
   - The field update_by_title: true indicates you should match rows by 'Title'.

3) Open yaml_addons/admin.yaml
   - Add the suggested 'Readiness Checklist' blocks near the top of the Admin / Rollout Cockpit page content.

4) Re-run deployment in dry-run first:
   python deploy/deploy_v3_4.py --dir split_yaml --dry-run
   (Then --deploy when satisfied.)

Notes
- No new pages or databases are introduced. This only polishes copy and defaults.
- If your deploy flow doesn't support partial seed updates, you may delete Sample Letters rows before seeding to avoid duplicates.
