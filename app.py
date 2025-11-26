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
    if "No existing Gmail credentials" in str(e):
        st.warning("⚠️ Gmail Email Features Not Available")
        st.info(str(e))
        email_handler = None
    else:
        st.error(f"Error initializing EmailHandler: {str(e)}")
        email_handler = None
except Exception as e:
    # If authentication failed due to expired/revoked token, surface clear UI guidance
    if isinstance(e, google.auth.exceptions.RefreshError) or 'expired' in str(e).lower() or 'revoked' in str(e).lower():
        st.error("Gmail authentication failed: token expired or revoked. Please re-authenticate.")
        st.info("To re-authenticate: delete 'token.json' in the project folder and reload the app. A browser window will open to complete OAuth.")
    else:
        st.error(f"Error initializing EmailHandler: {str(e)}")
    email_handler = None

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
        
        # ==================== USER PROFILE SECTION ====================
        st.divider()
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
        
        # Navigation Menu
        st.divider()
        st.markdown('<p style="font-size: 1.2em; font-weight: 600; margin: 0 0 1em 0;" class="app-title">Navigation</p>', 
                   unsafe_allow_html=True)
                   
        # Demo Controls (at the bottom of sidebar)
        with st.sidebar.expander("🛠️ Demo Controls", expanded=False):
            st.caption("Use these controls to manage demo data")
            if st.button("🔄 Reset Demo Data", type="secondary", use_container_width=True):
                try:
                    db.populate_sample_data()
                    clear_database_cache()
                    st.success("Demo data reset successfully!")
                    st.toast("💫 Fresh demo data loaded!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error resetting data: {str(e)}")
            
            if st.button("🔃 Force Refresh All Data", type="secondary", use_container_width=True):
                try:
                    clear_database_cache()
                    st.success("All caches cleared!")
                    st.toast("✨ Database synced with UI")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error refreshing: {str(e)}")
            
            st.markdown("---")
            st.caption("Gmail troubleshooting")
            if st.button("🔑 Re-authenticate Gmail (delete token)", use_container_width=True):
                try:
                    if os.path.exists('token.json'):
                        os.remove('token.json')
                    st.toast("token.json removed. Reload the app to start OAuth flow.")
                except Exception as e:
                    st.error(f"Could not remove token.json: {e}")
        
        selected = st.radio(
            "Go to",
            ["📧 Supplier Management", "💰 Quote Generator", "📊 Analytics"]
        )
        
        st.divider()
        
        # System Status
        st.subheader("System Status")
        try:
            # Check if Gmail is authenticated
            if email_handler.gmail.is_authenticated():
                st.success("Gmail: Connected ✅")
            else:
                st.warning("Gmail: Not Connected")
        except Exception:
            st.error("Gmail: Authentication Error")
            
        # Quick Stats
        st.subheader("Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Active Suppliers", len(st.session_state.active_suppliers))
        with col2:
            st.metric("Pending Quotes", len(st.session_state.price_requests))
            
        return selected

# ===================== SUPPLIER MANAGEMENT =====================
def render_supplier_page():
    st.header("📧 Supplier Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Active Suppliers")
        suppliers_df = pd.DataFrame(db.get_suppliers())
        if not suppliers_df.empty:
            st.dataframe(suppliers_df, height=300)
        else:
            st.info("No suppliers added yet")
            
    with col2:
        st.subheader("Add New Supplier")
        with st.form("new_supplier"):
            name = st.text_input("Supplier Name")
            email = st.text_input("Email")
            contact = st.text_area("Additional Info")
            
            if st.form_submit_button("Add Supplier", type="primary", use_container_width=True):
                if not name:
                    st.error("Supplier name is required")
                elif not email:
                    st.error("Email is required")
                else:
                    # Email validation
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, email):
                        st.error("Please enter a valid email address")
                    else:
                        # Check if email already exists
                        existing_suppliers = db.get_suppliers()
                        if any(supplier['email'] == email for supplier in existing_suppliers):
                            st.error("A supplier with this email already exists")
                        else:
                            supplier_id = db.add_supplier(name, email, contact)
                            st.success(f"Added supplier: {name}")
                            # Clear form
                            st.rerun()
                    
    st.divider()
    
    # Price Request Section
    st.subheader("Send Price Requests")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("price_request"):
            suppliers_list = db.get_suppliers()
            selected_suppliers = st.multiselect(
                "Select Suppliers",
                options=suppliers_list,
                format_func=lambda x: x.get('name', str(x)) if isinstance(x, dict) else str(x)  # Handle both dict and other formats
            )
            
            products = st.multiselect(
                "Select Products",
                options=[p["name"] for p in SAMPLE_PRODUCTS]
            )
            
            if st.form_submit_button("Send Price Request", type="primary", use_container_width=True):
                if selected_suppliers and products:
                    for supplier in selected_suppliers:
                        # Handle supplier as dictionary
                        supplier_email = supplier.get('email', '')
                        supplier_name = supplier.get('name', 'Unknown Supplier')
                        
                        result = email_handler.send_price_request(supplier_email, products)
                        if result.get('status') == 'success':
                            st.success(f"Price request sent to {supplier_name}")
                        else:
                            st.error(f"Failed to send to {supplier_name}: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please select at least one supplier and product")
    
    with col2:
        # Test Price Update Section
        st.subheader("Test Price Updates")
        with st.expander("🔧 Test Tools", expanded=True):

            if st.button("🔄 Check Email Replies", key="check_replies", type="primary", use_container_width=True):
                with st.spinner("🔍 Scanning inbox for price updates..."):
                    results = email_handler.check_replies_and_save(gemini)
                    
                    if not results:
                        st.warning("📝 No new replies found")
                    else:
                        clear_database_cache()
                        
                        processed_count = 0
                        
                        for result in results:
                            if result.get('products'):
                                processed_count += 1
                                products = result.get('products', [])
                                
                                st.write("📨 **Email processed successfully**")
                                for p in products:
                                    product_name = p.get('name', 'Unknown')
                                    product_price = p.get('price', 0)
                                    st.success(f"{product_name}: ${product_price:.2f}/sqft")
                                st.divider()
                        
                        if processed_count > 0:
                            st.success(f"✨ Successfully processed {processed_count} email replies!")
                            
                            # Show updated prices
                            st.write("**Current Prices After Update:**")
                            current_products = db.get_products()
                            if current_products:
                                df = pd.DataFrame(current_products)
                                df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
                                styled_df = df[['name', 'width', 'cost_price', 'updated_at']].copy()
                                styled_df.columns = ['Product', 'Width', 'Price/sqft', 'Last Updated']
                                styled_df['Price/sqft'] = styled_df['Price/sqft'].apply(lambda x: f'${x:.2f}')
                                
                                st.dataframe(
                                    styled_df,
                                    hide_index=True,
                                    use_container_width=True
                                )            # Manual price update tester
            st.write("---")
            st.write("📝 Test Manual Update")
            
            # Get unique product names
            test_product = st.selectbox(
                "Select Product",
                options=[p["name"] for p in SAMPLE_PRODUCTS]
            )
            
            # Get current products from database
            current_products = db.get_products()
            
            # Get widths for selected product from database
            product_widths = [p['width'] for p in current_products if p['name'] == test_product]
            if not product_widths:
                product_widths = ["5\"", "7\""]  # Default widths if none found
            
            test_width = st.selectbox(
                "Width",
                options=product_widths,
                help="Select the product width"
            )
            
            test_price = st.number_input("New Price per sqft", 
                                       min_value=0.01, 
                                       max_value=100.0, 
                                       value=5.0,
                                       step=0.1)
            
            if st.button("💲 Update Price", type="primary", use_container_width=True):
                if not test_product or not test_price:
                    st.error("Please select a product and enter a price")
                else:
                    try:
                        width_to_use = test_width.strip() if test_width else None
                        if width_to_use and not width_to_use.endswith('"'):
                            width_to_use = f'{width_to_use}"'
                        
                        product_display = f"{test_product} {width_to_use}" if width_to_use else test_product
                        
                        current_products = db.get_products()
                        product_exists = any(
                            p['name'] == test_product and p['width'] == width_to_use
                            for p in current_products
                        )
                        
                        if not product_exists:
                            st.error(f"Product '{product_display}' not found in database. Available widths: {', '.join(product_widths)}")
                        else:
                            success = db.update_product_price(test_product, test_price, width_to_use)
                            if success:
                                clear_database_cache()
                                st.success(f"✓ Updated price for {product_display} to ${test_price:.2f}/sqft")
                                
                                st.write("**Current Prices:**")
                                products_data = db.get_products()
                                if products_data:
                                    prices_df = pd.DataFrame([
                                        {
                                            'Product': p['name'],
                                            'Width': p['width'],
                                            'Price/sqft': f"${p['cost_price']:.2f}",
                                            'Last Updated': pd.to_datetime(p['updated_at']).strftime('%Y-%m-%d %H:%M')
                                        }
                                        for p in products_data
                                    ])
                                    st.dataframe(
                                        prices_df,
                                        hide_index=True,
                                        use_container_width=True
                                    )
                            else:
                                st.error(f"Failed to update price for {product_display}. Please try again.")
                            
                    except Exception as e:
                        st.error(f"Error updating price: {str(e)}")

# ===================== EMAIL HANDLING =====================
def parse_price_from_text(text):
    """Parse product prices from email text."""
    updates = []
    
    # Common width patterns
    width_patterns = ['"', 'inch', '″', '"', 'in']
    
    try:
        # Split into lines and process each line
        lines = text.split('\n')
        for line in lines:
            line = line.strip().lower()
            if not line:
                continue
                
            # Look for price patterns
            if 'updated the price' in line:
                # Parse structured updates like "updated the price of 7" width of Red Oak to $5.14 per sq.ft"
                try:
                    # Extract width
                    width_start = line.find('of ') + 3
                    width_end = line.find(' width')
                    if width_start > 3 and width_end > width_start:
                        width = line[width_start:width_end].strip()
                        
                        # Extract product name
                        product_start = line.find('of ', width_end) + 3
                        product_end = line.find(' to $')
                        if product_start > 3 and product_end > product_start:
                            product = line[product_start:product_end].strip()
                            
                            # Extract price
                            price_start = line.find('$') + 1
                            price_end = line.find(' per')
                            if price_start > 0 and price_end > price_start:
                                price = float(line[price_start:price_end].strip())
                                
                                # Format width consistently
                                if not any(w in width for w in width_patterns):
                                    width = f'{width}"'
                                
                                updates.append({
                                    'product': product.title(),
                                    'width': width,
                                    'price': price
                                })
                except Exception as e:
                    st.warning(f"Could not parse line: {line}")
                    
    except Exception as e:
        st.error(f"Error parsing email: {str(e)}")
    
    return updates

def check_supplier_replies():
    try:
        results = email_handler.check_replies_and_save(gemini)
        if results:
            messages = []
            for result in results:
                try:
                    supplier = result.get('supplier', 'Unknown Supplier')
                    message_text = result.get('message', '')
                    
                    if isinstance(message_text, str):
                        # Parse prices from the email text
                        price_updates = parse_price_from_text(message_text)
                        
                        if price_updates:
                            messages.append(f"✓ Processing updates from {supplier}:")
                            for update in price_updates:
                                try:
                                    success = db.update_product_price(
                                        update['product'],
                                        update['price'],
                                        update['width']
                                    )
                                    if success:
                                        messages.append(
                                            f"  • Updated {update['product']} ({update['width']}) "
                                            f"to ${update['price']:.2f}/sqft"
                                        )
                                    else:
                                        messages.append(
                                            f"  ⚠️ Failed to update {update['product']} ({update['width']})"
                                        )
                                except Exception as e:
                                    messages.append(f"  ⚠️ Error updating {update}: {str(e)}")
                        else:
                            messages.append(f"No price updates found in reply from {supplier}")
                    else:
                        messages.append(f"Invalid message format from {supplier}")
                        
                except Exception as e:
                    messages.append(f"Error processing reply from {supplier}: {str(e)}")
            
            return "\n".join(messages)
        return "No new replies found"
    except Exception as e:
        st.error(f"Error checking replies: {str(e)}")
        return f"Error: {str(e)}"

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
        
        with st.form("quote_form"):
            customer_name = st.text_input("Customer Name", placeholder="Enter customer name")
            location = st.text_input("Location", "Raleigh, NC")
            quantity = st.number_input("Square Feet", 100, 10000, 1000)
            
            submitted = st.form_submit_button("Generate Quote", type="primary", use_container_width=True)
    
    if submitted:
        if not customer_name or not customer_name.strip():
            st.error("⚠️ Customer name is required to generate a quote")
        else:
            with st.spinner("Generating intelligent quote..."):
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
                            quote_data = gemini.calculate_quote(base_price, market_data)
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
                    
                    selling_price = quote_data["selling_price"]
                    margin = quote_data["margin"]
                    total = round(selling_price * quantity, 2)
                    
                    db.create_quote(
                        customer_name, location,
                        json.dumps({"product": product, "width": width}),
                        quantity, total
                    )
                    
                    st.success("✓ Quote Generated Successfully!")
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
                                        st.write(f"**📊 Volume Tiers:**")
                                        st.caption(volume_discounts)
                            else:
                                st.info("ℹ️ No active discounts on this product")
                        
                except Exception as e:
                    st.error(f"Error generating quote: {str(e)}")

# ===================== ANALYTICS =====================
def render_analytics_page():
    st.header("📊 Analytics Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Quote Statistics")
        try:
            quotes = db.get_latest_quotes(100)
            if quotes and len(quotes) > 0:
                quotes_df = pd.DataFrame([
                    {
                        'id': q['id'],
                        'customer_name': q['customer_name'],
                        'location': q['location'],
                        'product_specs': q['product_specs'],
                        'quantity': q['quantity'],
                        'final_price': q['final_price'],
                        'created_at': q['created_at']
                    }
                    for q in quotes
                ])
                
                st.metric("Total Quotes", len(quotes))
                
                if not quotes_df.empty and 'final_price' in quotes_df.columns:
                    avg_value = quotes_df['final_price'].mean()
                    st.metric("Average Quote Value", format_currency(avg_value))
                    
                    if len(quotes_df) > 1:
                        try:
                            quotes_df['created_at'] = pd.to_datetime(quotes_df['created_at'])
                            st.write("Quote History")
                            chart_data = quotes_df.set_index('created_at')['final_price']
                            st.line_chart(chart_data, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not display chart: {str(e)}")
                    
                    st.write("Recent Quotes")
                    display_quotes = quotes_df[['customer_name', 'location', 'quantity', 'final_price']].head(10).copy()
                    display_quotes.columns = ['Customer', 'Location', 'Sq Ft', 'Total']
                    display_quotes['Total'] = display_quotes['Total'].apply(format_currency)
                    st.dataframe(display_quotes, hide_index=True, use_container_width=True)
            else:
                st.info("ℹ️ No quotes generated yet. Create quotes to see statistics.")
        except Exception as e:
            st.error(f"Error loading quote statistics: {str(e)}")
    
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
                st.bar_chart(chart_data, use_container_width=True)
                
                display_df = products_df[["Name", "Width", "Price/sqft", "Last Updated"]].copy()
                display_df["Price/sqft"] = display_df["Price/sqft"].apply(lambda x: f"${x:.2f}")
                st.dataframe(display_df, hide_index=True, use_container_width=True)
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
        st.dataframe(insights_df, hide_index=True, use_container_width=True)
        
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
    
    if selected == "📧 Supplier Management":
        render_supplier_page()
    elif selected == "💰 Quote Generator":
        render_quote_page()
    else:
        render_analytics_page()

if __name__ == "__main__":
    main()
    st.info("Full system: Auto scrape + AI + CRM export")