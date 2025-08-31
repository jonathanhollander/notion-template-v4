import os, json

APP_BASE_URL = os.environ.get("APP_BASE_URL","")
ASSET_STORAGE = os.environ.get("ASSET_STORAGE","notion")
if ASSET_STORAGE != "notion":
    raise RuntimeError("This build enforces Notion-only storage. Set ASSET_STORAGE=notion.")

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY","")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET","")

NOTION_CLIENT_ID = os.environ.get("NOTION_CLIENT_ID","")
NOTION_CLIENT_SECRET = os.environ.get("NOTION_CLIENT_SECRET","")
NOTION_REDIRECT_URI = os.environ.get("NOTION_REDIRECT_URI","")

PACKS_JSON = json.loads(os.environ.get("PACKS_JSON","[]"))
CLASSIFICATION_RULES_JSON = json.loads(os.environ.get("CLASSIFICATION_RULES_JSON","{}"))
