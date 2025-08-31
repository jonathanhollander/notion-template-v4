INCREMENTAL SCRIPT PATCH v3.7.9A
--------------------------------
Upgrades deploy/deploy.py with:
• Recursive marker detection for idempotency (no duplicate add-ons)
• Stable SYNC_KEY:: originals and synced references
• Live Rollout Summary callout from Setup & Acceptance DB
• Keeps single-script, no --dry-run; always previews and asks y/n
