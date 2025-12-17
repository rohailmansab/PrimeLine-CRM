import getpass
from database import Database
from auth_handler import AuthHandler
import sys

def create_super_admin():
    print("=== Create SUPER ADMIN User ===")
    
    # Hardcoded credentials for easy setup
    username = "superadmin"
    email = "superadmin@primeline.com"
    full_name = "Super Admin"
    password = "admin123"  # Default password
    
    print(f"Creating user with:")
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")

    # Initialize DB
    db = Database()
    
    # Check if user exists
    conn = db.get_connection()
    try:
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing_user = c.fetchone()
        
        if existing_user:
            print(f"\n⚠️ User '{username}' already exists. Updating to Super Admin...")
            c.execute("UPDATE users SET role = 'super_admin', is_admin = 1 WHERE username = ?", (username,))
            conn.commit()
            print("✅ User updated to Super Admin successfully!")
        else:
            # Hash password
            password_hash = AuthHandler.hash_password(password)
            
            # Insert super admin user
            c.execute('''INSERT INTO users (username, email, password_hash, full_name, is_active, is_admin, role)
                        VALUES (?, ?, ?, ?, 1, 1, 'super_admin')''',
                     (username, email, password_hash, full_name))
            conn.commit()
            print(f"\n✅ Super Admin user '{username}' created successfully!")
            
        print("\n👉 Login with these credentials to access User Management.")
        
    except Exception as e:
        print(f"Error creating super admin: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_super_admin()
