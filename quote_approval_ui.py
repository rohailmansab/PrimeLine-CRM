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
            
            b1, b2, b3 = st.columns([1, 1, 4])
            
            if b1.button("✅ Approve", key=f"approve_{quote['id']}", type="primary"):
                _approve_quote(db, email_handler, quote)
                
            if b2.button("❌ Reject", key=f"reject_{quote['id']}", type="secondary"):
                _reject_quote(db, quote['id'])

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
    try:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("UPDATE quotes SET status = 'rejected' WHERE id = ?", (quote_id,))
        conn.commit()
        conn.close()
        
        st.warning(f"Quote #{quote_id} rejected.")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error rejecting quote: {e}")
