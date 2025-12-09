import streamlit as st
import pandas as pd
from typing import List
import time

from models.base import get_db, SessionLocal
from repositories.customer_repository import CustomerRepository
from schemas.customer import CustomerCreate, CustomerUpdate

st.set_page_config(page_title="Customers", page_icon="👥", layout="wide")

# Initialize Session
if 'db' not in st.session_state:
    st.session_state.db = SessionLocal()

def get_repository():
    return CustomerRepository(st.session_state.db)

repo = get_repository()

# --- UI Components ---

def show_toast(message: str, type: str = "success"):
    if type == "success":
        st.toast(message, icon="✅")
    elif type == "error":
        st.toast(message, icon="❌")
    elif type == "info":
        st.toast(message, icon="ℹ️")

@st.dialog("Add Customer")
def add_customer_dialog():
    with st.form("add_customer_form"):
        full_name = st.text_input("Full Name*")
        email = st.text_input("Email*")
        phone = st.text_input("Phone")
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

                new_customer = CustomerCreate(full_name=full_name, email=email, phone=phone, notes=notes)
                repo.create(new_customer)
                st.session_state.refresh_key = time.time() # Trigger refresh
                st.rerun()
            except Exception as e:
                st.error(f"Error creating customer: {str(e)}")

@st.dialog("Edit Customer")
def edit_customer_dialog(customer_id, current_name, current_email, current_phone, current_notes):
    with st.form("edit_customer_form"):
        full_name = st.text_input("Full Name*", value=current_name)
        email = st.text_input("Email*", value=current_email)
        phone = st.text_input("Phone", value=current_phone if current_phone else "")
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

                update_data = CustomerUpdate(full_name=full_name, email=email, phone=phone, notes=notes)
                repo.update(customer_id, update_data)
                st.session_state.refresh_key = time.time()
                st.rerun()
            except Exception as e:
                st.error(f"Error updating customer: {str(e)}")

# --- Main Page Layout ---

st.title("👥 Customers")

# Top controls
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    search_query = st.text_input("🔍 Search customers...", placeholder="Name, email, or phone")

with col2:
    show_deleted = st.checkbox("Show Deleted", value=False)

with col3:
    if st.button("➕ Add Customer", type="primary", use_container_width=True):
        add_customer_dialog()

# Pagination state
if 'page' not in st.session_state:
    st.session_state.page = 0

PAGE_SIZE = 10

# Fetch Data
customers, total_count = repo.list_customers(
    skip=st.session_state.page * PAGE_SIZE,
    limit=PAGE_SIZE,
    search_query=search_query,
    include_deleted=show_deleted
)

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
            "Status": "Deleted" if c.is_deleted else "Active",
            "Created": c.created_at.strftime("%Y-%m-%d"),
            "Actions": "Edit" # Placeholder
        })
    
    df = pd.DataFrame(data)
    
    # Custom Table Layout
    # We use columns for a custom table to allow action buttons
    
    # Header
    cols = st.columns([2, 2, 2, 2, 1, 1, 2])
    headers = ["Name", "Email", "Phone", "Notes", "Status", "Created", "Actions"]
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")
    
    st.divider()
    
    for c in customers:
        cols = st.columns([2, 2, 2, 2, 1, 1, 2])
        
        cols[0].write(c.full_name)
        cols[1].write(c.email)
        cols[2].write(c.phone or "-")
        
        # Notes with truncation
        notes_display = c.notes if c.notes else "-"
        if len(notes_display) > 30:
            cols[3].write(notes_display[:30] + "...", help=notes_display)
        else:
            cols[3].write(notes_display)
        
        status_color = "red" if c.is_deleted else "green"
        cols[4].markdown(f":{status_color}[{'Deleted' if c.is_deleted else 'Active'}]")
        
        cols[5].write(c.created_at.strftime("%Y-%m-%d"))
        
        with cols[6]:
            if not c.is_deleted:
                c1, c2 = st.columns(2)
                if c1.button("✏️", key=f"edit_{c.id}", help="Edit"):
                    edit_customer_dialog(c.id, c.full_name, c.email, c.phone, c.notes)
                
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
        
        st.divider()

# Pagination Controls
total_pages = (total_count + PAGE_SIZE - 1) // PAGE_SIZE

if total_pages > 1:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        if st.button("Previous", disabled=st.session_state.page == 0):
            st.session_state.page -= 1
            st.rerun()
    with c2:
        st.markdown(f"<div style='text-align: center'>Page {st.session_state.page + 1} of {total_pages}</div>", unsafe_allow_html=True)
    with c3:
        if st.button("Next", disabled=st.session_state.page >= total_pages - 1):
            st.session_state.page += 1
            st.rerun()

# Success toast check
if 'success_msg' in st.session_state:
    show_toast(st.session_state.success_msg)
    del st.session_state.success_msg
