import getpass
from database import Database
from auth_handler import AuthHandler
import sys

def create_admin():
    print("=== Create Admin User ===")
    
    # Get inputs
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    full_name = input("Full Name: ").strip()
    password = getpass.getpass("Password: ")
    confirm_password = getpass.getpass("Confirm Password: ")
    
    # Validate inputs
    if password != confirm_password:
        print("Error: Passwords do not match!")
        return
    
    is_valid, error = AuthHandler.validate_password(password)
    if not is_valid:
        print(f"Error: {error}")
        return

    # Initialize DB
    db = Database()
    
    # Check if user exists
    conn = db.get_connection()
    try:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        if c.fetchone():
            print("Error: Username or email already exists!")
            return
            
        # Hash password
        password_hash = AuthHandler.hash_password(password)
        
        # Insert admin user
        c.execute('''INSERT INTO users (username, email, password_hash, full_name, is_active, is_admin)
                    VALUES (?, ?, ?, ?, 1, 1)''',
                 (username, email, password_hash, full_name))
        conn.commit()
        print(f"\n✅ Admin user '{username}' created successfully!")
        
    except Exception as e:
        print(f"Error creating admin: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_admin()
