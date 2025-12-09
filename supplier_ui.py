import streamlit as st
import pandas as pd
import time
from typing import Dict, Any

from config import SAMPLE_PRODUCTS

def format_currency(value: float) -> str:
    return f"${value:,.2f}"

def clear_database_cache():
    if 'db_refresh_key' in st.session_state:
        st.session_state.db_refresh_key += 1
    st.cache_data.clear()
    st.cache_resource.clear()

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

def check_supplier_replies(db, email_handler, gemini):
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

def render_supplier_page(db, email_handler, gemini):
    st.title("📧 Supplier Management")
    
    # Tabs for better organization
    tab1, tab2, tab3 = st.tabs(["Active Suppliers", "Send Price Requests", "Price Updates"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Your Suppliers")
            suppliers = db.get_suppliers()
            if not suppliers:
                st.info("No suppliers added yet. Add one to get started!")
            else:
                # Card view for suppliers
                for s in suppliers:
                    with st.container():
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"### {s.get('name', 'Unknown')}")
                            st.caption(f"📧 {s.get('email', '-')}")
                            if s.get('contact_info'):
                                st.write(f"📝 {s.get('contact_info')}")
                        with c2:
                            st.write("") # Placeholder for actions if needed
                        st.divider()

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
                                db.add_supplier(name, email, contact)
                                st.success(f"Added supplier: {name}")
                                time.sleep(0.5)
                                st.rerun()

    with tab2:
        st.subheader("Send Price Requests")
        st.write("Select suppliers and products to request updated pricing.")
        
        with st.form("price_request"):
            c1, c2 = st.columns(2)
            with c1:
                suppliers_list = db.get_suppliers()
                selected_suppliers = st.multiselect(
                    "Select Suppliers",
                    options=suppliers_list,
                    format_func=lambda x: x.get('name', str(x)) if isinstance(x, dict) else str(x)
                )
            with c2:
                products = st.multiselect(
                    "Select Products",
                    options=[p["name"] for p in SAMPLE_PRODUCTS]
                )
            
            if st.form_submit_button("Send Price Request", type="primary", use_container_width=True):
                if selected_suppliers and products:
                    for supplier in selected_suppliers:
                        supplier_email = supplier.get('email', '')
                        supplier_name = supplier.get('name', 'Unknown Supplier')
                        
                        result = email_handler.send_price_request(supplier_email, products)
                        if result.get('status') == 'success':
                            st.success(f"Price request sent to {supplier_name}")
                        else:
                            st.error(f"Failed to send to {supplier_name}: {result.get('error', 'Unknown error')}")
                else:
                    st.warning("Please select at least one supplier and product")

    with tab3:
        st.subheader("Test Price Updates")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔄 Auto-Check Replies")
            st.write("Scan your inbox for replies from suppliers and automatically update prices.")
            
            if st.button("Check Email Replies", key="check_replies", type="primary"):
                with st.spinner("🔍 Scanning inbox..."):
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

        with col2:
            st.markdown("#### 📝 Manual Update")
            st.write("Manually update a product price for testing.")
            
            test_product = st.selectbox(
                "Select Product",
                options=[p["name"] for p in SAMPLE_PRODUCTS]
            )
            
            current_products = db.get_products()
            product_widths = [p['width'] for p in current_products if p['name'] == test_product]
            if not product_widths:
                product_widths = ["5\"", "7\""]
            
            test_width = st.selectbox("Width", options=product_widths)
            
            test_price = st.number_input("New Price per sqft", min_value=0.01, value=5.0, step=0.1)
            
            if st.button("Update Price", type="primary"):
                try:
                    width_to_use = test_width.strip() if test_width else None
                    if width_to_use and not width_to_use.endswith('"'):
                        width_to_use = f'{width_to_use}"'
                    
                    success = db.update_product_price(test_product, test_price, width_to_use)
                    if success:
                        clear_database_cache()
                        st.success(f"Updated {test_product} to ${test_price:.2f}")
                    else:
                        st.error("Failed to update price.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        st.divider()
        st.subheader("Current Price List")
        current_products = db.get_products()
        if current_products:
            df = pd.DataFrame(current_products)
            df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
            styled_df = df[['name', 'width', 'cost_price', 'updated_at']].copy()
            styled_df.columns = ['Product', 'Width', 'Price/sqft', 'Last Updated']
            styled_df['Price/sqft'] = styled_df['Price/sqft'].apply(lambda x: f'${x:.2f}')
            st.dataframe(styled_df, hide_index=True, width="stretch")
