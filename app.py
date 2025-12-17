# import streamlit as st
# from email_handler import send_price_request, read_reply_and_save
# from quote_generator import generate_quote
# from database import init_db
# import pandas as pd
# import sqlite3

# init_db()

# st.title("Flooring AI Demo")
# tab1, tab2, tab3 = st.tabs(["Update Prices", "Generate Quote", "Leads"])

# # === Function 1 ===
# with tab1:
#     if st.button("Send Price Request Email"):
#         send_price_request()
#         st.success("Email sent to supplier!")

#     if st.button("Check Reply & Save Price"):
#         read_reply_and_save()

# # === Function 2 ===
# with tab2:
#     with st.form("quote_form"):
#         city = st.text_input("City", "Raleigh, NC")
#         product = st.text_input("Product", "White Oak")
#         width = st.text_input("Width", "5\"")
#         sqft = st.number_input("Square Feet", 100, 10000, 5000)
#         submitted = st.form_submit_button("Generate Quote")

#         if submitted:
#             quote = generate_quote(city, product, width, sqft)
#             st.success(f"Quote: ${quote['total']} (${quote['selling_price']}/sqft)")

# # === Function 3 ===
# with tab3:
#     st.write("Demo Leads (Manual + AI Summary)")
#     leads = [
#         {"Name": "John", "City": "Raleigh", "Need": "5\" oak, 3000 sqft", "Source": "FB Group"},
#         {"Name": "Sarah", "City": "Cary", "Need": "Refinish old floors", "Source": "Reddit"}
#     ]
#     st.dataframe(leads)



# app.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import time
import os
from typing import Dict, Any
import google.auth.exceptions

# Local imports
from database import Database
from gemini_client import GeminiClient
from email_handler import EmailHandler
from auth_ui import render_authentication_gate
from customer_ui import render_customer_page
from config import (
    GEMINI_API_KEY, DATABASE_PATH, EMAIL_TEMPLATES,
    THEME, SAMPLE_PRODUCTS, SAMPLE_SUPPLIERS
)

# ===================== UI SETUP =====================
st.set_page_config(
    page_title="Flooring AI Sales System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== INITIALIZATION =====================
if not os.path.exists('data'):
    os.makedirs('data')

db = Database(DATABASE_PATH)

# Initialize SQLAlchemy tables (for customers, etc.)
try:
    from models.base import Base, engine
    Base.metadata.create_all(bind=engine)
    print("✓ SQLAlchemy tables initialized")
except Exception as e:
    print(f"SQLAlchemy table initialization warning: {e}")

# ==================== AUTHENTICATION GATE ====================
# This must be checked FIRST, before any other UI is rendered
if not render_authentication_gate(db):
    st.stop()  # Block access if not authenticated

# Clean up expired sessions periodically
db.cleanup_expired_sessions()

try:
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]
    
    if product_count == 0:
        db.populate_sample_data()
        st.toast("💫 Sample data loaded for demo!")
    conn.close()
except Exception as e:
    st.error(f"Database initialization error: {str(e)}")

try:
    if not GEMINI_API_KEY:
        gemini = None
    else:
        gemini = GeminiClient(GEMINI_API_KEY)
except Exception as e:
    st.error(f"❌ Error initializing AI services: {str(e)}")
    gemini = None

try:
    email_handler = EmailHandler(db)
except RuntimeError as e:
    # Headless environment - user needs to set up token.json
    error_msg = str(e)
    if "Gmail authentication failed" in error_msg or "No existing Gmail credentials" in error_msg:
        # SILENT FAILURE - Log to console only to keep UI clean
        print(f"Gmail Auth Warning: {error_msg}")
        email_handler = None
        st.session_state.gmail_status = "not_configured"
    else:
        st.error(f"Error initializing EmailHandler: {error_msg}")
        email_handler = None
except Exception as e:
    # If authentication failed due to expired/revoked token, surface clear UI guidance
    if isinstance(e, google.auth.exceptions.RefreshError) or 'expired' in str(e).lower() or 'revoked' in str(e).lower():
        st.error("Gmail authentication failed: token expired or revoked. Please re-authenticate.")
        st.info("To re-authenticate: delete 'token.json' in the project folder and reload the app. A browser window will open to complete OAuth.")
    else:
        st.error(f"Error initializing EmailHandler: {str(e)}")
    email_handler = None
    st.session_state.gmail_status = "error"

# Default status if not set above
if 'gmail_status' not in st.session_state:
    if email_handler:
        st.session_state.gmail_status = "connected"
    else:
        st.session_state.gmail_status = "error"

# Initialize Scheduler
try:
    from scheduler_service import SchedulerService
    if email_handler and db:
        scheduler = SchedulerService(db, email_handler, gemini)
        scheduler.start_scheduler()
except Exception as e:
    print(f"Scheduler initialization error: {e}")

# Custom CSS for theme compatibility
st.markdown("""
<style>
    /* Theme-aware Sidebar Styling */
    .css-1d391kg, .css-1v3fvcr {
        padding-top: 0 !important;
    }
    
    [data-testid="stSidebar"] {
        background-image: linear-gradient(to bottom, var(--sidebar-gradient1), var(--sidebar-gradient2));
    }
    
    /* Logo and Title Styling */
    .sidebar-logo img {
        filter: var(--logo-filter);
    }
    .app-title {
        color: var(--text-color);
        font-size: 26px;
        font-weight: 600;
        margin: 0;
    }
    .app-subtitle {
        color: var(--subtitle-color);
        font-size: 14px;
        margin: 5px 0 0 0;
        opacity: 0.8;
    }
    
    /* Button Styling */
    .stButton>button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        margin-bottom: 0.5rem;
        border-radius: 10px;
        border: 2px solid transparent;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        font-size: 15px;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    .stButton>button:active {
        transform: translateY(0);
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4);
    }
    
    /* Primary Buttons */
    button[kind="primary"], .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        color: white !important;
        border: none !important;
    }
    button[kind="primary"]:hover, .stButton button[kind="primary"]:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
        transform: translateY(-2px);
    }
    
    /* Secondary Buttons */
    button[kind="secondary"], .stButton button[kind="secondary"] {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
        box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4) !important;
        color: white !important;
        border: none !important;
    }
    button[kind="secondary"]:hover, .stButton button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #f5576c 0%, #f093fb 100%) !important;
        box-shadow: 0 6px 20px rgba(245, 87, 108, 0.6) !important;
        transform: translateY(-2px);
    }
    
    /* Metrics and Stats */
    .css-1xarl3l, .css-1p05t8e {
        background-color: var(--metric-bg);
        border: 1px solid var(--metric-border);
        padding: 10px;
        border-radius: 8px;
    }
    
    /* DataFrames */
    .stDataFrame {
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
        background-color: var(--dataframe-bg);
    }
    
    :root[data-theme="light"] {
        --sidebar-gradient1: #f5f7fa;
        --sidebar-gradient2: #e4e9f2;
        --text-color: #2C3E50;
        --subtitle-color: #666666;
        --primary-color: #4A90E2;
        --button-bg: #ffffff;
        --hover-text: #ffffff;
        --metric-bg: #ffffff;
        --metric-border: #e1e4e8;
        --dataframe-bg: #ffffff;
        --logo-filter: drop-shadow(0px 4px 8px rgba(0, 0, 0, 0.1));
    }
    
    :root[data-theme="dark"] {
        --sidebar-gradient1: #1E1E1E;
        --sidebar-gradient2: #2D2D2D;
        --text-color: #E1E1E1;
        --subtitle-color: #B8B8B8;
        --primary-color: #4A90E2;
        --button-bg: #363636;
        --hover-text: #ffffff;
        --metric-bg: #2D2D2D;
        --metric-border: #404040;
        --dataframe-bg: #2D2D2D;
        --logo-filter: drop-shadow(0px 4px 8px rgba(255, 255, 255, 0.1)) brightness(0.9);
    }
</style>
""", unsafe_allow_html=True)

# ===================== SESSION STATE =====================
if 'active_suppliers' not in st.session_state:
    st.session_state.active_suppliers = []
if 'price_requests' not in st.session_state:
    st.session_state.price_requests = []
if 'db_refresh_key' not in st.session_state:
    st.session_state.db_refresh_key = 0

# ===================== HELPER FUNCTIONS =====================

def require_admin() -> bool:
    """Check if current user has admin access"""
    is_admin = st.session_state.get('is_admin', False)
    if not is_admin:
        st.error("🔒 Access Denied")
        st.warning("This feature is restricted to administrators only.")
        st.info("Please contact your system administrator if you need access to this feature.")
        return False
    return True

def format_currency(value: float) -> str:
    return f"${value:,.2f}"

def clear_database_cache():
    st.session_state.db_refresh_key += 1
    st.cache_data.clear()
    st.cache_resource.clear()

def get_market_data(location: str, product: Dict[str, Any]) -> Dict[str, Any]:
    """Get market analysis with fallback handling"""
    
    def get_default_analysis():
        base_price = product.get("base_price", 4.0)
        return {
            "recommended_price_range": {
                "low": round(base_price * 1.2, 2),
                "high": round(base_price * 1.6, 2),
                "optimal": round(base_price * 1.3, 2)
            },
            "market_factors": ["Using standard industry margins"],
            "competitor_analysis": {
                "average_market_price": round(base_price * 1.4, 2),
                "price_positioning": "mid-range"
            },
            "seasonal_adjustment": 0,
            "demand_indicator": "medium"
        }
    
    try:
        if not gemini or not gemini.initialized:
            return get_default_analysis()
            
        analysis = gemini.generate_market_analysis(
            location,
            {"name": product["name"], "cost": product.get("base_price", 4.0), "specs": product}
        )
        if not analysis:
            raise Exception("Empty analysis received")
        return analysis
    except Exception as e:
        return get_default_analysis()

# ===================== EMAIL =====================
# ===================== SIDEBAR =====================
def render_sidebar():
    with st.sidebar:
        # Theme-aware Logo and Branding
        st.markdown('''
            <div style="text-align: center; padding: 20px 10px; margin-bottom: 20px;">
                <div class="sidebar-logo">
                    <img src="https://cdn-icons-png.flaticon.com/512/8886/8886581.png" 
                         width="80">
                </div>
                <div style="margin-top: 15px;">
                    <h1 class="app-title">PrimeLine Flooring</h1>
                    <p class="app-subtitle">Smart Flooring Solutions through Artificial Intelligence</p>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        

        
        st.divider()
        
        # Navigation Menu
        # Show admin badge if user is admin
        is_admin = st.session_state.get('is_admin', False)
        if is_admin:
            st.info("👑 Admin Access")
        
        # Conditional navigation based on admin status
        # Conditional navigation based on admin status
        role = st.session_state.get('role', 'user')
        
        if role in ['super_admin', 'admin']:
             # Admins see Admin Dashboard + other tools
            selected = st.radio(
                "Go to",
                ["🛡️ Admin Dashboard", "📧 Supplier Management", "💰 Quote Generator", "📊 Analytics", "👥 Customers", "📜 Customer History"]
            )
        else:
            # Regular users don't see Admin Dashboard or Supplier Management
            selected = st.radio(
                "Go to",
                ["💰 Quote Generator", "👥 Customers", "📜 Customer History", "📊 Analytics"]
            )
            
        st.divider()
        
        # ==================== USER PROFILE SECTION ====================
        st.markdown("### 👤 User Profile")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{st.session_state.full_name}**")
            st.caption(st.session_state.email)
            if st.session_state.remember_me:
                st.caption("✅ Remember me active (30 days)")
            else:
                st.caption("⏱️ Session expires in 45 mins")
        
        with col2:
            st.write("")  # Spacer
        
        # Sign Out Button
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            try:
                db.invalidate_session(st.session_state.session_token)
                st.session_state.authenticated = False
                st.session_state.session_token = None
                st.session_state.user_id = None
                st.session_state.username = None
                st.session_state.email = None
                st.session_state.full_name = None
                st.session_state.remember_me = False
                st.success("✅ You have been signed out successfully")
                st.toast("Signed out", icon="👋")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error during sign out: {str(e)}")
        
        st.divider()
        
        # Sidebar Status
        st.subheader("System Status")
        
        # Assuming gmail_status, db, and gemini are available in the scope where render_sidebar is called
        # or passed as arguments. For this edit, we'll assume they are accessible.
        if 'gmail_status' in st.session_state: # Added a check for gmail_status existence
            if st.session_state.gmail_status == "connected":
                st.success("Gmail: Connected")
            elif st.session_state.gmail_status == "not_configured":
                st.info("Gmail: Offline (No Secrets)")
            else:
                st.error("Gmail: Authentication Error")
        else:
            st.warning("Gmail: Status Unknown") # Fallback if gmail_status is not set
        
        if 'db' in globals() and db: # Check if db is defined and not None
            st.success("Database: Connected")
        else:
            st.error("Database: Disconnected")
        
        if 'gemini' in globals() and gemini: # Check if gemini is defined and not None
            st.success("AI Engine: Online")
        else:
            st.warning("AI Engine: Offline")
            
        # Automated Sync Status
        st.subheader("Auto-Sync Status")
        try:
            last_update = db.get_last_sync("weekly_update")
            last_check = db.get_last_sync("daily_check")
            
            if last_update:
                t = datetime.fromisoformat(last_update['timestamp'])
                st.caption(f"Last Request: {t.strftime('%a %H:%M')}")
            else:
                st.caption("Last Request: Never")
                
            if last_check:
                t = datetime.fromisoformat(last_check['timestamp'])
                st.caption(f"Last Check: {t.strftime('%a %H:%M')}")
            else:
                st.caption("Last Check: Never")
                
            # Manual Trigger for Admins
            if st.session_state.get('is_admin', False):
                if st.button("🔄 Force Sync Now", type="secondary", use_container_width=True):
                    with st.spinner("Running sync..."):
                        try:
                            from scheduler_service import SchedulerService
                            if 'scheduler' not in globals():
                                scheduler = SchedulerService(db, email_handler, gemini)
                            
                            # Run both tasks
                            scheduler.daily_reply_check()
                            # We don't force weekly update as it sends emails to everyone
                            
                            st.toast("Sync completed!", icon="✅")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Sync failed: {e}")
                            
        except Exception as e:
            st.caption("Sync Status: Unavailable")
            
        # Quick Stats
        st.subheader("Quick Stats")
        col1, col2 = st.columns(2)
        
        # Fetch real stats with caching
        @st.cache_data(ttl=300)
        def get_sidebar_stats(refresh_key):
            try:
                active_suppliers = db.get_active_suppliers_count()
                pending_requests = db.get_pending_requests_count()
                return active_suppliers, pending_requests
            except:
                return 0, 0
        
        # Use session state key to force refresh when needed
        active_count, pending_count = get_sidebar_stats(st.session_state.get('db_refresh_key', 0))
        
        with col1:
            st.metric("Active Suppliers", active_count)
        with col2:
            st.metric("Pending Quotes", pending_count)
            
        return selected

# ===================== SUPPLIER MANAGEMENT =====================
# Logic moved to supplier_ui.py


# ===================== QUOTE GENERATOR =====================
def render_quote_page():
    st.header("💰 Quote Generator")
    
    # Error handling for database connection
    try:
        products = db.get_products()
        if not products:
            st.error("No products found in database. Please check the database connection.")
            return
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Generate New Quote")
        
        # Initialize session state for form fields
        if 'selected_product' not in st.session_state:
            st.session_state.selected_product = sorted(set(p["name"] for p in products))[0]
        if 'selected_width' not in st.session_state:
            st.session_state.selected_width = None
        
        # Product selector
        product_names = sorted(set(p["name"] for p in products))
        product = st.selectbox(
            "Product",
            options=product_names,
            key="product_select",
            on_change=lambda: st.session_state.update({"selected_width": None})
        )
        
        # Get widths for selected product from database
        product_widths = sorted(set(p["width"] for p in products if p["name"] == product))
        
        if not product_widths:
            st.error(f"No widths found for {product}")
            return
        
        # Width selector - always updated based on selected product
        width = st.selectbox(
            "Width",
            options=product_widths,
            key="width_select"
        )
        
        # Customer Selection
        from repositories.customer_repository import CustomerRepository
        from models.base import SessionLocal
        
        # Use a new session for the repository
        session = SessionLocal()
        try:
            customer_repo = CustomerRepository(session)
            # Filter customers by user
            user_id = st.session_state.get('user_id')
            is_admin = db.is_user_admin(user_id) if user_id else False
            customers, _ = customer_repo.list_customers(
                limit=1000,
                user_id=str(user_id) if user_id else None,
                is_admin=is_admin
            )
        finally:
            session.close()
        
        customer_options = {f"{c.full_name} ({c.email})": c for c in customers}
        selected_customer_key = st.selectbox(
            "Select Customer",
            options=["New Customer"] + list(customer_options.keys()),
            key="customer_select"
        )
        
        default_name = ""
        default_location = "Raleigh, NC"
        
        if selected_customer_key != "New Customer":
            selected_customer = customer_options[selected_customer_key]
            default_name = selected_customer.full_name
            if selected_customer.location:
                default_location = selected_customer.location
        
        with st.form("quote_form"):
            customer_name = st.text_input("Customer Name", value=default_name, placeholder="Enter customer name")
            location = st.text_input("Location", value=default_location)
            quantity = st.number_input("Square Feet", 100, 10000, 1000)
            
            use_ai_reference = True
            is_admin = st.session_state.get('role') in ['admin', 'super_admin']
            if is_admin:
                use_ai_reference = st.checkbox("Use AI Suggested Price as Reference Only", value=True, help="If checked, quote will use Standard Price (Base + 30%). AI price will be shown for info only.")
            
            submitted = st.form_submit_button("Submit for Approval", type="primary", use_container_width=True)
    
    if submitted:
        if not customer_name or not customer_name.strip():
            st.error("⚠️ Customer name is required to generate a quote")
        else:
            with st.spinner("Processing quote request..."):
                try:
                    matching_product = next(
                        (p for p in products if p['name'] == product and p['width'] == width),
                        None
                    )
                    
                    if not matching_product:
                        st.error(f"Product {product} {width} not found in database")
                        return
                    
                    # Get actual pricing from database
                    standard_price = matching_product.get('standard_price', 0)
                    cost_price = matching_product.get('cost_price', 0)
                    discount_pct = matching_product.get('discount_percentage', 0)
                    promo_name = matching_product.get('promotion_name')
                    start_date = matching_product.get('promotion_start_date')
                    end_date = matching_product.get('promotion_end_date')
                    
                    # Determine if promotion is active and calculate effective price
                    promo_active = False
                    if discount_pct and discount_pct > 0 and start_date and end_date:
                        promo_active = db.is_promotion_active(start_date, end_date)
                    
                    # Calculate base price for quote - use standard price, apply discount if active
                    if promo_active:
                        base_price = standard_price * (1 - discount_pct / 100)
                    else:
                        base_price = standard_price if standard_price > 0 else cost_price
                    
                    if base_price <= 0:
                        st.error(f"Invalid price data for {product} {width}")
                        return
                    
                    product_with_price = {
                        "name": product,
                        "width": width,
                        "base_price": base_price
                    }
                    market_data = get_market_data(location, product_with_price)
                    
                    # Try Gemini first, fall back to simple calculation
                    quote_data = None
                    if gemini and gemini.initialized:
                        try:
                            print(f"Calculating quote with Gemini (base price: ${base_price:.2f})...")
                            quote_data = gemini.calculate_quote(
                                base_price, 
                                market_data,
                                product_name=product,
                                width=width,
                                location=location
                            )
                            print(f"Gemini quote: {quote_data}")
                        except Exception as e:
                            print(f"Gemini calculation failed: {str(e)}")
                            quote_data = None
                    
                    # Fallback if Gemini failed
                    if not quote_data:
                        quote_data = {
                            "selling_price": base_price * 1.3,
                            "margin": 30.0,
                            "confidence": 0.5
                        }
                        print(f"Using fallback quote calculation: {quote_data}")
                    
                    # Security: Sanitize AI data for non-admins immediately
                    if not is_admin:
                        quote_data.pop('suggested_retail_price', None)
                        quote_data.pop('suggested_dealer_price', None)
                    
                    # Pricing Logic: Determine final selling price
                    ai_selling_price = quote_data["selling_price"]
                    standard_selling_price = base_price * 1.3
                    
                    if is_admin and use_ai_reference:
                        selling_price = standard_selling_price
                        margin = 30.0
                    else:
                        selling_price = ai_selling_price
                        margin = quote_data["margin"]
                        
                    suggested_retail = quote_data.get("suggested_retail_price")
                    suggested_dealer = quote_data.get("suggested_dealer_price")
                    
                    total = round(selling_price * quantity, 2)
                    
                    # Create quote with user_id and pending status
                    # Create quote with user_id and pending status
                    user_id = st.session_state.get('user_id')
                    db.create_quote(
                        customer_name, location,
                        json.dumps({"product": product, "width": width}),
                        quantity, total, user_id=user_id,
                        status='pending_admin_approval',
                        ai_retail_price=suggested_retail,
                        ai_dealer_price=suggested_dealer,
                        ai_zip_code=location,
                        ai_generated_at=datetime.now()
                    )
                    
                    st.success("✓ Quote Submitted for Approval!")
                    
                    is_admin = st.session_state.get('role') in ['admin', 'super_admin']
                    
                    if is_admin:
                        st.info("Your quote has been sent to the admin for review. You will be notified once it is approved.")
                        st.write("---")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Price per sqft", format_currency(selling_price))
                            st.metric("Quantity", f"{quantity} sqft")
                        with col2:
                            st.metric("Total Amount", format_currency(total))
                            st.metric("Margin", f"{margin:.1f}%")
                        with col3:
                            if promo_active and discount_pct and discount_pct > 0:
                                st.metric("Discount Applied", f"🎉 {discount_pct}%")
                                st.caption(f"📌 {promo_name}")
                                days_left = db.get_promotion_days_remaining(end_date)
                                st.caption(f"⏰ {days_left} days left")
                            else:
                                st.metric("Pricing", "✓ Standard Rate")
                        
                        with st.expander("📋 Detailed Quote Breakdown"):
                            st.write(f"**Customer:** {customer_name}")
                            st.write(f"**Location:** {location}")
                            st.write(f"**Product:** {width} {product}")
                            st.write(f"**Standard Price (per sqft):** {format_currency(standard_price)}")
                            if promo_active and discount_pct and discount_pct > 0:
                                discounted_price = standard_price * (1 - discount_pct / 100)
                                st.write(f"**Applied Discount:** {discount_pct}% = {format_currency(discounted_price)}")
                            st.write(f"**Selling Price (per sqft):** {format_currency(selling_price)}")
                            st.write(f"**Market Analysis:** {market_data.get('demand_indicator', 'N/A')}")
                            
                            # Admin-only visibility for AI suggested prices
                            st.divider()
                            st.markdown("### 🤖 AI Market Pricing (Zip-Code Based)")
                            
                            with st.container(border=True):
                                st.caption(f"📍 **Zip Code Used:** {location}")
                                
                                ac1, ac2 = st.columns(2)
                                with ac1:
                                    if suggested_retail:
                                        st.metric("Suggested Retail Price", format_currency(suggested_retail), help="Market rate for end consumers")
                                with ac2:
                                    if suggested_dealer:
                                        st.metric("Suggested Dealer Price", format_currency(suggested_dealer), help="Market rate for contractors/dealers")
                                
                                st.caption("📝 *Note: For reference only. Supplier pricing remains the source of truth.*")
                            
                            if matching_product:
                                st.divider()
                                st.subheader("💰 Promotion & Discount Details")
                                
                                volume_discounts = matching_product.get('volume_discounts')
                                
                                if discount_pct and discount_pct > 0:
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**🎯 Discount Rate:** {discount_pct}%")
                                        if promo_name:
                                            st.write(f"**📌 Promotion:** {promo_name}")
                                        if start_date and end_date:
                                            days_left = db.get_promotion_days_remaining(end_date)
                                            status_icon = "✅ ACTIVE" if promo_active else "⏱️ ENDED"
                                            st.write(f"**📅 Status:** {status_icon}")
                                            if promo_active:
                                                st.write(f"**⏰ Days Remaining:** {days_left} days")
                                            st.write(f"**Valid:** {start_date.split()[0]} to {end_date.split()[0]}")
                                    with col2:
                                        if volume_discounts:
                                            st.write("**📦 Volume Discounts:**")
                                            st.info(volume_discounts)
                                else:
                                    if volume_discounts:
                                        st.info(f"📦 **Volume Discounts Available:** {volume_discounts}")
                    else:
                        # Regular User View - STRICTLY LIMITED
                        st.info("ℹ️ Quote submitted for admin review")
                        
                        uc1, uc2, uc3 = st.columns(3)
                        with uc1:
                            if suggested_retail:
                                st.metric("Suggested Retail Price", format_currency(suggested_retail), help="AI-Suggested Market Price")
                            else:
                                st.metric("Suggested Retail Price", "Pending")
                        with uc2:
                            st.metric("Quantity", f"{quantity} sqft")
                        with uc3:
                            st.metric("Status", "Pending Admin Approval")
                        
                except Exception as e:
                    st.error(f"Error generating quote: {str(e)}")

# ===================== ANALYTICS =====================
def render_analytics_page():
    st.header("📊 Analytics Dashboard")
    
    # --- AI Market Pricing Lookup (Admin & Super Admin Only) ---
    user_id = st.session_state.get('user_id')
    is_admin = db.is_user_admin(user_id) if user_id else False
    
    if is_admin:
        with st.container(border=True):
            st.subheader("🤖 AI Market Pricing Lookup")
            st.caption("On-demand market pricing analysis for any product and location.")
            
            products_data = db.get_products()
            if products_data:
                product_names = sorted(list(set(p['name'] for p in products_data)))
                
                lcol1, lcol2, lcol3 = st.columns([2, 1, 1])
                
                with lcol1:
                    selected_product = st.selectbox("Select Product", options=product_names, key="lookup_product")
                
                with lcol2:
                    available_widths = sorted(list(set(p['width'] for p in products_data if p['name'] == selected_product)))
                    selected_width = st.selectbox("Select Width", options=available_widths, key="lookup_width")
                
                with lcol3:
                    lookup_zip = st.text_input("Zip Code", placeholder="e.g. 90210", key="lookup_zip")
                
                if st.button("🔍 Get AI Pricing", type="primary", use_container_width=True):
                    if not lookup_zip:
                        st.error("⚠️ Please enter a Zip Code to perform the lookup.")
                    else:
                        with st.spinner(f"AI is analyzing market data for {selected_product} in {lookup_zip}..."):
                            try:
                                # Find the product to get its base cost
                                matching_p = next((p for p in products_data if p['name'] == selected_product and p['width'] == selected_width), None)
                                base_price = matching_p['standard_price'] if matching_p else 4.0
                                
                                product_with_price = {
                                    "name": selected_product,
                                    "width": selected_width,
                                    "base_price": base_price
                                }
                                
                                # Call AI logic
                                market_data = get_market_data(lookup_zip, product_with_price)
                                
                                if gemini and gemini.initialized:
                                    quote_data = gemini.calculate_quote(
                                        base_price, 
                                        market_data,
                                        product_name=selected_product,
                                        width=selected_width,
                                        location=lookup_zip
                                    )
                                    
                                    if quote_data:
                                        st.success("✅ AI Analysis Complete")
                                        
                                        # Display Results
                                        res_col1, res_col2 = st.columns(2)
                                        with res_col1:
                                            st.metric("Suggested Retail Price", f"${quote_data.get('suggested_retail_price', 0):.2f}", help="Market rate for end consumers")
                                        with res_col2:
                                            st.metric("Suggested Dealer Price", f"${quote_data.get('suggested_dealer_price', 0):.2f}", help="Market rate for contractors/dealers")
                                        
                                        st.info(f"📊 **Analysis Context:** {selected_product} ({selected_width}) in {lookup_zip} | Generated at {datetime.now().strftime('%H:%M:%S')}")
                                    else:
                                        st.error("AI could not generate pricing data. Please try again.")
                                else:
                                    st.error("Gemini AI is not initialized. Please check your API key.")
                            except Exception as e:
                                st.error(f"Error during AI lookup: {str(e)}")
            else:
                st.info("No product data available for lookup.")
        st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quote Statistics")
        
        # Check if user is admin for filtering
        user_id = st.session_state.get('user_id')
        is_admin = db.is_user_admin(user_id) if user_id else False
        
        # Show filter indicator
        if is_admin:
            st.caption("👑 Admin view: Showing company-wide statistics")
        else:
            st.caption("👤 Personal view: Showing your quotes only")
        
        try:
            # Fetch comprehensive analytics data
            analytics_data = db.get_analytics_data(user_id=user_id, is_admin=is_admin)
            
            if analytics_data:
                # Process data into DataFrame
                df = pd.DataFrame(analytics_data)
                
                # Extract wood type and width from product_specs JSON
                def extract_specs(specs_str):
                    try:
                        specs = json.loads(specs_str)
                        return specs.get('product', 'Unknown'), specs.get('width', 'Unknown')
                    except:
                        return 'Unknown', 'Unknown'

                df['wood_type'], df['width'] = zip(*df['product_specs'].map(extract_specs))
                
                # Ensure zip_code is available (fallback to location if missing)
                df['zip_code'] = df['zip_code'].fillna(df['location'])
                df['customer_type'] = df['customer_type'].fillna('Unknown').str.title()
                
                # --- Sorting Controls ---
                st.markdown("### 🛠️ Filter & Sort")
                sort_col, order_col = st.columns([2, 1])
                with sort_col:
                    sort_by = st.selectbox(
                        "Sort Quotes By",
                        ["Date (Newest First)", "Date (Oldest First)", "Customer Name", "Wood Type", "Zip Code", "Price (High to Low)"]
                    )
                
                # Apply sorting
                if sort_by == "Date (Newest First)":
                    df = df.sort_values('created_at', ascending=False)
                elif sort_by == "Date (Oldest First)":
                    df = df.sort_values('created_at', ascending=True)
                elif sort_by == "Customer Name":
                    df = df.sort_values('customer_name')
                elif sort_by == "Wood Type":
                    df = df.sort_values('wood_type')
                elif sort_by == "Zip Code":
                    df = df.sort_values('zip_code')
                elif sort_by == "Price (High to Low)":
                    df = df.sort_values('final_price', ascending=False)
                
                # --- Display Key Metrics ---
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Quotes", len(df))
                m2.metric("Avg Quote Value", format_currency(df['final_price'].mean()))
                m3.metric("Total Volume", f"{df['quantity'].sum():,} sqft")
                
                # --- Quote History Chart ---
                if len(df) > 1:
                    st.markdown("### 📈 Quote History")
                    df['created_at'] = pd.to_datetime(df['created_at'])
                    chart_data = df.set_index('created_at')['final_price']
                    st.line_chart(chart_data, width="stretch")
                
                # --- New Visualizations ---
                st.divider()
                st.subheader("📍 Pricing Insights")
                
                tab1, tab2 = st.tabs(["🗺️ Zip Code Analysis", "👥 Dealer vs Retail"])
                
                with tab1:
                    st.markdown("**Average Price per SqFt by Zip Code**")
                    if 'zip_code' in df.columns and not df['zip_code'].isnull().all():
                        # Calculate price per sqft for each quote first
                        df['price_per_sqft'] = df['final_price'] / df['quantity']
                        zip_stats = df.groupby('zip_code')['price_per_sqft'].mean().sort_values(ascending=False)
                        st.bar_chart(zip_stats)
                    else:
                        st.info("Insufficient zip code data for analysis.")
                        
                with tab2:
                    st.markdown("**Pricing Strategy: Dealer vs Retail**")
                    if 'customer_type' in df.columns:
                        # Calculate price per sqft
                        if 'price_per_sqft' not in df.columns:
                            df['price_per_sqft'] = df['final_price'] / df['quantity']
                        
                        type_stats = df.groupby('customer_type')['price_per_sqft'].mean()
                        st.bar_chart(type_stats, color="#ffaa00")
                        
                        # Show data table
                        st.dataframe(type_stats.to_frame(name="Avg Price/SqFt").style.format("${:.2f}"), use_container_width=True)
                    else:
                        st.info("Insufficient customer type data.")

                # --- Recent Quotes Table ---
                st.divider()
                st.subheader("📋 Recent Quotes")
                display_cols = ['customer_name', 'wood_type', 'zip_code', 'quantity', 'final_price', 'created_at']
                display_df = df[display_cols].copy()
                display_df.columns = ['Customer', 'Product', 'Zip/Location', 'Sq Ft', 'Total Price', 'Date']
                display_df['Total Price'] = display_df['Total Price'].apply(format_currency)
                st.dataframe(display_df, hide_index=True, use_container_width=True)
                
            else:
                st.info("ℹ️ No quotes generated yet. Create quotes to see statistics.")
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")
    
    with col2:
        st.subheader("Current Pricing Overview")
        products = db.get_products()
        if products:
            products_df = pd.DataFrame([
                {
                    "Product": f"{p['name']} ({p['width']})",
                    "Name": p['name'],
                    "Width": p['width'],
                    "Price/sqft": p['cost_price'],
                    "Last Updated": pd.to_datetime(p['updated_at']).strftime('%Y-%m-%d') if p.get('updated_at') else 'N/A'
                }
                for p in products
            ])
            
            if not products_df.empty:
                st.write("Current Product Prices")
                
                chart_data = products_df.set_index("Product")["Price/sqft"]
                st.bar_chart(chart_data, width="stretch")
                
                display_df = products_df[["Name", "Width", "Price/sqft", "Last Updated"]].copy()
                display_df["Price/sqft"] = display_df["Price/sqft"].apply(lambda x: f"${x:.2f}")
                st.dataframe(display_df, hide_index=True, width="stretch")
        else:
            st.info("ℹ️ No product data available. Add products to see analytics.")
    
    st.divider()
    
    # New comprehensive tables section
    st.subheader("🎯 Product Discount & Promotion Insights")
    
    products = db.get_products()
    if products:
        # Prepare comprehensive product data with promotion details
        product_insights = []
        for p in products:
            discount_pct = p.get('discount_percentage', 0)
            promotion_name = p.get('promotion_name')
            start_date = p.get('promotion_start_date')
            end_date = p.get('promotion_end_date')
            volume_discounts = p.get('volume_discounts')
            min_qty = p.get('min_qty_discount')
            category = p.get('category', 'Standard')
            
            # Classify tier
            if discount_pct and discount_pct >= 15:
                tier = "🏆 Premium+"
            elif discount_pct and discount_pct >= 8:
                tier = "⭐ Premium"
            elif discount_pct and discount_pct >= 5:
                tier = "💎 Mid-Tier"
            elif discount_pct:
                tier = "📦 Standard"
            else:
                tier = "💰 Budget"
            
            # Check promotion status
            if promotion_name and start_date and end_date:
                is_active = db.is_promotion_active(start_date, end_date)
                days_remaining = db.get_promotion_days_remaining(end_date)
                promo_status = f"✅ Active ({days_remaining}d left)" if is_active else "⏱️ Expired"
            else:
                promo_status = "None"
                days_remaining = 0
            
            product_insights.append({
                'Product': f"{p['name']} {p['width']}",
                'Category': category,
                'Tier': tier,
                'Base Price': f"${p['cost_price']:.2f}",
                'Standard Price': f"${p['standard_price']:.2f}",
                'Discount %': f"{discount_pct}%" if discount_pct else "—",
                'Promotion': promotion_name if promotion_name else "None",
                'Promo Status': promo_status,
                'Volume Tiers': "Yes" if volume_discounts else "No",
                'Min Qty': f"{min_qty} sqft" if min_qty else "—"
            })
        
        insights_df = pd.DataFrame(product_insights)
        
        # Display with styling
        st.write("**Product Discount & Promotion Matrix**")
        st.dataframe(insights_df, hide_index=True, width="stretch")
        
        # Summary statistics
        st.write("**Key Business Insights**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            active_promos = sum(1 for p in product_insights if "Active" in p['Promo Status'])
            st.metric("Active Promotions", active_promos)
        
        with col2:
            products_with_volume = sum(1 for p in product_insights if p['Volume Tiers'] == "Yes")
            st.metric("Volume Discount Offerings", products_with_volume)
        
        with col3:
            avg_discount = pd.to_numeric(insights_df['Discount %'].str.rstrip('%'), errors='coerce').mean()
            st.metric("Avg Discount %", f"{avg_discount:.1f}%" if not pd.isna(avg_discount) else "N/A")
        
        with col4:
            total_products = len(insights_df)
            st.metric("Total Products", total_products)
        
        # Tier distribution
        st.write("**Product Tier Distribution**")
        tier_counts = pd.Series([p['Tier'] for p in product_insights]).value_counts()
        st.bar_chart(tier_counts)
    else:
        st.info("ℹ️ No product data available. Add products to see comprehensive insights.")

# ===================== MAIN APP =====================
def main():
    selected = render_sidebar()
    
    if selected == "🛡️ Admin Dashboard":
        # Admin Dashboard - User Management & Quote Approvals
        if st.session_state.get('role') in ['admin', 'super_admin']:
            from admin_ui import render_admin_dashboard
            # Pass email_handler if available, else None
            eh = email_handler if 'email_handler' in globals() else None
            render_admin_dashboard(db, eh)
        else:
            st.error("⛔ Access Denied: Admin privileges required.")
    elif selected == "👥 User Management": # Backward compatibility or removal
        # This block can be removed if "User Management" is no longer an option
        pass
    elif selected == "📧 Supplier Management":
        # Protect supplier management - admin only
        if require_admin():
            from supplier_ui import render_supplier_page
            render_supplier_page(db, email_handler, gemini)
    elif selected == "💰 Quote Generator":
        render_quote_page()
    elif selected == "👥 Customers":
        render_customer_page()
    elif selected == "📜 Customer History":
        from customer_ui import render_customer_history_page
        render_customer_history_page()
    else:
        render_analytics_page()

if __name__ == "__main__":
    main()
    st.info("Full system: Auto scrape + AI + CRM export")