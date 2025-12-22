import streamlit as st
import pandas as pd
import time
from typing import Dict, Any

from config import SAMPLE_PRODUCTS, SUPPORTED_WIDTHS
from utils import validate_width

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

@st.dialog("Supplier Inventory")
def view_supplier_inventory(db, supplier_id, supplier_name):
    """Display all products from a specific supplier in read-only format"""
    st.subheader(f"Products from {supplier_name}")
    
    # Get products from this supplier
    products = db.get_products_by_supplier(supplier_id)
    
    if not products:
        st.info(f"No products found from {supplier_name}")
        st.caption("Products will appear here once they are imported from this supplier.")
        return
    
    # Display count
    st.caption(f"Total Products: {len(products)}")
    
    # Create DataFrame for display
    data = []
    for p in products:
        data.append({
            "Product": p['name'],
            "Width": p['width'],
            "Category": p['category'],
            "Cost Price": f"${p['cost_price']:.2f}",
            "Standard Price": f"${p['standard_price']:.2f}",
            "Discount": f"{p['discount_percentage']}%" if p['discount_percentage'] else "-",
            "Promotion": p['promotion_name'] or "-",
            "Last Updated": p['updated_at']
        })
    
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True)

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
    
    # Check if user is admin
    from database import Database
    from config import DATABASE_PATH
    db_instance = Database(DATABASE_PATH)
    user_id = st.session_state.get('user_id')
    is_admin = db_instance.is_user_admin(user_id) if user_id else False
    
    # Tabs for better organization - add Bulk Import for admins
    if is_admin:
        tab1, tab2, tab3, tab4 = st.tabs(["Active Suppliers", "Send Price Requests", "Price Updates", "📤 Bulk Import"])
    else:
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
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if s.get('phone'): st.write(f"📞 {s.get('phone')}")
                                if s.get('zip_code'): st.write(f"📍 {s.get('zip_code')}")
                            with col_b:
                                if s.get('address'): st.write(f"🏠 {s.get('address')}")
                            
                            if s.get('additional_info'):
                                st.write(f"📝 {s.get('additional_info')}")
                        with c2:
                            st.write("")  # Spacing
                            if st.button("📦 View Supply", key=f"view_{s['id']}", type="secondary", use_container_width=True):
                                view_supplier_inventory(db, s['id'], s['name'])
                        st.divider()

        with col2:
            st.subheader("Add New Supplier")
            with st.form("new_supplier"):
                name = st.text_input("Supplier Name*")
                email = st.text_input("Email*")
                phone = st.text_input("Phone")
                address = st.text_input("Address")
                zip_code = st.text_input("Zip Code")
                additional_info = st.text_area("Additional Info")
                
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
                                db.add_supplier(name, email, phone, address, zip_code, additional_info)
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
            
            # Supplier Selection
            suppliers_list = db.get_suppliers()
            selected_supplier_manual = st.selectbox(
                "Select Supplier",
                options=suppliers_list,
                format_func=lambda x: x.get('name', str(x)) if isinstance(x, dict) else str(x),
                key="manual_supplier_select"
            )
            
            test_product = st.selectbox(
                "Select Product",
                options=[p["name"] for p in SAMPLE_PRODUCTS]
            )
            
            width_option = st.selectbox("Width", options=SUPPORTED_WIDTHS, key="manual_width_select")
            
            test_width = width_option
            if width_option == "Custom":
                test_width = st.text_input("Enter Custom Width", placeholder="e.g. 9\"", key="manual_custom_width")
                test_width = validate_width(test_width)
            
            test_price = st.number_input("New Price per sqft", min_value=0.01, value=5.0, step=0.1)
            
            if st.button("Update Price", type="primary"):
                if not selected_supplier_manual:
                    st.error("Please select a supplier first.")
                else:
                    try:
                        width_to_use = test_width.strip() if test_width else None
                        if width_to_use and not width_to_use.endswith('"'):
                            width_to_use = f'{width_to_use}"'
                        
                        # Get supplier ID
                        supplier_id = selected_supplier_manual.get('id')
                        
                        success = db.update_product_price(test_product, test_price, width_to_use, supplier_id=supplier_id)
                        if success:
                            # Log the manual update with supplier ID
                            supplier_name = selected_supplier_manual.get('name')
                            msg = f"Manual update: {test_product} {width_to_use} to ${test_price:.2f}"
                            db.log_sync_event("manual_update", "success", msg, supplier_id)
                            
                            clear_database_cache()
                            st.success(f"Updated {test_product} to ${test_price:.2f} (Source: {supplier_name})")
                        else:
                            st.error("Failed to update price.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        st.divider()
        st.subheader("Current Price List")
        current_products = db.get_products()
        if current_products:
            df = pd.DataFrame(current_products)
            
            # Format dates
            df['updated_at'] = pd.to_datetime(df['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Handle missing supplier names
            df['supplier_name'] = df['supplier_name'].fillna('Unknown')
            
            # Select and rename columns
            styled_df = df[['supplier_name', 'name', 'width', 'standard_price', 'updated_at']].copy()
            styled_df.columns = ['Supplier', 'Product', 'Width', 'Price/sqft', 'Last Updated']
            
            # Sort by Price (Highest to Lowest)
            styled_df = styled_df.sort_values(by='Price/sqft', ascending=False)
            
            # Format price
            styled_df['Price/sqft'] = styled_df['Price/sqft'].apply(lambda x: f'${x:.2f}')
            
            st.dataframe(styled_df, hide_index=True, width="stretch")
    
    # Bulk Import Tab (Admin Only)
    if is_admin:
        with tab4:
            st.subheader("📤 Bulk Product Import")
            st.caption("Upload CSV or Excel files to bulk import/update products")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # File uploader
                uploaded_file = st.file_uploader(
                    "Choose a file",
                    type=["csv", "xlsx", "xls"],
                    help="Upload a CSV or Excel file with product data"
                )
                
                if uploaded_file:
                    st.info(f"📄 File: {uploaded_file.name} ({uploaded_file.size} bytes)")
                    
                    # Parse file
                    from file_parser import parse_csv_file, parse_excel_file, prepare_product_dict
                    
                    df = None
                    errors = []
                    
                    if uploaded_file.name.endswith('.csv'):
                        df, errors = parse_csv_file(uploaded_file)
                    else:
                        df, errors = parse_excel_file(uploaded_file)
                    
                    if errors:
                        st.error("❌ Validation Errors:")
                        for error in errors:
                            st.write(f"- {error}")
                    
                    if df is not None and not errors:
                        st.success("✅ File validated successfully!")
                        
                        # Preview data
                        with st.expander("📊 Preview Data", expanded=True):
                            st.dataframe(df.head(10), use_container_width=True)
                            st.caption(f"Showing first 10 of {len(df)} rows")
                        
                        # Supplier selection (optional)
                        suppliers = db.get_suppliers()
                        supplier_options = {"None (No supplier)": None}
                        supplier_options.update({s['name']: s['id'] for s in suppliers})
                        
                        selected_supplier = st.selectbox(
                            "Associate with Supplier (Optional)",
                            options=list(supplier_options.keys())
                        )
                        supplier_id = supplier_options[selected_supplier]
                        
                        # Import button
                        if st.button("🚀 Import Products", type="primary", use_container_width=True):
                            with st.spinner("Importing products..."):
                                # Convert DataFrame to list of dicts
                                products_data = [prepare_product_dict(row) for _, row in df.iterrows()]
                                
                                # Import
                                results = db.bulk_import_products(
                                    products_data,
                                    supplier_id=supplier_id,
                                    user_id=user_id
                                )
                                
                                # Display results
                                st.success("✅ Import Complete!")
                                
                                col_a, col_b, col_c = st.columns(3)
                                col_a.metric("✅ Inserted", results['inserted'])
                                col_b.metric("🔄 Updated", results['updated'])
                                col_c.metric("⚠️ Skipped", results['skipped'])
                                
                                if results['errors']:
                                    with st.expander(f"❌ Errors ({len(results['errors'])})", expanded=False):
                                        for error in results['errors']:
                                            st.write(f"Row {error.get('row', '?')}: {error.get('product', 'Unknown')} - {error.get('error', 'Unknown error')}")
                                
                                # Clear cache to refresh product list
                                clear_database_cache()
                                time.sleep(1)
                                st.rerun()
            
            with col2:
                st.subheader("📋 Template")
                st.write("Download a sample template to see the expected format:")
                
                from file_parser import create_sample_template
                import io
                
                # Create sample template
                sample_df = create_sample_template()
                
                # Convert to CSV for download
                csv_buffer = io.StringIO()
                sample_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="�� Download CSV Template",
                    data=csv_data,
                    file_name="product_import_template.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                # Convert to Excel for download
                excel_buffer = io.BytesIO()
                sample_df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_data = excel_buffer.getvalue()
                
                st.download_button(
                    label="📥 Download Excel Template",
                    data=excel_data,
                    file_name="product_import_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.divider()
                
                st.subheader("ℹ️ Instructions")
                st.markdown("""
                **Required Columns:**
                - `name`: Product name
                - `width`: Width (e.g., 5", 7")
                - `standard_price`: Selling price
                
                **Optional Columns:**
                - `cost_price`: Cost per unit
                - `category`: Product category
                - `description`: Product description
                - `discount_percentage`: Discount %
                - `min_qty_discount`: Min quantity for discount
                - `promotion_name`: Promotion name
                - `volume_discounts`: Volume discount tiers
                
                **Notes:**
                - Existing products (same name + width) will be updated
                - New products will be inserted
                - Invalid rows will be skipped with error log
                """)
