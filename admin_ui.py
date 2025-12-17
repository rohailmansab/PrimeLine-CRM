import streamlit as st
import pandas as pd
from database import Database
import time

from quote_approval_ui import render_approval_dashboard

def render_admin_dashboard(db: Database, email_handler=None):
    """
    Render the Admin Dashboard.
    Includes User Management and Quote Approvals.
    """
    st.header("🛡️ Admin Dashboard")
    
    # Security check
    if st.session_state.get('role') not in ['admin', 'super_admin']:
        st.error("⛔ Access Denied: Admin privileges required.")
        return

    tab1, tab2 = st.tabs(["👥 User Management", "💰 Quote Approvals"])
    
    with tab1:
        render_user_management_tab(db)
        
    with tab2:
        render_approval_dashboard(db, email_handler)

def render_user_management_tab(db: Database):
    """
    Render the User Management tab.
    Allows viewing users, changing roles, and deleting users.
    """
    st.subheader("👥 User Management")
    
    # Security check - double check just in case
    if st.session_state.get('role') != 'super_admin':
        st.warning("⚠️ User Management is restricted to Super Admins.")
        return

    # Fetch all users
    users = db.get_all_users()
    
    if not users:
        st.info("No users found.")
        return

    # Convert to DataFrame for display
    df = pd.DataFrame(users)
    
    # Display summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users", len(users))
    with col2:
        admin_count = len([u for u in users if u['role'] in ('admin', 'super_admin')])
        st.metric("Admins", admin_count)
    with col3:
        active_count = len([u for u in users if u['is_active']])
        st.metric("Active Users", active_count)

    st.divider()

    # User List with Actions
    st.subheader("User Directory")
    
    for user in users:
        with st.expander(f"{user['full_name']} (@{user['username']}) - {user['role'].upper()}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Email:** {user['email']}")
                st.write(f"**Role:** {user['role']}")
                st.write(f"**Status:** {'Active' if user['is_active'] else 'Inactive'}")
                st.write(f"**Last Login:** {user['last_login']}")
                st.write(f"**Joined:** {user['created_at']}")
            
            with col2:
                # Actions
                current_role = user['role']
                user_id = user['id']
                
                # Prevent modifying self
                if user_id == st.session_state.user_id:
                    st.info("You cannot modify your own account here.")
                    continue
                
                # Prevent modifying other Super Admins (optional, but good practice)
                if current_role == 'super_admin':
                    st.warning("Cannot modify other Super Admins.")
                    continue

                st.write("### Actions")
                
                # Role Management
                new_role = st.selectbox(
                    "Change Role",
                    options=['user', 'admin', 'super_admin'],
                    index=['user', 'admin', 'super_admin'].index(current_role) if current_role in ['user', 'admin', 'super_admin'] else 0,
                    key=f"role_select_{user_id}"
                )
                
                if new_role != current_role:
                    if st.button(f"Update Role to {new_role}", key=f"update_role_{user_id}"):
                        if db.update_user_role(user_id, new_role):
                            st.success(f"Updated {user['username']} to {new_role}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to update role")

                st.divider()
                
                # Delete User
                if user['is_active']:
                    if st.button("🗑️ Delete User", key=f"delete_{user_id}", type="primary"):
                        if db.delete_user(user_id):
                            st.success(f"User {user['username']} deactivated")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to delete user")
                else:
                    st.info("User is already inactive")
