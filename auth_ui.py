"""
Professional Login & Sign-Up UI Module
Creates stunning, responsive authentication pages with Streamlit
"""

import streamlit as st
from auth_handler import AuthHandler
from database import Database
import time


def render_auth_styles():
    """Apply professional styling to auth pages"""
    st.markdown("""
    <style>
        /* Main Container Styling */
        .auth-container {
            max-width: 450px;
            margin: 0 auto;
        }
        
        /* Header Styling */
        .auth-header {
            text-align: center;
            margin-bottom: 0px;
        }
        
        .auth-title {
            font-size: 42px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: auto;
        }
        
        .auth-subtitle {
            font-size: 14px;
            color: #666;
            margin: 0;
        }
        
        /* Form Container */
        .auth-form {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.1);
            border: 1px solid rgba(102, 126, 234, 0.1);
        }
        
        /* Input Styling */
        .stTextInput input, .stTextInput password {
            border-radius: 8px !important;
            border: 2px solid #e0e0e0 !important;
            padding: 12px 16px !important;
            font-size: 14px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        .stTextInput input:focus, .stTextInput password:focus {
            border-color: #667eea !important;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
        }
        
        /* Checkbox Styling */
        .stCheckbox {
            margin: 16px 0 !important;
        }
        
        .stCheckbox label {
            font-size: 14px !important;
            color: #333 !important;
        }
        
        /* Button Styling */
        .stButton > button {
            width: 100%;
            padding: 12px 24px !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            letter-spacing: 0.5px !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6) !important;
        }
        
        .stButton > button:active {
            transform: translateY(0) !important;
        }
        
        /* Secondary Button */
        .secondary-button {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%) !important;
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4) !important;
        }
        
        .secondary-button:hover {
            box-shadow: 0 6px 25px rgba(245, 87, 108, 0.6) !important;
        }
        
        /* Link Styling */
        .auth-link {
            text-align: center;
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
        
        .auth-link a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.3s;
        }
        
        .auth-link a:hover {
            color: #764ba2;
            text-decoration: underline;
        }
        
        /* Error/Success Messages */
        .error-message {
            background-color: #fee;
            border-left: 4px solid #f44;
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 14px;
            color: #d32f2f;
        }
        
        .success-message {
            background-color: #efe;
            border-left: 4px solid #4f4;
            padding: 12px 16px;
            border-radius: 4px;
            margin-bottom: 16px;
            font-size: 14px;
            color: #2e7d32;
        }
        
        /* Password Requirements */
        .password-requirements {
            background-color: #f5f7fa;
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
            font-size: 13px;
        }
        
        .requirement-item {
            display: flex;
            align-items: center;
            margin: 8px 0;
            color: #666;
        }
        
        .requirement-check {
            margin-right: 10px;
            font-weight: bold;
        }
        
        /* Divider */
        .auth-divider {
            text-align: center;
            margin: 24px 0;
            position: relative;
        }
        
        .auth-divider::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 1px;
            background-color: #e0e0e0;
        }
        
        .auth-divider span {
            background-color: white;
            padding: 0 12px;
            color: #999;
            font-size: 13px;
            position: relative;
        }
    </style>
    """, unsafe_allow_html=True)


def render_login_page(db: Database) -> bool:
    """
    STEP 2: Render professional login page
    Returns: True if login successful, False otherwise
    """
    render_auth_styles()
    
    # Add fade-in animation for smooth entry
    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
            animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("""
        <div class="auth-container fade-in">
            <div class="auth-header">
                <h1 class="auth-title">PrimeLine Flooring</h1>
                <h4 class="auth-subtitle">Smart Flooring Solutions through Artificial Intelligence</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="auth-form fade-in">', unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Sign In", divider="rainbow")
            
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                help="Your unique username"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Your secure password"
            )
            
            remember_me = st.checkbox("Remember me (30 days)", value=False)
            
            # Submit button
            submitted = st.form_submit_button(
                "🔓 Sign In",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                # Validate inputs
                is_valid, error = AuthHandler.validate_login_inputs(username, password)
                if not is_valid:
                    st.error(f"❌ {error}")
                    return False
                
                # Get user from database
                user = db.get_user_by_username(username)
                if not user:
                    st.error("❌ Username or password incorrect")
                    return False
                
                # Verify password
                if not AuthHandler.verify_password(password, user['password_hash']):
                    st.error("❌ Username or password incorrect")
                    return False
                
                # Create session
                session_token = AuthHandler.generate_session_token()
                session_result = db.create_session(
                    user['id'],
                    session_token,
                    remember_me=remember_me
                )
                
                if session_result['success']:
                    # Store in session state
                    st.session_state.authenticated = True
                    st.session_state.session_token = session_token
                    st.session_state.user_id = user['id']
                    st.session_state.username = user['username']
                    st.session_state.email = user['email']
                    st.session_state.full_name = user['full_name']
                    st.session_state.remember_me = remember_me
                    
                    # Load role and admin status
                    role = user.get('role', 'user')
                    st.session_state.role = role
                    st.session_state.is_admin = role in ('admin', 'super_admin') or bool(user.get('is_admin', 0))
                    
                    st.success(f"✅ Welcome back, {user['full_name']}!")
                    st.toast(f"Logged in as {user['username']}", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {session_result.get('error', 'Unknown error')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<br><p style="text-align: center; font-size: 12px; color: #999;">🔒 Your data is secure and encrypted</p>', unsafe_allow_html=True)
    
    return False


def render_signup_page(db: Database) -> bool:
    """
    STEP 2: Render professional sign-up page
    Returns: True if signup successful, False otherwise
    """
    render_auth_styles()
    
    # Add fade-in animation for smooth entry
    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
            animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="auth-container fade-in">
            <div class="auth-header">
                <h1 class="auth-title">PrimeLine Flooring</h1>
                <h4 class="auth-subtitle">Smart Flooring Solutions through Artificial Intelligence</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="auth-form fade-in">', unsafe_allow_html=True)
        
        # Signup form
        with st.form("signup_form", clear_on_submit=False):
            st.subheader("Create Account", divider="rainbow")
            
            full_name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                help="Your complete name"
            )
            
            username = st.text_input(
                "Username",
                placeholder="Choose a username (3-30 characters)",
                help="Letters, numbers, underscores, hyphens only"
            )
            
            email = st.text_input(
                "Email",
                placeholder="Enter your email address",
                help="Valid email address"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a strong password",
                help="Min 8 chars with uppercase, lowercase, digit, special char"
            )
            
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Re-enter your password",
                help="Must match password above"
            )
            
            # Show password requirements
            with st.expander("📋 Password Requirements", expanded=False):
                requirements = AuthHandler.get_password_strength_requirements()
                for key, requirement in requirements.items():
                    st.caption(f"✓ {requirement}")
            
            # Admin Code (Optional)
            admin_code = st.text_input(
                "Admin Code (Optional)",
                type="password",
                placeholder="Enter admin code if applicable",
                help="Leave blank if you are not an admin"
            )
            
            agree_terms = st.checkbox("I agree to the Terms of Service and Privacy Policy", value=False)
            
            submitted = st.form_submit_button(
                "✨ Create Account",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not agree_terms:
                    st.error("❌ Please agree to the Terms of Service")
                    return False
                
                # Validate all inputs
                is_valid, error = AuthHandler.validate_signup_inputs(
                    username, email, password, confirm_password, full_name
                )
                
                if not is_valid:
                    st.error(f"❌ {error}")
                    return False
                
                # Check admin/super admin code
                is_admin_signup = False
                is_super_admin_signup = False
                
                if admin_code:
                    if admin_code == "admin123":  # Simple hardcoded check for now
                        is_admin_signup = True
                        st.toast("Admin privileges granted!", icon="👑")
                    elif admin_code == "supersecret2025": # Super Admin Code
                        is_super_admin_signup = True
                        st.toast("Super Admin privileges granted!", icon="🚀")
                    else:
                        st.warning("⚠️ Invalid Admin Code - Account will be created as standard user")
                
                # Hash password
                password_hash = AuthHandler.hash_password(password)
                
                # Register user
                result = db.register_user(username, email, password_hash, full_name)
                
                if result['success']:
                    # If admin code was valid, update the user role immediately
                    if is_super_admin_signup:
                        try:
                            conn = db.get_connection()
                            c = conn.cursor()
                            c.execute("UPDATE users SET role = 'super_admin', is_admin = 1 WHERE id = ?", (result['user_id'],))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            print(f"Error promoting user to super admin: {e}")
                    elif is_admin_signup:
                        try:
                            conn = db.get_connection()
                            c = conn.cursor()
                            c.execute("UPDATE users SET role = 'admin', is_admin = 1 WHERE id = ?", (result['user_id'],))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            print(f"Error promoting user to admin: {e}")
                
                if result['success']:
                    # Auto-login after signup
                    user = db.get_user_by_username(username)
                    session_token = AuthHandler.generate_session_token()
                    session_result = db.create_session(user['id'], session_token, remember_me=True)
                    
                    if session_result['success']:
                        st.session_state.authenticated = True
                        st.session_state.session_token = session_token
                        st.session_state.user_id = user['id']
                        st.session_state.username = user['username']
                        st.session_state.email = user['email']
                        st.session_state.full_name = user['full_name']
                        st.session_state.remember_me = True
                        
                        # Load role and admin status
                        role = user.get('role', 'user')
                        st.session_state.role = role
                        st.session_state.is_admin = role in ('admin', 'super_admin') or bool(user.get('is_admin', 0))
                        
                        st.success(f"✅ Welcome to PrimeLine, {full_name}!")
                        st.toast("Account created successfully!", icon="🎉")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error(f"❌ {result.get('error', 'Registration failed')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<br><p style="text-align: center; font-size: 12px; color: #999;">🔒 Your data is secure and encrypted</p>', unsafe_allow_html=True)
    
    return False


def render_landing_page():
    """
    STEP 1: Landing page with Sign In / Sign Up buttons
    Clean, minimal interface with two action buttons
    """
    render_auth_styles()
    
    # Add fade-in animation CSS
    st.markdown("""
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .fade-in {
            animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .landing-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 60px 20px;
            text-align: center;
        }
        
        .landing-logo {
            font-size: 80px;
            margin-bottom: 20px;
        }
        
        .landing-title {
            font-size: 48px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
        }
        
        .landing-subtitle {
            font-size: 16px;
            color: #666;
            margin-bottom: 50px;
            line-height: 1.6;
        }
        
        .button-container {
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-top: 40px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="landing-container fade-in">
            <div class="landing-logo">🏢</div>
            <h1 class="landing-title">PrimeLine Flooring</h1>
            <p class="landing-subtitle">
                Smart Flooring Solutions through Artificial Intelligence<br>
                Welcome to the future of flooring management
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="button-container fade-in">', unsafe_allow_html=True)
        
        # Sign In Button
        if st.button("🔓 Sign In", key="landing_signin", use_container_width=True, type="primary"):
            st.session_state.auth_flow_step = "signin"
            st.rerun()
        
        # Sign Up Button
        if st.button("✨ Create Account", key="landing_signup", use_container_width=True, type="secondary"):
            st.session_state.auth_flow_step = "signup"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<br><p style="text-align: center; font-size: 12px; color: #999;">🔒 Your data is secure and encrypted</p>', unsafe_allow_html=True)


def render_authentication_gate(db: Database):
    """
    Main authentication gate - blocks access to app until user is authenticated
    
    HIERARCHICAL 3-STEP FLOW:
    -------------------------
    Step 1 (Landing Page): User sees only "Sign In" | "Sign Up" buttons
    Step 2 (Form Page): User sees only the selected form (login OR signup)
    Step 3 (Navigation): User can click "Back to Auth Options" to return to Step 1
    
    This design eliminates the radio button and provides smooth, intentional navigation
    between authentication states with fade-in animations and proper state management.
    """
    # Initialize session state for authentication
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.session_token = None
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.full_name = None
        st.session_state.remember_me = False
    
    # Initialize auth flow state (landing, signin, signup)
    if 'auth_flow_step' not in st.session_state:
        st.session_state.auth_flow_step = "landing"
    
    # Validate existing session token
    if st.session_state.authenticated and st.session_state.session_token:
        session_valid = db.validate_session(st.session_state.session_token)
        if session_valid['valid']:
            return True  # Session is valid, allow access
        else:
            # Session expired or invalid
            st.session_state.authenticated = False
            st.session_state.session_token = None
            st.warning(f"⚠️ Session expired: {session_valid.get('error', 'Unknown error')}")
            time.sleep(2)
            st.rerun()
    
    # User is not authenticated - show auth flow
    if not st.session_state.authenticated:
        st.set_page_config(
            page_title="PrimeLine - Sign In",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Hide sidebar for auth pages
        st.markdown("""
        <style>
            /* Hide sidebar for auth pages */
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # STEP 1: Landing Page - Show only if user hasn't selected an option
        if st.session_state.auth_flow_step == "landing":
            render_landing_page()
        
        # STEP 2: Sign In Form - Show only login form
        elif st.session_state.auth_flow_step == "signin":
            # Add back button at the top
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("← Back to Auth Options", key="back_from_signin"):
                    st.session_state.auth_flow_step = "landing"
                    st.rerun()
            
            render_login_page(db)
        
        # STEP 3: Sign Up Form - Show only signup form
        elif st.session_state.auth_flow_step == "signup":
            # Add back button at the top
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("← Back to Auth Options", key="back_from_signup"):
                    st.session_state.auth_flow_step = "landing"
                    st.rerun()
            
            render_signup_page(db)
        
        return False  # Access denied
    
    return True  # Access granted
