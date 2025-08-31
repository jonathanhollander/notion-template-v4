import os, io, secrets, string, qrcode
from qrcode.image.svg import SvgImage
from PIL import Image, ImageDraw, ImageFont

def short_code(n=7):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))

def make_qr_png(data: str, style: str = "plain", caption: str = None, box_size=10, border=4) -> bytes:
    qr = qrcode.QRCode(box_size=box_size, border=border, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    if style in ("border","caption"):
        # add padding/border
        pad = 20
        new_size = (img.size[0] + pad*2, img.size[1] + pad*2 + (40 if style == "caption" and caption else 0))
        out = Image.new("RGB", new_size, "white")
        draw = ImageDraw.Draw(out)
        # border rectangle
        draw.rectangle([5,5,new_size[0]-6,new_size[1]-6-(40 if style=="caption" and caption else 0)], outline=(80,90,100), width=2)
        out.paste(img, (pad, pad))
        if style == "caption" and caption:
            # simple caption
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 16)
            except:
                font = ImageFont.load_default()
            draw.text((pad, new_size[1]-30), caption, fill=(47,72,88), font=font)
        img = out

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def make_qr_svg(data: str) -> bytes:
    img = qrcode.make(data, image_factory=SvgImage)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue()
