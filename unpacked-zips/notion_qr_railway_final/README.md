# Railway FastAPI — Full Stack (Promos + Widget + Analytics + DB Nudges)
Built 2025-08-23T07:23:20.056821Z

**What’s inside**
- Storefront: `/` and `/promo/{id}` (Top‑10 + Complete seeded).
- Stripe checkout scaffold (works without keys in dev).
- **Nudge widget** `/widget/nudge?family|executor` for Notion embeds:
  - Creates an **anonymous wid** cookie if OAuth creds aren’t set.
  - Pulls nudge text from **DB table `nudges`** (fallback to hardcoded if empty).
- Analytics: `installs`, `sessions`, `events`, `visits` tables.
- Content-free `metrics_snapshots` table for future polling.
- Auto-run **all migrations** on startup.
- Admin: `/admin/sync-products` (Bearer token).

**Deploy**
1. Push to GitHub.
2. Railway → New Project → Deploy from GitHub.
3. Add **Postgres** (Railway sets `DATABASE_URL`).
4. Set env vars from `.env.example`.
5. Visit `/healthz`.

**Use in your Notion template**
- Family Dashboard embed: `https://YOURAPP.up.railway.app/widget/nudge?family`
- Executor Dashboard embed: `https://YOURAPP.up.railway.app/widget/nudge?executor`

**Extend later**
- Implement Notion OAuth in `/widget/oauth/*` if you need workspace-bound actions.
- Add a poller to populate `metrics_snapshots` with content-free counts.
- Integrate QR image generation + direct Notion upload in the connect flow.
