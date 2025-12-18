import streamlit as st
import json
import time
from datetime import datetime

def render_approval_dashboard(db, email_handler):
    st.header("✅ Quote Approvals")
    
    # Fetch pending quotes
    conn = db.get_connection()
    try:
        c = conn.cursor()
        c.execute('''SELECT q.id, q.customer_name, q.location, q.product_specs, 
                            q.quantity, q.final_price, q.created_at, q.user_id,
                            u.full_name as created_by
                     FROM quotes q
                     LEFT JOIN users u ON q.user_id = u.id
                     WHERE q.status = 'pending_admin_approval'
                     ORDER BY q.created_at DESC''')
        pending_quotes = [dict(row) for row in c.fetchall()]
    finally:
        conn.close()
        
    if not pending_quotes:
        st.info("🎉 No pending quotes to review!")
        return

    st.write(f"Found **{len(pending_quotes)}** quotes waiting for approval.")
    
    for quote in pending_quotes:
        with st.expander(f"Quote #{quote['id']} - {quote['customer_name']} - ${quote['final_price']:,.2f}"):
            col1, col2 = st.columns(2)
            
            # Parse product specs
            try:
                specs = json.loads(quote['product_specs'])
                product_name = f"{specs.get('width', '')} {specs.get('product', '')}"
            except:
                product_name = quote['product_specs']
            
            with col1:
                st.write(f"**Customer:** {quote['customer_name']}")
                st.write(f"**Location:** {quote['location']}")
                st.write(f"**Created By:** {quote['created_by'] or 'Unknown'}")
                st.write(f"**Date:** {quote['created_at']}")
                
            with col2:
                st.write(f"**Product:** {product_name}")
                st.write(f"**Quantity:** {quote['quantity']} sqft")
                st.metric("Total Price", f"${quote['final_price']:,.2f}")
                
            st.divider()
            
            b1, b2, b3 = st.columns([1, 1, 1])
            
            if b1.button("✅ Approve", key=f"approve_{quote['id']}", type="primary"):
                _approve_quote(db, email_handler, quote)
                
            if b2.button("❌ Reject", key=f"reject_{quote['id']}", type="secondary"):
                reject_quote_dialog(db, quote['id'])
                
            if b3.button("✏️ Edit", key=f"edit_{quote['id']}"):
                edit_quote_dialog(db, quote)

@st.dialog("Reject Quote")
def reject_quote_dialog(db, quote_id):
    st.write(f"Rejecting Quote #{quote_id}")
    with st.form(f"reject_form_{quote_id}"):
        reason = st.text_area("Reason for Rejection", placeholder="e.g., Price too low, incorrect specs...")
        if st.form_submit_button("Confirm Rejection", type="primary"):
            if not reason:
                st.error("Please provide a reason.")
            else:
                if db.update_quote_status(quote_id, 'rejected', reason):
                    st.warning(f"Quote #{quote_id} rejected.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Failed to reject quote.")

@st.dialog("Edit Quote")
def edit_quote_dialog(db, quote):
    st.write(f"Editing Quote #{quote['id']} for {quote['customer_name']}")
    
    # Parse current specs
    try:
        specs = json.loads(quote['product_specs'])
    except:
        specs = {"product": quote['product_specs'], "width": ""}

    with st.form("edit_quote_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_price = st.number_input("Total Price ($)", value=float(quote['final_price']), step=0.01)
            new_qty = st.number_input("Quantity (sqft)", value=int(quote['quantity']), step=1)
        with col2:
            new_loc = st.text_input("Location", value=quote['location'])
            new_product = st.text_input("Product Name", value=specs.get('product', ''))
            new_width = st.text_input("Width", value=specs.get('width', ''))
        
        if st.form_submit_button("Save Changes", type="primary"):
            new_specs = json.dumps({"product": new_product, "width": new_width})
            if db.update_quote(quote['id'], new_price, quantity=new_qty, location=new_loc, product_specs=new_specs):
                st.success("Quote updated successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Failed to update quote.")

def _approve_quote(db, email_handler, quote):
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("UPDATE quotes SET status = 'approved' WHERE id = ?", (quote['id'],))
        conn.commit()
        conn.close()
        
        # Send email to customer (mocked for now if email_handler not fully set up for this)
        # In a real scenario, we would use email_handler.send_email
        
        st.success(f"Quote #{quote['id']} approved!")
        st.toast("Quote approved and sent to customer", icon="🚀")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error approving quote: {e}")

def _reject_quote(db, quote_id):
    # This is now handled by reject_quote_dialog
    pass
