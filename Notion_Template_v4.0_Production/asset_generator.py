#!/usr/bin/env python3
"""
Asset Generator for Notion Estate Planning Concierge v4.0
"""

import os
import re
from PIL import Image, ImageDraw

def get_color_for_asset(asset_name, theme):
    if theme == "dark":
        if "preparation" in asset_name:
            return "#a8d8ff"  # Light Blue
        elif "executor" in asset_name:
            return "#d8bfff"  # Light Purple
        elif "family" in asset_name:
            return "#afffe9"  # Light Green
        else:
            return "#ffffff" # White
    elif theme == "light":
        if "preparation" in asset_name:
            return "#e0f7fa"  # Lighter Blue
        elif "executor" in asset_name:
            return "#ede7f6"  # Lighter Purple
        elif "family" in asset_name:
            return "#e0f2f1"  # Lighter Green
        else:
            return "#f5f5f5" # Lighter Grey
    elif theme == "blue":
        return "#a8d8ff" # Light Blue
    elif theme == "green":
        return "#afffe9" # Light Green
    elif theme == "purple":
        return "#d8bfff" # Light Purple
    else:
        if "preparation" in asset_name:
            return "#4a90e2"  # Blue
        elif "executor" in asset_name:
            return "#7b68ee"  # Purple
        elif "family" in asset_name:
            return "#50e3c2"  # Green
        elif "legal" in asset_name:
            return "#d0021b"  # Red
        elif "financial" in asset_name:
            return "#f5a623"  # Orange
        elif "property" in asset_name:
            return "#bd10e0"  # Pink
        elif "insurance" in asset_name:
            return "#9013fe"  # Purple
        elif "subscriptions" in asset_name:
            return "#417505"  # Green
        elif "letters" in asset_name:
            return "#f8e71c"  # Yellow
        elif "memories" in asset_name:
            return "#e99578"  # Peach
        elif "contacts" in asset_name:
            return "#b8e986"  # Light Green
        elif "qr-codes" in asset_name:
            return "#000000"  # Black
        else:
            return "#cccccc"  # Grey

def generate_icon(asset_name: str, output_dir: str, theme: str):
    """Generate an icon asset."""
    # Create a simple icon with a solid color and a simple shape
    img = Image.new('RGB', (100, 100), color = get_color_for_asset(asset_name, theme))
    d = ImageDraw.Draw(img)
    #d.text((10,10), asset_name, fill=(255,255,0))
    output_path = os.path.join(output_dir, asset_name.replace(".svg", ".png"))
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    img.save(output_path)

def generate_cover(asset_name: str, output_dir: str, theme: str):
    """Generate a cover asset."""
    # Create a simple cover with a solid color
    img = Image.new('RGB', (1500, 600), color = get_color_for_asset(asset_name, theme))
    d = ImageDraw.Draw(img)
    #d.text((10,10), asset_name, fill=(255,255,0))
    output_path = os.path.join(output_dir, asset_name.replace(".svg", ".png"))
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    img.save(output_path)

def generate_assets_for_theme(theme: str):
    """Generate all the assets for a given theme."""
    # Create the assets directory if it doesn't exist
    if not os.path.exists(f"assets/icons_{theme}"):
        os.makedirs(f"assets/icons_{theme}")
    if not os.path.exists(f"assets/covers_{theme}"):
        os.makedirs(f"assets/covers_{theme}")

    # Generate all the icons
    pages = [
        "Admin – Release Notes",
        "Admin – Rollout Cockpit",
        "Admin – Diagnostics",
        "Admin – Final UI Checklist",
        "Admin Hub",
        "Preparation Hub",
        "Executor Hub",
        "Family Hub",
        "Legal Documents",
        "Financial Accounts",
        "Property & Assets",
        "Insurance",
        "Subscriptions",
        "Letters",
        "Memories & Keepsakes",
        "Contacts",
        "QR Codes",
        "Living Will – Sample Document",
        "Power of Attorney – Sample",
        "Advance Directive – Sample",
        "Trust – Sample Outline",
        "Executor Checklist",
        "Bank & Account Access Notes",
        "Funeral & Memorial Preferences",
        "Messages for Family",
        "Keepsakes Index",
        "Primary Bank Accounts",
        "Credit Cards",
        "Brokerage & Retirement",
        "Real Estate",
        "Vehicles",
        "Digital Assets",
        "Life Insurance",
        "Homeowners/Renters",
        "Health Insurance",
        "Streaming Services",
        "Utilities",
        "Online Services",
        "QR – Family Essentials",
        "QR – Full Access for Executor",
        "Executor Task 01",
        "Executor Task 02",
        "Executor Task 03",
        "Executor Task 04",
        "Executor Task 05",
        "Executor Task 06",
        "Executor Task 07",
        "Executor Task 08",
        "Executor Task 09",
        "Executor Task 10",
        "Executor Task 11",
        "Executor Task 12",
        "Executor Task 13",
        "Executor Task 14",
        "Executor Task 15",
        "Executor Task 16",
        "Executor Task 17",
        "Executor Task 18",
        "Executor Task 19",
        "Executor Task 20",
        "Executor Task 21",
        "Executor Task 22",
        "Executor Task 23",
        "Executor Task 24",
        "Executor Task 25",
        "Executor Task 26",
        "Executor Task 27",
        "Executor Task 28",
        "Executor Task 29",
        "Executor Task 30",
        "Executor Task 31",
        "Executor Task 32",
        "Executor Task 33",
        "Executor Task 34",
        "Executor Task 35",
        "Executor Task 36",
        "Executor Task 37",
        "Executor Task 38",
        "Executor Task 39",
        "Executor Task 40",
        "Executor Guide – SSA Notification",
        "Executor Guide – IRS Final Return Notes",
        "Executor Guide – DMV Title Transfer",
        "Executor Guide – USPS Mail Forwarding",
        "Executor Guide – Mortgage Servicer",
        "Executor Guide – Landlord/HOA",
        "Executor Guide – Pension/401(k) Administrator",
        "Executor Guide – Brokerage Transfer",
        "Executor Guide – Credit Bureaus (Equifax/Experian/TransUnion)",
        "Digital Assets – Passwords & Access Hints",
        "Digital Assets – Email Accounts",
        "Digital Assets – Cloud Storage",
        "Digital Assets – Photo Archives",
        "Digital Assets – Domain Names",
        "Digital Assets – Crypto Wallets",
        "Letters of Sympathy (Optional)",
        "Memorial Playlist",
        "Photo Collage Plan",
        "Memorial Guestbook",
        "Letter – Credit Card Company (Notification of Death)",
        "Letter – Bank (Account Transition/Closure)",
        "Letter – Utility Provider (Service Change/Closure)",
        "Admin – Assets & Icons",
        "Preparation Hub – Beginner Tips",
        "Preparation Hub – Advanced Tools",
        "Letters – Library (Pages)",
        "Admin – Guided Helpers",
        "Admin – Visual Assets",
        "Digital Legacy Management",
        "Google Inactive Account Manager",
        "Apple Legacy Contact",
        "Facebook Memorialization",
        "Instagram Memorial",
        "LinkedIn Legacy Settings",
        "Password Manager Legacy Access",
        "Cryptocurrency Wallet Access",
        "Domain and Hosting Management",
        "Help Center",
        "Contextual Help System",
        "FAQ Center",
        "Troubleshooting Guide",
        "Video Learning Center",
        "Best Practices Guide",
        "Progress Dashboard",
        "Analytics Hub",
        "Visual Progress Center",
        "Language Configuration Center",
        "Translation Management System",
        "Language Switcher Interface",
        "RTL Support Framework",
        "Translation Quality Center",
        "Language Switcher Control Panel",
        "Executive Analytics Dashboard",
        "Task Velocity Tracker",
        "Bottleneck Detection Center",
        "Trend Analysis Hub",
        "Export & Reporting Center",
        "Analytics Command Center",
        "Automation Control Center",
        "Smart Reminder System",
        "Workflow Automation Hub",
        "Smart Alert Configuration",
        "Progress Alert System",
        "Performance Dashboard",
        "System Resource Monitor",
        "Load Optimization Center",
        "Performance Analytics",
        "Cache Management System",
        "Gold Release Dashboard",
        "System Validation Center",
        "Compliance Audit Center",
        "Quality Assurance Dashboard",
        "User Manual Hub",
        "Administrator Guide",
        "API Documentation Center",
        "Video Production Scripts",
        "Builder’s Console"
    ]

    for page in pages:
        # Sanitize the page title to create a valid filename
        asset_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', page).lower()
        generate_icon(f"{asset_name}_icon.png", f"assets/icons_{theme}", theme)
        generate_cover(f"{asset_name}_cover.png", f"assets/covers_{theme}", theme)

if __name__ == "__main__":
    generate_assets_for_theme("default")
    generate_assets_for_theme("dark")
    generate_assets_for_theme("light")
    generate_assets_for_theme("blue")
    generate_assets_for_theme("green")
    generate_assets_for_theme("purple")
