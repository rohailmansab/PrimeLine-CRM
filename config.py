import os
from dotenv import load_dotenv

load_dotenv()

def validate_api_key(key: str) -> bool:
    if not key:
        return False
    return key.startswith("AI") and len(key) > 20

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not validate_api_key(GEMINI_API_KEY):
    print("Warning: Invalid or missing Gemini API key")
    GEMINI_API_KEY = None

GMAIL_CREDENTIALS_PATH = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
DATABASE_PATH = "data/crm.db"

EMAIL_TEMPLATES = {
    "price_request": """Dear {supplier_name},

We hope this email finds you well. We are updating our pricing database and would appreciate your latest pricing information for the following products:

{product_list}

Please provide current prices per square foot and any volume discounts available.

Best regards,
PrimeLine Flooring Team""",
    
    "quote": """Dear {customer_name},

Thank you for your interest in our flooring products. Based on your requirements:

Location: {location}
Product: {product}
Quantity: {quantity} sq ft

We are pleased to offer:

Price per sq ft: ${price_per_sqft}
Total Amount: ${total_amount}

This quote is valid for 30 days.

Best regards,
PrimeLine Flooring Team"""
}

THEME = {
    "primaryColor": "#FF4B4B",
    "backgroundColor": "#FFFFFF",
    "secondaryBackgroundColor": "#F0F2F6",
    "textColor": "#262730",
    "font": "sans serif"
}

PRODUCT_CATEGORIES = [
    "Hardwood – Solid",
    "Hardwood – Engineered",
    "Hardwood – Reclaimed",
    "LVP Flooring"
]

SAMPLE_PRODUCTS = [
    {"name": "White Oak", "widths": ["5\"", "7\""], "base_price": 4.25, "category": "Hardwood – Solid"},
    {"name": "Red Oak", "widths": ["5\"", "7\""], "base_price": 3.85, "category": "Hardwood – Solid"},
    {"name": "Maple", "widths": ["4\"", "6\""], "base_price": 4.50, "category": "Hardwood – Engineered"},
    {"name": "Walnut", "widths": ["5\"", "7\""], "base_price": 5.95, "category": "Hardwood – Solid"},
    {"name": "Bamboo", "widths": ["5\""], "base_price": 3.95, "category": "Hardwood – Engineered"},
    {"name": "Cork", "widths": ["6\""], "base_price": 3.85, "category": "Hardwood – Engineered"},
    {"name": "Hickory", "widths": ["5\"", "7\""], "base_price": 4.75, "category": "Hardwood – Solid"},
    {"name": "E-Thermawood", "widths": ["5\"", "6\""], "base_price": 5.25, "category": "Hardwood – Engineered"}
]

SAMPLE_SUPPLIERS = [
    {"name": "Premium Hardwoods", "email": "sales@premiumhardwoods.com"},
    {"name": "EcoFloor Solutions", "email": "info@ecofloorsolutions.com"},
    {"name": "Classic Woods Inc", "email": "orders@classicwoods.com"}
]

UI_CONFIG = {
    "sidebar_width": 280,
    "content_padding": 20,
    "border_radius": 12,
    "shadow": "0 4px 12px rgba(0,0,0,0.1)"
}

SCHEDULER_CONFIG = {
    "weekly_update_day": "monday",
    "weekly_update_time": "09:00",  # UTC
    "daily_check_time": "14:00",    # UTC
    "timezone": "UTC"
}

SUPPORTED_WIDTHS = ["2.5\"", "3.5\"", "4\"", "5\"", "6\"", "7\"", "8\"", "10\"", "11\"", "12\"", "13\"", "14\"", "Custom"]