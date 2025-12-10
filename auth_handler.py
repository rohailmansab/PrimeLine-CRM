"""
Professional Authentication Handler Module
Handles password security, user registration, login validation, and session management
"""

import hashlib
import secrets
import re
from datetime import datetime
from typing import Dict, Tuple, Optional


class AuthHandler:
    """
    Enterprise-grade authentication handler with:
    - Secure password hashing (using PBKDF2)
    - Session token generation
    - Input validation
    - Security best practices
    """
    
    # Password security configuration
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGITS = True
    PASSWORD_REQUIRE_SPECIAL = True
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Session configuration
    SESSION_TOKEN_LENGTH = 32
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using PBKDF2 with SHA-256
        Returns: salt$hash format for easy verification
        """
        salt = secrets.token_hex(16)  # 32-char hex string (16 bytes)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        password_hash = hash_obj.hex()
        return f"{salt}${password_hash}"
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify password against stored hash
        Returns: True if password matches, False otherwise
        """
        try:
            salt, stored_hash = password_hash.split('$')
            hash_obj = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            computed_hash = hash_obj.hex()
            return computed_hash == stored_hash
        except Exception as e:
            print(f"Password verification error: {str(e)}")
            return False
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate username format
        Returns: (is_valid, error_message)
        """
        if not username:
            return False, "Username is required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        
        if len(username) > 30:
            return False, "Username must not exceed 30 characters"
        
        # Username: alphanumeric, underscores, hyphens only
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"
        
        return True, ""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate email format
        Returns: (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Please enter a valid email address"
        
        if len(email) > 100:
            return False, "Email is too long"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
        
        if len(password) < AuthHandler.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {AuthHandler.PASSWORD_MIN_LENGTH} characters"
        
        if len(password) > 128:
            return False, "Password is too long"
        
        if AuthHandler.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if AuthHandler.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if AuthHandler.PASSWORD_REQUIRE_DIGITS and not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if AuthHandler.PASSWORD_REQUIRE_SPECIAL and not re.search(rf'[{re.escape(AuthHandler.SPECIAL_CHARS)}]', password):
            return False, "Password must contain at least one special character"
        
        return True, ""
    
    @staticmethod
    def validate_full_name(full_name: str) -> Tuple[bool, str]:
        """
        Validate full name format
        Returns: (is_valid, error_message)
        """
        if not full_name or not full_name.strip():
            return False, "Full name is required"
        
        if len(full_name) < 2:
            return False, "Full name must be at least 2 characters"
        
        if len(full_name) > 100:
            return False, "Full name is too long"
        
        # Allow letters, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s'-]+$", full_name):
            return False, "Full name can only contain letters, spaces, hyphens, and apostrophes"
        
        return True, ""
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate a secure random session token"""
        return secrets.token_urlsafe(AuthHandler.SESSION_TOKEN_LENGTH)
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """Basic input sanitization"""
        return str(input_str).strip()
    
    @staticmethod
    def get_password_strength_requirements() -> Dict[str, str]:
        """Return password requirements for UI display"""
        return {
            "min_length": f"At least {AuthHandler.PASSWORD_MIN_LENGTH} characters",
            "uppercase": "At least one uppercase letter (A-Z)",
            "lowercase": "At least one lowercase letter (a-z)",
            "digits": "At least one digit (0-9)",
            "special": f"At least one special character ({AuthHandler.SPECIAL_CHARS})"
        }
    
    @staticmethod
    def validate_signup_inputs(username: str, email: str, password: str, 
                               confirm_password: str, full_name: str) -> Tuple[bool, str]:
        """
        Validate all signup inputs at once
        Returns: (is_valid, error_message)
        """
        # Sanitize inputs
        username = AuthHandler.sanitize_input(username)
        email = AuthHandler.sanitize_input(email)
        full_name = AuthHandler.sanitize_input(full_name)
        
        # Validate username
        is_valid, error = AuthHandler.validate_username(username)
        if not is_valid:
            return False, error
        
        # Validate email
        is_valid, error = AuthHandler.validate_email(email)
        if not is_valid:
            return False, error
        
        # Validate full name
        is_valid, error = AuthHandler.validate_full_name(full_name)
        if not is_valid:
            return False, error
        
        # Validate password
        is_valid, error = AuthHandler.validate_password(password)
        if not is_valid:
            return False, error
        
        # Confirm password matches
        if password != confirm_password:
            return False, "Passwords do not match"
        
        return True, ""
    
    @staticmethod
    def validate_login_inputs(username: str, password: str) -> Tuple[bool, str]:
        """
        Validate login inputs
        Returns: (is_valid, error_message)
        """
        username = AuthHandler.sanitize_input(username)
        
        if not username:
            return False, "Username is required"
        
        if not password:
            return False, "Password is required"
        
        return True, ""
