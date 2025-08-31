# QR Service Pro — FastAPI + Stripe + Railway

Monetize **QR bundles** that point to **private Notion pages**. Includes:
- **Stripe Checkout** for credits ($9.99 → 10 QRs, $1 → 20-trial one-time)
- **Magic Link sign-in** (email-based; dev page shows link)
- **QR styles** (plain / border / caption)
- **PNG & SVG export**
- **Short redirects** with **scan tracking**
- **Print sheet (PDF)** with up to 12 QRs per page
- **Postgres-ready** via `DATABASE_URL` (SQLite by default)
- **Trial abuse protection**: one-time per email

## Quickstart (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export STRIPE_SECRET_KEY=sk_test_xxx STRIPE_WEBHOOK_SECRET=whsec_xxx SECRET_KEY=dev APP_BASE_URL=http://127.0.0.1:8000
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000

## Deploy to Railway
1. Push this folder to GitHub.
2. Create a new Railway project → Deploy from GitHub.
3. Add env vars:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - `SECRET_KEY`
   - `APP_BASE_URL` (e.g., `https://your.app`)
   - `SUCCESS_URL` (e.g., `https://your.app/success`)
   - `CANCEL_URL` (e.g., `https://your.app/`)
   - `DATABASE_URL` (use Railway Postgres plugin and copy the URL)
4. Add Stripe webhook endpoint: `https://your.app/webhook` with the webhook secret.
5. Launch. Magic link page shows the URL; wire up real email later.

## Notes
- The QR **does not** bypass Notion permissions: viewers must be invited by email to the target Notion page.
- Trial pack is limited to one redemption per email (`trial_redeemed`).
- To harden auth, swap magic-link demo UI for a real email sender (Postmark, SendGrid) and add CSRF protection.
- For persistent QR images, use Railway volumes or S3.
- For analytics, you can add UTM params to the redirect target or log IP/country (mind privacy laws).
