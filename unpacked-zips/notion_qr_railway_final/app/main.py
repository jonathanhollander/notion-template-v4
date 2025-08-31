import os, glob, datetime
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from .db import db_conn
from .repo_products import get_active_products, get_product, upsert_products
from .analytics import log_visit
from .collect import router as collect_router
from .nudges import router as nudges_router
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY","")

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.on_event("startup")
def migrate():
    for path in sorted(glob.glob("migrations/*.sql")):
        with open(path,"r",encoding="utf-8") as f:
            sql = f.read()
        with db_conn() as c:
            c.execute(sql)

@app.get("/healthz")
def healthz():
    return {"ok": True, "time": datetime.datetime.utcnow().isoformat()+"Z"}

@app.get("/")
def home(request: Request):
    prods = get_active_products(["top10","complete"])
    log_visit(request, "home")
    return templates.TemplateResponse("home.html", {"request": request, "products": prods, "year": datetime.datetime.now().year})

@app.get("/promo/{promo_id}")
def promo_page(promo_id: str, request: Request):
    prod = get_product(promo_id)
    if not prod:
        log_visit(request, "promo_inactive", promo_id=promo_id)
        return RedirectResponse("/", status_code=302)
    log_visit(request, "promo", promo_id=promo_id)
    return templates.TemplateResponse("promo.html", {"request": request, "promo": prod, "year": datetime.datetime.now().year})

@app.post("/checkout/{product_id}")
def checkout_start(product_id: str, request: Request):
    prod = get_product(product_id)
    if not prod:
        log_visit(request, "promo_inactive", promo_id=product_id, product_id=product_id)
        raise HTTPException(status_code=410, detail="Offer not available")
    if not stripe.api_key:
        return {"url": f"/post-checkout/success?product={product_id}&session_id=dev"}
    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{"price": prod["price_id"], "quantity": 1}],
        success_url=f"{os.getenv('APP_BASE_URL','')}/post-checkout/success?product={product_id}&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{os.getenv('APP_BASE_URL','')}/post-checkout/cancel?product={product_id}"
    )
    log_visit(request, "checkout_start", promo_id=product_id, product_id=product_id, extra={"session_id": session.get("id")})
    return {"url": session.url}

@app.get("/post-checkout/success")
def success(product: str, session_id: str="dev", request: Request):
    log_visit(request, "checkout_success", promo_id=product, product_id=product, extra={"session_id": session_id})
    return templates.TemplateResponse("success.html", {"request": request, "product": product, "year": datetime.datetime.now().year})

@app.get("/post-checkout/cancel")
def cancel(product: str, request: Request):
    log_visit(request, "checkout_cancel", promo_id=product, product_id=product)
    return templates.TemplateResponse("cancel.html", {"request": request, "year": datetime.datetime.now().year})

@app.get("/connect-notion")
def connect_notion(request: Request, product: str):
    cid = os.getenv("NOTION_CLIENT_ID"); redir = os.getenv("NOTION_REDIRECT_URI")
    if not cid or not redir:
        url = "#"
    else:
        url = f"https://api.notion.com/v1/oauth/authorize?owner=user&client_id={cid}&redirect_uri={redir}&response_type=code&state={product}"
    return templates.TemplateResponse("connect.html", {"request": request, "notion_auth_url": url, "year": datetime.datetime.now().year})

@app.post("/confirm-roots")
def confirm_roots(request: Request, family_root_id: str=Form(...), executor_root_id: str=Form(...), product: str=Form(...)):
    return templates.TemplateResponse("done.html", {"request": request, "year": datetime.datetime.now().year})

def admin_auth(authorization: str = Header("")):
    if authorization != f"Bearer {os.environ.get('ADMIN_TOKEN','')}":
        raise HTTPException(401, "Unauthorized")

@app.post("/admin/sync-products")
def admin_sync_products(payload: list, _=Depends(admin_auth)):
    upsert_products(payload)
    return {"ok": True, "count": len(payload)}

app.include_router(collect_router)
app.include_router(nudges_router)
