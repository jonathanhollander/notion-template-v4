import os, io, stripe, time
from fastapi import FastAPI, Request, Form, Depends, HTTPException, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from .db import SessionLocal, init_db
from .models import User, QRCode
from .utils import short_code, make_qr_png, make_qr_svg

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-too")
SUCCESS_URL = os.getenv("SUCCESS_URL","/success")
CANCEL_URL = os.getenv("CANCEL_URL","/")
APP_BASE_URL = os.getenv("APP_BASE_URL","")

serializer = URLSafeTimedSerializer(SECRET_KEY)

app = FastAPI(title="QR Service Pro")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    init_db()

# ---------------- Authentication (magic link) ----------------
def send_magic_link(email: str):
    token = serializer.dumps(email)
    link = f"{APP_BASE_URL}/auth?token={token}" if APP_BASE_URL else f"/auth?token={token}"
    # In production: send email with this link. For demo we just return it.
    return link

def current_user(request: Request, db: Session) -> User | None:
    email = request.cookies.get("email")
    if not email:
        return None
    u = db.query(User).filter(User.email==email).first()
    return u

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def login(request: Request, email: str = Form(...), db: Session = Depends(get_db)):
    # create record if not exists
    user = db.query(User).filter(User.email==email).first()
    if not user:
        user = User(id=email, email=email, credits_remaining=0, trial_redeemed=False)
        db.add(user); db.commit()
    link = send_magic_link(email)
    # Show link on page for demo; replace with email later
    return templates.TemplateResponse("magiclink.html", {"request": request, "email": email, "link": link})

@app.get("/auth", response_class=HTMLResponse)
def auth(request: Request, token: str, db: Session = Depends(get_db)):
    try:
        email = serializer.loads(token, max_age=3600*24)
    except SignatureExpired:
        return HTMLResponse("<h3>Link expired. Please log in again.</h3>", status_code=400)
    except BadSignature:
        return HTMLResponse("<h3>Invalid link.</h3>", status_code=400)
    # set cookie
    resp = RedirectResponse(url="/dashboard", status_code=302)
    resp.set_cookie("email", email, max_age=60*60*24*7, httponly=True, samesite="Lax")
    return resp

@app.get("/logout")
def logout():
    resp = RedirectResponse(url="/", status_code=302)
    resp.delete_cookie("email")
    return resp

# ---------------- Dashboard ----------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse(url="/", status_code=302)
    qrs = db.query(QRCode).filter(QRCode.user_id==user.id).order_by(QRCode.created_at.desc()).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "qrs": qrs})

# ---------------- Stripe ----------------
@app.post("/create-checkout-session")
def create_checkout_session(request: Request, bundle: str = Form("qr10"), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: raise HTTPException(status_code=401, detail="Not logged in")
    if bundle == "trial20":
        if user.trial_redeemed:
            raise HTTPException(status_code=400, detail="Trial already redeemed")
        price = {"currency":"usd","unit_amount":100,"product_data":{"name":"QR Trial Pack (20 codes) $1"}}
        meta = {"credits":"20","bundle":"trial20","email":user.email}
    else:
        price = {"currency":"usd","unit_amount":999,"product_data":{"name":"QR Bundle (10 codes) $9.99"}}
        meta = {"credits":"10","bundle":"qr10","email":user.email}
    session = stripe.checkout.Session.create(
        mode="payment",
        customer_email=user.email,
        line_items=[{"price_data":price,"quantity":1}],
        success_url=SUCCESS_URL,
        cancel_url=CANCEL_URL,
        metadata=meta
    )
    return {"url": session.url}

@app.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]
        email = s.get("metadata", {}).get("email") or s.get("customer_details", {}).get("email") or s.get("customer_email")
        credits = int(s.get("metadata", {}).get("credits","0"))
        bundle = s.get("metadata", {}).get("bundle")
        if email and credits:
            user = db.query(User).filter(User.email==email).first()
            if not user:
                user = User(id=email, email=email, credits_remaining=0, trial_redeemed=False)
                db.add(user); db.commit()
            if bundle == "trial20":
                if not user.trial_redeemed:
                    user.trial_redeemed = True
                    user.credits_remaining = (user.credits_remaining or 0) + credits
            else:
                user.credits_remaining = (user.credits_remaining or 0) + credits
            db.add(user); db.commit()
    return {"received": True}

@app.get("/success", response_class=HTMLResponse)
def success(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("success.html", {"request": request, "user": user})

# ---------------- Create QR ----------------
@app.post("/qr/new")
def qr_new(request: Request, label: str = Form(...), target_url: str = Form(...), style: str = Form("plain"), caption: str = Form(""), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: raise HTTPException(status_code=401, detail="Not logged in")
    if user.credits_remaining <= 0:
        raise HTTPException(status_code=402, detail="No credits remaining. Please purchase a bundle.")
    code = short_code(7)
    # Build redirect URL
    base = APP_BASE_URL.rstrip("/") if APP_BASE_URL else str(request.base_url).rstrip("/")
    short_url = f"{base}/r/{code}"
    # Generate images
    png = make_qr_png(short_url, style=style, caption=(caption if style=="caption" else None))
    svg = make_qr_svg(short_url)
    # store files
    png_path = f"app/static/qr_{code}.png"
    with open(png_path, "wb") as f: f.write(png)
    svg_path = f"app/static/qr_{code}.svg"
    with open(svg_path, "wb") as f: f.write(svg)
    qr = QRCode(id=code, user_id=user.id, label=label, target_url=target_url, image_path_png=png_path, image_path_svg=svg_path, style=style)
    user.credits_remaining -= 1
    db.add(qr); db.add(user); db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

# ---------------- Redirect + scan tracking ----------------
@app.get("/r/{code}")
def redirector(code: str, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == code).first()
    if not qr:
        raise HTTPException(status_code=404, detail="Not found")
    qr.scan_count += 1
    db.add(qr); db.commit()
    return RedirectResponse(url=qr.target_url, status_code=302)

# ---------------- Assets & print sheet ----------------
@app.get("/qr/{code}.png")
def qr_png(code: str, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == code).first()
    if not qr: raise HTTPException(status_code=404, detail="Not found")
    with open(qr.image_path_png, "rb") as f:
        data = f.read()
    return StreamingResponse(io.BytesIO(data), media_type="image/png")

@app.get("/qr/{code}.svg")
def qr_svg(code: str, db: Session = Depends(get_db)):
    qr = db.query(QRCode).filter(QRCode.id == code).first()
    if not qr: raise HTTPException(status_code=404, detail="Not found")
    with open(qr.image_path_svg, "rb") as f:
        data = f.read()
    return StreamingResponse(io.BytesIO(data), media_type="image/svg+xml")

@app.get("/print-sheet.pdf")
def print_sheet(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user: return RedirectResponse(url="/", status_code=302)
    qrs = db.query(QRCode).filter(QRCode.user_id==user.id).order_by(QRCode.created_at.desc()).limit(12).all()
    # Create PDF grid 3x4
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    margin = 0.5*inch
    cols, rows = 3, 4
    cell_w = (width - 2*margin) / cols
    cell_h = (height - 2*margin) / rows
    x = margin
    y = height - margin - cell_h
    i = 0
    for qr in qrs:
        # draw label
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x+6, y+cell_h-14, qr.label)
        # draw image
        c.drawImage(f"/{qr.image_path_png}", x+10, y+30, cell_w-20, cell_h-50, preserveAspectRatio=True, mask='auto')
        # draw short url text
        c.setFont("Helvetica", 8)
        c.drawString(x+6, y+18, f"/r/{qr.id}")
        # advance grid
        i += 1
        x += cell_w
        if i % cols == 0:
            x = margin
            y -= cell_h
            if i % (cols*rows) == 0:
                c.showPage(); y = height - margin - cell_h
    c.showPage(); c.save()
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="qr_print_sheet.pdf"'})
