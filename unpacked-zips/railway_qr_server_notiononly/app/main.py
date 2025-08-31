import os, json, io
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from .settings import *
from .qr import make_qr_png
from .notion_flow import (
    oauth_token_exchange, get_client, find_roots, crawl_subtree,
    retrieve_page_url, ensure_page, direct_upload_image_and_get_file_object,
    append_image_block_from_file
)
import stripe

stripe.api_key = STRIPE_SECRET_KEY

app = FastAPI(title="QR to Notion (Direct Upload Only)")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    packs = PACKS_JSON
    return templates.TemplateResponse("home.html", {"request": request, "packs": packs})

@app.post("/checkout")
def checkout(request: Request, pack_id: str = Form(...)):
    pack = next((p for p in PACKS_JSON if p["id"] == pack_id), None)
    if not pack: raise HTTPException(404, "Unknown pack")
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": pack["price_id"], "quantity": 1}],
        success_url=f"{APP_BASE_URL}/post-checkout?pack_id={pack_id}",
        cancel_url=f"{APP_BASE_URL}/"
    )
    return {"url": session.url}

@app.get("/post-checkout", response_class=HTMLResponse)
def post_checkout(request: Request, pack_id: str):
    # Prompt to connect Notion
    return templates.TemplateResponse("connect_notion.html", {"request": request, "pack_id": pack_id, "client_id": NOTION_CLIENT_ID, "redirect_uri": NOTION_REDIRECT_URI})

@app.get("/oauth/callback")
def oauth_callback(request: Request, code: str, state: str = ""):
    tok = oauth_token_exchange(NOTION_CLIENT_ID, NOTION_CLIENT_SECRET, NOTION_REDIRECT_URI, code)
    access_token = tok["access_token"]
    return RedirectResponse(url=f"/select-menu?token={access_token}")

@app.get("/select-menu", response_class=HTMLResponse)
def select_menu(request: Request, token: str):
    # Ask user to paste the top-level Menu page URL or pick via lightweight UI.
    return templates.TemplateResponse("select_menu.html", {"request": request, "token": token})

@app.post("/generate", response_class=HTMLResponse)
def generate(request: Request, token: str = Form(...), menu_page_id: str = Form(...), pack_id: str = Form(...)):
    if ASSET_STORAGE != "notion":
        raise HTTPException(500, "Server is configured to require Notion direct upload only.")

    notion = get_client(token)
    buckets = CLASSIFICATION_RULES_JSON.get("buckets", {})
    fam_root_title = buckets.get("family_root","Family Portal")
    exe_root_title = buckets.get("executor_root","Executor Console")

    fam_root, exe_root = find_roots(notion, menu_page_id, fam_root_title, exe_root_title)
    if not fam_root or not exe_root:
        return HTMLResponse(f"<h3>Could not find Family/Executor roots under the selected Menu.</h3><p>Found: family={fam_root}, executor={exe_root}</p>")

    family_pages = crawl_subtree(notion, fam_root)
    executor_pages = crawl_subtree(notion, exe_root)

    # Choose subset based on pack
    pack = next((p for p in PACKS_JSON if p["id"] == pack_id), None)
    if not pack: raise HTTPException(404, "Unknown pack")
    qr_set = pack.get("qr_set","complete")

    def filter_pages(pages, wanted_titles):
        title_set = {t.lower() for t in wanted_titles}
        return [p for p in pages if p["title"].lower() in title_set]

    if qr_set == "top10":
        wanted = CLASSIFICATION_RULES_JSON.get("top10",{})
        family_pages = filter_pages(family_pages, wanted.get("family",[]))
        executor_pages = filter_pages(executor_pages, wanted.get("executor",[]))
    # else complete → keep all

    # Prepare output pages
    fam_qr_page = ensure_page(notion, fam_root, "My QR Codes — Family")
    exe_qr_page = ensure_page(notion, exe_root, "My QR Codes — Executor")

    # Generate & upload
    for subset, parent in ((family_pages, fam_qr_page), (executor_pages, exe_qr_page)):
        for item in subset:
            url = retrieve_page_url(notion, item["page_id"])
            png = make_qr_png(url)
            file_obj = direct_upload_image_and_get_file_object(token, png, f"{item['title']}.png")
            append_image_block_from_file(notion, parent, file_obj, caption_text=item["title"])

    return templates.TemplateResponse("done.html", {"request": request, "family_count": len(family_pages), "executor_count": len(executor_pages)})

# Webhook (optional if you want to lock generation to paid sessions)
@app.post("/webhook")
async def webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(400, str(e))
    # TODO: set a flag in your DB/session if you want to enforce payment before generation.
    return {"ok": True}
