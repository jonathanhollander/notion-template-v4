Legacy Concierge — FULL bundle v3.4 (Undertones everywhere + 17 letters)
Generated: 2025-08-30T02:26:33.184705Z

What's new vs v3.3
- All page/subpage copy carries context-aware undertones (executor clarity; family invitation).
- Letters Library expanded to 17 seeded letters (14 executor, 3 family), and mapped to relevant sections.
- All text centralized in globals.strings.pages.*; disclaimers and diagnostics phrasing centralized in globals.*.

How to run
1) pip install -r deploy/requirements.txt
2) Set NOTION_TOKEN (and optionally NOTION_PARENT_PAGEID)
3) Preview: python deploy/deploy_v3_4.py --dir split_yaml --dry-run
4) Deploy:  python deploy/deploy_v3_4.py --dir split_yaml --deploy
