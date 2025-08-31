# Railway QR Server — Notion Direct Upload Only
Built 2025-08-23T05:53:37.229018Z

This app **only** embeds QR images via Notion **Direct Upload** (no external hosting).

## Deploy (Railway → GitHub)
1) Push to GitHub.
2) Railway → New Project → Deploy from GitHub.
3) Set Variables from `.env.example`.
4) Add Stripe webhook: `POST /webhook`.
5) Open `/` → buy pack → Connect Notion → paste Menu page ID → Generate.

## Notes
- Env `ASSET_STORAGE` is forced to `notion`; the app exits otherwise.
- The function `direct_upload_image_and_get_file_object` uses a documented 2‑step create‑file + PUT upload flow; update if Notion changes endpoints.
