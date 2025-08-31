import io, qrcode
from PIL import Image

def make_qr_png(url: str, box_size=10, border=4) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=border)
    qr.add_data(url); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()
