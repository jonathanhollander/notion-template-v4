Legacy Concierge – Full Bundle v3.6.0

What this bundle does
- Creates all pages from split YAML with icons, descriptions, disclaimers.
- Adds collapsed, step-by-step "⚠️ Setup Helper" toggles for manual actions (nesting, DB views, icons).
- Creates the unified "Setup & Acceptance" database and seeds Acceptance rows for every page & subpage with realistic time estimates.
- Creates content databases (Accounts, Property, Insurance, Contacts, Subscriptions, Keepsakes, Letters Index) and seeds example rows.
- Generates Letters as subpages with sample bodies.
- Adds a Release Notes page with full version history.
- Writes a live Rollout Summary (section subtotals + total time).

How to run
1) pip install -r deploy/requirements.txt
2) cp deploy/.env.example .env
3) Set NOTION_TOKEN and NOTION_PARENT_PAGEID (and optionally ICON_BASE_URL for hosted icons)
4) Preview: python deploy/deploy_v3_5.py --dir split_yaml --dry-run
5) Deploy:  python deploy/deploy_v3_5.py --dir split_yaml --deploy
6) Update:  python deploy/deploy_v3_5.py --dir split_yaml --update

Notes
- Notion API cannot create saved views; the script adds hub-level helper toggles with exact steps to add them manually.
- Manual nesting: pages are created under the provided parent; helper toggles instruct you to drag them into their hubs.
- Delete helpers once complete—rows auto-flip to Done in the unified DB on the next --update.

v3.6.1 (no new features — gap closure)
- Restored helper upsert + auto-Done and live DB-driven Rollout (regression fix from 3.5.9).
- Added hub saved-view helper toggles to each hub (manual steps, collapsed).
- Expanded page inventory (~100+ with executor tasks, digital assets guides, agency guides).
- Introduced centralized copy registry (00_copy_registry.yaml); pages can reference by slug.
- Expanded letters catalog (SSA, IRS, DMV, USPS, mortgage, landlord/HOA, pension/401k, brokerage, credit bureaus) + QR pack cover letters.
- Beefed up DB seeds with more varied examples.
- Refined time estimates for specific page types (digital assets, executor tasks, guides, QR pages).
- Moved Release Notes into an Admin branch (“Admin – Release Notes”).

v3.6.2 (gap-closure, no new features)
- Compassionate, page-specific helper instructions across the template.
- Acceptance rows carry unique checks and refined time estimates.
- Letters pages include draft + disclaimer + AI prompt.
- Legal sample documents include structured sections + disclaimers + AI prompt.
- Tailored DB helper pages created; acceptance items added for each.
- Admin branch completed with Rollout Cockpit and Diagnostics.
- Emoji icons preserved; optional hosted icon filenames supported via ICON_BASE_URL.

v3.6.3 Visual Cohesion Patch
- Bundled semantic-named placeholder assets in /assets/icons and /assets/covers (SVG).
- YAML references these filenames via icon_file / cover_file.
- IMPORTANT: Notion API requires public URLs for icons/covers. Set ASSET_BASE_URL (or ICON_BASE_URL) to the public folder where you host /assets/ so the deployer can attach them.
  - Example: ASSET_BASE_URL=https://yourdomain.com/notion-assets
  - Then /assets/icons/preparation-hub-icon.svg will resolve to https://yourdomain.com/notion-assets/assets/icons/preparation-hub-icon.svg
- Until you host assets, emoji icons remain the fallback, and covers may remain default.

v3.7.0 Ultra-Premium UX Patch
- Start Here and Welcome dashboards added (no fake data).
- Hub pages transformed into dashboards with section links and guidance.
- Back-to-Hub and Next-step navigation links added to all child pages.
- Database seed rows removed entirely (no stubs or fake entries).
- Letters/legal content written as real, generic drafts with instructions, no dummy names/numbers.
- Callouts aligned by role (Executor blue, Family peach, Owner teal) where applicable.

v3.7.1 User-Facing UI Polish
- Start Here & Hubs converted to card/tile dashboards (role-colored callouts in columns).
- Universal navigation: Back-to-Hub and Next Step on all subpages (including letters/legal).
- Role color alignment inside pages (executor blue, family peach, preparation teal/gray).
- Progress summaries added to hubs (with helper on how to view Pending).
- First-run checklist embedded in Start Here.
- Keepsakes structured (Photos, Stories, Letters) with gentle prompts.
- Legal & Letters pages reformatted for skimmability (Purpose, Draft toggle, Disclaimer callout).
- Accessibility captions under tiles.
- Naming & slugs standardized across extended pages.
- PNG icons/covers generated for maximum reliability; YAML points to PNG by default.

v3.7.2 Premium UI Patch (user-facing)
- Start Here & Hubs now true dashboards: card grids, dividers, captions, mobile notes, top-nav row.
- Global Quick Jump not a separate page (kept simple): hub top-nav links + Start Here grid cover all flows.
- Hero block added to every user page (no duplicates on rerun).
- Letters & Legal: long draft/sample sections moved under collapsible toggles.
- Brand accents via role-colored callouts; strict heading hierarchy.
- Emotional completion cue appears during `--update` when Acceptance row flips to Done.
- Admin 'Final UI Checklist' page added (deletable).

v3.7.3 (DB Seeds – Real Project Data)
- Seeded all available databases with durable, project-relevant entries (no demo names).
- Accounts, Property, Insurance, Contacts, Subscriptions, Keepsakes, Letters Index now deploy ready-to-use.
- Acceptance rows remain in zz_acceptance_rows.yaml and mirror the page tree.

v3.7.3a Brokerage Details Patch
- Accounts DB: replaced generic 'Brokerage Accounts' with detailed, durable entries:
  • Brokerage – Taxable (Individual), Brokerage – Taxable (Joint),
  • Brokerage – Traditional IRA, Brokerage – Roth IRA,
  • Brokerage – 529 College Savings
  Each row includes concrete next steps (DTC forms, beneficiary/TOD, cost basis, medallion).
- Letters Index DB: added 'Letter – Brokerage Firms' category.

v3.7.4 API Max Patch
- Relations from DB rows to related subpages (title-matched) now auto-populate.
- Acceptance DB 'Check' formula shows ✅ when Status = Done.
- Rich-text seeds (italic/gray) used for Notes to improve scannability.
- Multi-select defaults across Accounts, Insurance, Subscriptions, Contacts, Keepsakes, Letters Index.
- Synced blocks: master disclaimers/helpers page added; synced copies placed on Legal, Letters, Executor.

v3.7.5 Audit Fix Patch
- Implemented true Notion relations from seed rows using "Related Page Title".
- Acceptance DB "Check" is now a real formula (✅ when Status=Done).
- Seeded Notes/Note properties render as italic gray rich_text.
- Multi-select defaults respected in seed processing.
- Robust request handling incl. 504 and proper JSON parsing.
- All helper functions defined (no NameError), navigation/hero blocks preserved.

v3.7.6 Post-Audit Hardening
- Relations: robust title→ID resolution with optional /v1/search fallback; breadcrumb if unresolved.
- Synced blocks: stable SYNC_KEY markers (LEGAL/LETTERS/EXECUTOR) instead of brittle text parsing.
- Acceptance DB: Check formula enforced at create; patch safeguard kept.
- Notes: unified 'Note' property, rich_text italic gray; merged 'Notes'→'Note' in seeds.
- Icons: URL-safe path join for external assets.
- Error handling: expect_ok() + clearer logs; dry-run shows merged counts.

v3.7.7 Post-Audit Fixes II
- Hero/content: single-pass hero injection at page create; no duplicate hero blocks.
- Navigation: Back-to-Hub + Next-step links added to child pages (toggle group with link_to_page blocks).
- Mobile tips: 📱 callout added to Hub pages (YAML 'hub: true' or default hub titles).
- Icons: external SVG accepted in resolve_icon.
- Letters/Legal: Body and Disclaimer fields rendered (toggle for Draft; callout for Disclaimer).
