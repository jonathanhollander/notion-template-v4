# Railway FastAPI — Empathetic Companion (no 'nudge' wording)
Built 2025-08-23T07:53:20.172495Z

**Public endpoints**
- Widget (embed in Notion):
  - Family: `/widget/companion?family`
  - Executor: `/widget/companion?executor`
  - Always renders. When disabled server-side, shows a calm placeholder so analytics continue.

**Admin endpoints** (Bearer `ADMIN_TOKEN`):
- `POST /admin/messages/workspace-toggle` — `{"wid":"...","enabled":true|false}`
- `POST /admin/messages/default` — `{"enabled":true|false}` (global default for new workspaces)
- `POST /admin/messages/rotation` — `{"ids":[...],"include":true|false}`

**Database**
- `gentle_messages` — empathetic message bank (audience, text, enabled, include_in_rotation)
- `installs` with `companion_enabled`
- `app_settings('companion_default')`
- analytics: `sessions`, `events`, `visits`
- future progress: `metrics_snapshots`

**Deploy on Railway**
1. Push repo to GitHub.
2. Railway → New Project → Deploy from GitHub.
3. Add **Postgres**; ensure `DATABASE_URL` is set.
4. Set env vars via `.env.example`.
5. Visit `/healthz`.
6. Add to Notion as Embed using the URLs above.

**Notes**
- All UI copy uses *empathetic* language; no “nudge” wording anywhere.
- You can expand `gentle_messages` with hundreds of localized lines later.
