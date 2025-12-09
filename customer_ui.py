import streamlit as st
import pandas as pd
import time
from datetime import datetime

from models.base import SessionLocal
from repositories.customer_repository import CustomerRepository
from schemas.customer import CustomerCreate, CustomerUpdate

def get_repository():
    if 'db' not in st.session_state:
        st.session_state.db = SessionLocal()
    return CustomerRepository(st.session_state.db)

def show_toast(message: str, type: str = "success"):
    if type == "success":
        st.toast(message, icon="✅")
    elif type == "error":
        st.toast(message, icon="❌")
    elif type == "info":
        st.toast(message, icon="ℹ️")

@st.dialog("Add Customer")
def add_customer_dialog():
    repo = get_repository()
    with st.form("add_customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name*")
            email = st.text_input("Email*")
        with col2:
            phone = st.text_input("Phone")
            location = st.text_input("Location")
        
        notes = st.text_area("Notes")
        
        submitted = st.form_submit_button("Create Customer", type="primary")
        
        if submitted:
            if not full_name or not email:
                st.error("Name and Email are required.")
                return
            
            try:
                # Check if email exists
                if repo.get_by_email(email):
                    st.error("Email already exists.")
                    return

                new_customer = CustomerCreate(
                    full_name=full_name, 
                    email=email, 
                    phone=phone, 
                    location=location,
                    notes=notes
                )
                repo.create(new_customer)
                st.session_state.refresh_key = time.time() # Trigger refresh
                st.rerun()
            except Exception as e:
                st.error(f"Error creating customer: {str(e)}")

@st.dialog("Edit Customer")
def edit_customer_dialog(customer_id, current_name, current_email, current_phone, current_location, current_notes):
    repo = get_repository()
    with st.form("edit_customer_form"):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name*", value=current_name)
            email = st.text_input("Email*", value=current_email)
        with col2:
            phone = st.text_input("Phone", value=current_phone if current_phone else "")
            location = st.text_input("Location", value=current_location if current_location else "")
            
        notes = st.text_area("Notes", value=current_notes if current_notes else "")
        
        submitted = st.form_submit_button("Update Customer", type="primary")
        
        if submitted:
            if not full_name or not email:
                st.error("Name and Email are required.")
                return
            
            try:
                # Check email uniqueness if changed
                existing = repo.get_by_email(email)
                if existing and str(existing.id) != str(customer_id):
                    st.error("Email already exists.")
                    return

                update_data = CustomerUpdate(
                    full_name=full_name, 
                    email=email, 
                    phone=phone, 
                    location=location,
                    notes=notes
                )
                repo.update(customer_id, update_data)
                st.session_state.refresh_key = time.time()
                st.rerun()
            except Exception as e:
                st.error(f"Error updating customer: {str(e)}")

def render_customer_page():
    st.title("👥 Customer Management")
    
    repo = get_repository()
    
    # Top controls
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_query = st.text_input("🔍 Search customers...", placeholder="Name, email, phone, or location")
    
    with col2:
        show_deleted = st.checkbox("Show Deleted", value=False)
    
    with col3:
        if st.button("➕ Add Customer", type="primary", use_container_width=True):
            add_customer_dialog()
    
    # Pagination state
    if 'customer_page' not in st.session_state:
        st.session_state.customer_page = 0
    
    PAGE_SIZE = 10
    
    # Fetch Data
    customers, total_count = repo.list_customers(
        skip=st.session_state.customer_page * PAGE_SIZE,
        limit=PAGE_SIZE,
        search_query=search_query,
        include_deleted=show_deleted
    )
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Customers", total_count)
    m2.metric("Active Customers", total_count) # Placeholder logic, could be refined
    m3.metric("New This Month", "0") # Placeholder
    
    st.divider()
    
    # Display Data
    if not customers:
        st.info("No customers found.")
    else:
        # Convert to DataFrame for display
        data = []
        for c in customers:
            data.append({
                "ID": str(c.id),
                "Name": c.full_name,
                "Email": c.email,
                "Phone": c.phone,
                "Location": c.location,
                "Notes": c.notes,
                "Status": "Deleted" if c.is_deleted else "Active",
                "Created": c.created_at.strftime("%Y-%m-%d"),
            })
        
        df = pd.DataFrame(data)
        
        # Use columns for a custom card-like or improved table layout
        # For "stunning" visuals, we can use a styled dataframe or custom HTML, 
        # but let's stick to a clean Streamlit layout with columns for actions.
        
        # Header
        cols = st.columns([2, 2, 1.5, 1.5, 2, 1, 1])
        headers = ["Name", "Email", "Phone", "Location", "Notes", "Status", "Actions"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")
        
        st.markdown("---")
        
        for c in customers:
            cols = st.columns([2, 2, 1.5, 1.5, 2, 1, 1])
            
            # Name & Avatar
            with cols[0]:
                st.markdown(f"**{c.full_name}**")
            
            cols[1].write(c.email)
            cols[2].write(c.phone or "-")
            cols[3].write(c.location or "-")
            
            # Notes with truncation
            notes_display = c.notes if c.notes else "-"
            if len(notes_display) > 30:
                cols[4].write(notes_display[:30] + "...", help=notes_display)
            else:
                cols[4].write(notes_display)
            
            status_color = "red" if c.is_deleted else "green"
            cols[5].markdown(f":{status_color}[{'Deleted' if c.is_deleted else 'Active'}]")
            
            with cols[6]:
                if not c.is_deleted:
                    c1, c2 = st.columns(2)
                    if c1.button("✏️", key=f"edit_{c.id}", help="Edit"):
                        edit_customer_dialog(c.id, c.full_name, c.email, c.phone, c.location, c.notes)
                    
                    if c2.button("🗑️", key=f"del_{c.id}", help="Delete", type="secondary"):
                        if repo.delete(c.id):
                            show_toast("Customer deleted", "success")
                            time.sleep(0.5)
                            st.rerun()
                else:
                    if st.button("♻️ Restore", key=f"res_{c.id}"):
                        if repo.restore(c.id):
                            show_toast("Customer restored", "success")
                            time.sleep(0.5)
                            st.rerun()
            
            st.markdown("---")

    # Pagination Controls
    total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE
    
    if total_pages > 1:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("Previous", disabled=st.session_state.customer_page == 0):
                st.session_state.customer_page -= 1
                st.rerun()
        with c2:
            st.markdown(f"<div style='text-align: center'>Page {st.session_state.customer_page + 1} of {total_pages}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("Next", disabled=st.session_state.customer_page >= total_pages - 1):
                st.session_state.customer_page += 1
                st.rerun()

def render_customer_history_page():
    st.title("📜 Customer History & Insights")
    
    repo = get_repository()
    customers, _ = repo.list_customers(limit=1000)
    
    if not customers:
        st.info("No customers found.")
        return

    # Customer Selector
    customer_options = {f"{c.full_name} ({c.email})": c for c in customers}
    selected_customer_key = st.selectbox(
        "Select Customer to View History",
        options=list(customer_options.keys())
    )
    
    selected_customer = customer_options[selected_customer_key]
    
    # Customer Profile Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"👤 {selected_customer.full_name}")
        st.write(f"📧 {selected_customer.email}")
        st.write(f"📞 {selected_customer.phone or 'No phone'}")
        st.write(f"📍 {selected_customer.location or 'No location'}")
    
    with col2:
        st.metric("Customer Since", selected_customer.created_at.strftime("%Y-%m-%d"))
    
    st.divider()
    
    # Fetch Quotes for this customer
    # Note: We need a method to get quotes by customer. 
    # Assuming we can query the quotes table directly or via a repository.
    # For now, we'll use a direct SQL query or helper if available, 
    # but since we are in the UI, let's use the session from repo.
    
    try:
        # This assumes a 'quotes' table exists and has 'customer_name' or similar.
        # Ideally we should link by ID, but the current quote system uses names.
        # We'll match by name for now as per existing app logic.
        from sqlalchemy import text
        
        # Buying Power / Insights
        st.subheader("💰 Buying Power & Insights")
        
        # Calculate metrics
        query = text("SELECT COUNT(*) as count, SUM(final_price) as total_spend, AVG(final_price) as avg_order FROM quotes WHERE customer_name = :name")
        result = repo.db.execute(query, {"name": selected_customer.full_name}).fetchone()
        
        count = result[0] or 0
        total_spend = result[1] or 0
        avg_order = result[2] or 0
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Quotes/Orders", count)
        m2.metric("Total Spend (Est.)", f"${total_spend:,.2f}")
        m3.metric("Avg. Order Value", f"${avg_order:,.2f}")
        
        # Buying Power Logic
        if total_spend > 10000:
            power = "🔥 High Roller"
            desc = "Top tier customer with high spending capacity."
        elif total_spend > 5000:
            power = "⭐ Strong Buyer"
            desc = "Consistent buyer with good potential."
        elif total_spend > 1000:
            power = "🌱 Growing"
            desc = "Regular customer, potential for upsell."
        else:
            power = "🆕 New / Low Volume"
            desc = "Needs nurturing to increase spend."
            
        st.info(f"**Buying Power Status:** {power} - {desc}")
        
        st.subheader("📜 Purchase History")
        
        history_query = text("SELECT * FROM quotes WHERE customer_name = :name ORDER BY created_at DESC")
        history = repo.db.execute(history_query, {"name": selected_customer.full_name}).fetchall()
        
        if history:
            # Convert to dicts for dataframe
            history_data = []
            for row in history:
                # Map row to dict based on column names (assuming standard SQLAlchemy row)
                # If row is tuple-like, we might need index. 
                # But .fetchall() with text() usually returns Row objects which are accessible by key.
                # Let's try to be safe.
                try:
                    row_dict = row._mapping
                except AttributeError:
                    # Fallback for older SQLAlchemy
                    row_dict = dict(row)
                
                history_data.append({
                    "Date": row_dict.get('created_at'),
                    "Location": row_dict.get('location'),
                    "Product Specs": row_dict.get('product_specs'),
                    "Quantity": row_dict.get('quantity'),
                    "Total": f"${row_dict.get('final_price', 0):,.2f}"
                })
            
            st.dataframe(pd.DataFrame(history_data), width="stretch")
        else:
            st.write("No purchase history found.")
            
    except Exception as e:
        st.error(f"Error loading history: {str(e)}")

