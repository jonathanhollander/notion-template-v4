from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)  # use email as id for simplicity
    email = Column(String, unique=True, index=True, nullable=False)
    stripe_customer_id = Column(String, nullable=True)
    credits_remaining = Column(Integer, default=0)
    trial_redeemed = Column(Boolean, default=False)

class QRCode(Base):
    __tablename__ = "qr_codes"
    id = Column(String, primary_key=True)   # short code
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=False)
    label = Column(String, nullable=False)
    target_url = Column(Text, nullable=False)
    image_path_png = Column(String, nullable=False)
    image_path_svg = Column(String, nullable=True)
    style = Column(String, nullable=False, default="plain")  # plain|border|caption
    created_at = Column(DateTime, server_default=func.now())
    scan_count = Column(Integer, default=0)
