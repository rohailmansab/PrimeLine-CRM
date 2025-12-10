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
    Render professional login page
    Returns: True if login successful, False otherwise
    """
    render_auth_styles()
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        st.markdown("""
        <div class="auth-container">
            <div class="auth-header">
                <h1 class="auth-title">PrimeLine Flooring</h1>
                <h4 class="auth-subtitle">Smart Flooring Solutions through Artificial Intelligence</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="auth-form">', unsafe_allow_html=True)
        
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
                    
                    st.success(f"✅ Welcome back, {user['full_name']}!")
                    st.toast(f"Logged in as {user['username']}", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {session_result.get('error', 'Unknown error')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Switch to signup
        st.markdown("""
        <div class="auth-link">
            Don't have an account? <a href="#" onclick="document.querySelector('[data-testid=stRadio]').click()">Sign up here</a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<br><p style="text-align: center; font-size: 12px; color: #999;">🔒 Your data is secure and encrypted</p>', unsafe_allow_html=True)
    
    return False


def render_signup_page(db: Database) -> bool:
    """
    Render professional sign-up page
    Returns: True if signup successful, False otherwise
    """
    render_auth_styles()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="auth-container">
            <div class="auth-header">
                <h1 class="auth-title">PrimeLine Flooring</h1>
                <h4 class="auth-subtitle">Smart Flooring Solutions through Artificial Intelligence</h4>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="auth-form">', unsafe_allow_html=True)
        
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
                
                # Hash password
                password_hash = AuthHandler.hash_password(password)
                
                # Register user
                result = db.register_user(username, email, password_hash, full_name)
                
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
                        
                        st.success(f"✅ Welcome to PrimeLine, {full_name}!")
                        st.toast("Account created successfully!", icon="🎉")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error(f"❌ {result.get('error', 'Registration failed')}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Switch to login
        st.markdown("""
        <div class="auth-link">
            Already have an account? <a href="#" onclick="document.querySelector('[data-testid=stRadio]').click()">Sign in here</a>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<br><p style="text-align: center; font-size: 12px; color: #999;">🔒 Your data is secure and encrypted</p>', unsafe_allow_html=True)
    
    return False


def render_authentication_gate(db: Database):
    """
    Main authentication gate - blocks access to app until user is authenticated
    """
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.session_token = None
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.email = None
        st.session_state.full_name = None
        st.session_state.remember_me = False
    
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
    
    if not st.session_state.authenticated:
        st.set_page_config(
            page_title="PrimeLine - Sign In",
            page_icon="🏢",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Show authentication UI
        st.markdown("""
        <style>
            /* Hide sidebar for auth pages */
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Choice between login and signup
        auth_choice = st.radio(
            "Choose an option:",
            ["Sign In", "Sign Up"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if auth_choice == "Sign In":
            render_login_page(db)
        else:
            render_signup_page(db)
        
        return False  # Access denied
    
    return True  # Access granted
