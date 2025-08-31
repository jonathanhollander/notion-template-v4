Legacy Concierge — GOLD v3.8.3

ENV
  NOTION_TOKEN=secret_xxx
  ROOT_PAGE_ID=xxxx-xxxx
  ASSET_BASE_URL=https://your.host/assets   (optional but recommended)
  THROTTLE_RPS=2.5

RUN
  python deploy/deploy.py --dir split_yaml

ARTIFACTS (generated in ./artifacts)
  capabilities.json
  preflight_report.json
  deployment_ledger.json
  relations_report.json
  manual_tasks_report.json
  transaction_log.json

NOTES
  • Saved views / linked DB embeds / some rollup UI steps are manual-by-API. They are tracked via Admin databases and Acceptance tasks.
  • Re-run safe: idempotent helpers; basic rollback archives objects created during a failed run.
