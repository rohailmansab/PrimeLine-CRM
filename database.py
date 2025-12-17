import sqlite3
from datetime import datetime
import os
import time
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str = 'data/crm.db'):
        self.db_path = db_path
        self._ensure_data_dir()
        self.init_db()
        
    def _ensure_data_dir(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn
    
    @contextmanager
    def get_db_context(self):
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # Users table - optimized for authentication
            c.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                         email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                         password_hash TEXT NOT NULL,
                         full_name TEXT,
                         is_active INTEGER DEFAULT 1,
                         is_admin INTEGER DEFAULT 0,
                         role TEXT DEFAULT 'user',
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         last_login TIMESTAMP)''')
            
            # Sessions table - optimized for session management
            c.execute('''CREATE TABLE IF NOT EXISTS sessions
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_id INTEGER NOT NULL,
                         session_token TEXT NOT NULL UNIQUE,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         expires_at TIMESTAMP NOT NULL,
                         last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         ip_address TEXT,
                         user_agent TEXT,
                         remember_me INTEGER DEFAULT 0,
                         is_active INTEGER DEFAULT 1,
                         FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)''')
            
            # Create indexes for performance
            c.execute('''CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)''')
            c.execute('''CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)''')
            
            # Customers table
            c.execute('''CREATE TABLE IF NOT EXISTS customers
                        (id CHAR(32) PRIMARY KEY,
                         full_name VARCHAR(255) NOT NULL,
                         email VARCHAR(255) NOT NULL,
                         phone VARCHAR(50),
                         location VARCHAR(255),
                         notes TEXT,
                         is_deleted BOOLEAN DEFAULT 0,
                         deleted_at DATETIME,
                         created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                         updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                         user_id INTEGER,
                         business_name TEXT,
                         zip_code TEXT,
                         customer_type TEXT DEFAULT 'contractor',
                         FOREIGN KEY(user_id) REFERENCES users(id))''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS products
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL,
                         width TEXT NOT NULL,
                         description TEXT,
                         category TEXT DEFAULT 'Hardwood',
                         cost_price REAL DEFAULT 0.0,
                         standard_price REAL DEFAULT 0.0,
                         min_qty_discount INTEGER,
                         discount_percentage REAL,
                         discount_type TEXT,
                         promotion_name TEXT,
                         promotion_start_date TIMESTAMP,
                         promotion_end_date TIMESTAMP,
                         volume_discounts TEXT,
                         updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                         
            c.execute('''CREATE TABLE IF NOT EXISTS suppliers
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT NOT NULL UNIQUE,
                         email TEXT NOT NULL UNIQUE,
                         contact_info TEXT,
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                         
            c.execute('''CREATE TABLE IF NOT EXISTS price_requests
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         supplier_id INTEGER,
                         status TEXT DEFAULT 'pending',
                         sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         response_data TEXT,
                         FOREIGN KEY(supplier_id) REFERENCES suppliers(id))''')
                         
            c.execute('''CREATE TABLE IF NOT EXISTS quotes
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         customer_name TEXT NOT NULL,
                         location TEXT NOT NULL,
                         product_specs TEXT NOT NULL,
                         quantity INTEGER,
                         final_price REAL,
                         user_id INTEGER,
                         status TEXT DEFAULT 'pending_admin_approval',
                         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         FOREIGN KEY(user_id) REFERENCES users(id))''')
            
            # Migration: Add is_admin column to existing users table if it doesn't exist
            try:
                c.execute("SELECT is_admin FROM users LIMIT 1")
            except:
                c.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
                print("✓ Added is_admin column to users table")

            # Migration: Add role column to existing users table if it doesn't exist
            try:
                c.execute("SELECT role FROM users LIMIT 1")
            except:
                c.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
                print("✓ Added role column to users table")
                
                # Backfill role based on is_admin
                c.execute("UPDATE users SET role = 'admin' WHERE is_admin = 1")
                conn.commit()
                print("✓ Backfilled role column based on is_admin status")
            
            # Migration: Add user_id column to existing quotes table if it doesn't exist
            try:
                c.execute("SELECT user_id FROM quotes LIMIT 1")
            except:
                c.execute("ALTER TABLE quotes ADD COLUMN user_id INTEGER REFERENCES users(id)")
                print("✓ Added user_id column to quotes table")

            # Migration: Add status column to existing quotes table if it doesn't exist
            try:
                c.execute("SELECT status FROM quotes LIMIT 1")
            except:
                c.execute("ALTER TABLE quotes ADD COLUMN status TEXT DEFAULT 'pending_admin_approval'")
                print("✓ Added status column to quotes table")
                
                # Backfill status for existing quotes to 'approved' (assuming old quotes are valid)
                c.execute("UPDATE quotes SET status = 'approved' WHERE status = 'pending_admin_approval'")
                conn.commit()
                print("✓ Backfilled status column for existing quotes")
            
            # Migration: Add business_name column to customers table
            try:
                c.execute("SELECT business_name FROM customers LIMIT 1")
            except:
                c.execute("ALTER TABLE customers ADD COLUMN business_name TEXT")
                print("✓ Added business_name column to customers table")

            # Migration: Add zip_code column to customers table
            try:
                c.execute("SELECT zip_code FROM customers LIMIT 1")
            except:
                c.execute("ALTER TABLE customers ADD COLUMN zip_code TEXT")
                print("✓ Added zip_code column to customers table")
                
                # Migrate location to zip_code (naive migration)
                c.execute("UPDATE customers SET zip_code = location WHERE location IS NOT NULL")
                print("✓ Migrated location to zip_code")

            # Migration: Add customer_type column to customers table
            try:
                c.execute("SELECT customer_type FROM customers LIMIT 1")
            except:
                c.execute("ALTER TABLE customers ADD COLUMN customer_type TEXT DEFAULT 'contractor'")
                print("✓ Added customer_type column to customers table")
            
            # Migration: Ensure email is unique
            try:
                c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_email ON customers(email)")
            except Exception as e:
                print(f"Note: Could not create unique index on customers email: {e}")

            # Create customer_interactions table
            c.execute('''CREATE TABLE IF NOT EXISTS customer_interactions
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     customer_id TEXT NOT NULL,
                     user_id INTEGER,
                     status TEXT NOT NULL,
                     notes TEXT,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                     FOREIGN KEY (customer_id) REFERENCES customers(id),
                     FOREIGN KEY (user_id) REFERENCES users(id))''')
            
            # Create index for quote user_id filtering
            c.execute('''CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id)''')
            
            # Migration: Add user_id column to existing customers table if it doesn't exist
            # Check if table exists first (since it might be managed by SQLAlchemy)
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers'")
            if c.fetchone():
                try:
                    c.execute("SELECT user_id FROM customers LIMIT 1")
                except:
                    c.execute("ALTER TABLE customers ADD COLUMN user_id INTEGER REFERENCES users(id)")
                    print("✓ Added user_id column to customers table")
            
            # Migration: Add is_active column to suppliers table if it doesn't exist
            try:
                c.execute("SELECT is_active FROM suppliers LIMIT 1")
            except:
                c.execute("ALTER TABLE suppliers ADD COLUMN is_active INTEGER DEFAULT 1")
                print("✓ Added is_active column to suppliers table")

            # Migration: Add supplier_id column to products table if it doesn't exist
            try:
                c.execute("SELECT supplier_id FROM products LIMIT 1")
            except:
                c.execute("ALTER TABLE products ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id)")
                print("✓ Added supplier_id column to products table")

            # Migration: Add AI pricing columns to quotes table
            try:
                c.execute("SELECT ai_retail_price FROM quotes LIMIT 1")
            except:
                c.execute("ALTER TABLE quotes ADD COLUMN ai_retail_price REAL")
                c.execute("ALTER TABLE quotes ADD COLUMN ai_dealer_price REAL")
                c.execute("ALTER TABLE quotes ADD COLUMN ai_zip_code TEXT")
                c.execute("ALTER TABLE quotes ADD COLUMN ai_generated_at TIMESTAMP")
                print("✓ Added AI pricing columns to quotes table")

            # Sync History table for automated tasks
            c.execute('''CREATE TABLE IF NOT EXISTS sync_history
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         sync_type TEXT NOT NULL,
                         supplier_id INTEGER,
                         status TEXT NOT NULL,
                         message TEXT,
                         timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                         FOREIGN KEY(supplier_id) REFERENCES suppliers(id))''')
            
            conn.commit()
        finally:
            conn.close()

    # ... (skipping unchanged methods)

    def update_product_price(self, name: str, new_price: float, width: str = None, 
                           discount_percentage: float = None, min_qty: int = None,
                           promotion_name: str = None, volume_discounts: str = None,
                           supplier_id: int = None) -> bool:
        """Update product price and optional promotion details"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # Check if product exists
            if width:
                c.execute("SELECT id FROM products WHERE name = ? AND width = ?", (name, width))
            else:
                c.execute("SELECT id FROM products WHERE name = ?", (name,))
                
            if not c.fetchone():
                print(f"Product not found: {name} {width or ''}")
                return False
            
            # Update price
            if width:
                if discount_percentage is not None:
                    query = '''UPDATE products 
                              SET standard_price = ?, cost_price = ?, 
                                  discount_percentage = ?, min_qty_discount = ?,
                                  promotion_name = ?, volume_discounts = ?,
                                  updated_at = CURRENT_TIMESTAMP'''
                    params = [new_price, new_price * 0.7 if discount_percentage else new_price,
                             discount_percentage, min_qty, promotion_name, volume_discounts]
                    
                    if supplier_id:
                        query += ", supplier_id = ?"
                        params.append(supplier_id)
                        
                    query += " WHERE name = ? AND width = ?"
                    params.extend([name, width])
                    
                    c.execute(query, tuple(params))
                else:
                    query = '''UPDATE products 
                              SET standard_price = ?, cost_price = ?, updated_at = CURRENT_TIMESTAMP'''
                    params = [new_price, new_price]
                    
                    if supplier_id:
                        query += ", supplier_id = ?"
                        params.append(supplier_id)
                        
                    query += " WHERE name = ? AND width = ?"
                    params.extend([name, width])
                    
                    c.execute(query, tuple(params))
            else:
                # Similar logic for no width (omitted for brevity as width is usually present)
                pass
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Database error in update_product_price: {str(e)}")
            return False
        finally:
            conn.close()

    def get_products(self):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT p.id, p.name, p.width, p.description, p.category, p.cost_price, p.standard_price, 
                                p.discount_percentage, p.min_qty_discount, p.promotion_name, 
                                p.promotion_start_date, p.promotion_end_date, p.volume_discounts, p.updated_at,
                                s.name as supplier_name
                        FROM products p
                        LEFT JOIN suppliers s ON p.supplier_id = s.id
                        ORDER BY p.name, p.width''')
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def get_active_suppliers_count(self) -> int:
        """Get count of active suppliers"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            # Handle case where is_active might not exist yet (though migration handles it)
            try:
                c.execute("SELECT COUNT(*) FROM suppliers WHERE is_active = 1")
            except:
                c.execute("SELECT COUNT(*) FROM suppliers")
            return c.fetchone()[0]
        except Exception as e:
            print(f"Error counting suppliers: {e}")
            return 0
        finally:
            conn.close()

    def get_pending_requests_count(self) -> int:
        """Get count of pending price requests"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM price_requests WHERE status = 'pending'")
            return c.fetchone()[0]
        except Exception as e:
            print(f"Error counting requests: {e}")
            return 0
        finally:
            conn.close()

    def log_sync_event(self, sync_type: str, status: str, message: str = None, supplier_id: int = None):
        """Log an automated sync event"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''INSERT INTO sync_history (sync_type, status, message, supplier_id)
                        VALUES (?, ?, ?, ?)''',
                     (sync_type, status, message, supplier_id))
            conn.commit()
        except Exception as e:
            print(f"Error logging sync event: {str(e)}")
        finally:
            conn.close()

    def get_last_sync(self, sync_type: str):
        """Get the last successful sync event for a given type"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT timestamp, status, message FROM sync_history 
                        WHERE sync_type = ? AND status = 'success'
                        ORDER BY timestamp DESC LIMIT 1''', (sync_type,))
            result = c.fetchone()
            return dict(result) if result else None
        finally:
            conn.close()

    def add_product(self, name: str, width: str, description: str = None, 
                   category: str = "Hardwood", cost_price: float = 0.0,
                   standard_price: float = 0.0, min_qty_discount: int = None,
                   discount_percentage: float = None, discount_type: str = None,
                   promotion_name: str = None, promotion_start_date: str = None,
                   promotion_end_date: str = None, volume_discounts: str = None) -> int:
        conn = self.get_connection()
        try:
            c = conn.cursor()
            width_str = str(width).strip()
            if width_str and not width_str.endswith('"'):
                width_str = f'{width_str}"'
            
            std_price = standard_price if standard_price > 0 else cost_price
            
            c.execute('''INSERT INTO products (name, width, description, category, cost_price, standard_price,
                                               min_qty_discount, discount_percentage, discount_type,
                                               promotion_name, promotion_start_date, promotion_end_date, volume_discounts)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (name.strip(), width_str, description, category, float(cost_price), float(std_price),
                      min_qty_discount, discount_percentage, discount_type,
                      promotion_name, promotion_start_date, promotion_end_date, volume_discounts))
            conn.commit()
            result = c.lastrowid
            return result
        finally:
            conn.close()

    def add_supplier(self, name: str, email: str, contact_info: str = None) -> int:
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''INSERT INTO suppliers (name, email, contact_info)
                        VALUES (?, ?, ?)''',
                     (name.strip(), email.strip(), contact_info))
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()





    def is_promotion_active(self, promotion_start_date: str, promotion_end_date: str) -> bool:
        """Check if promotion is currently active based on dates"""
        try:
            if not promotion_start_date or not promotion_end_date:
                return False
            
            current_date = datetime.now()
            
            # Parse dates - handle various formats
            start = datetime.fromisoformat(promotion_start_date.split()[0] if ' ' in promotion_start_date else promotion_start_date)
            end = datetime.fromisoformat(promotion_end_date.split()[0] if ' ' in promotion_end_date else promotion_end_date)
            
            # Set end time to end of day
            end = end.replace(hour=23, minute=59, second=59)
            
            is_active = start <= current_date <= end
            return is_active
        except Exception as e:
            print(f"Error checking promotion activity: {str(e)}")
            return False

    def get_promotion_days_remaining(self, promotion_end_date: str) -> int:
        """Calculate days remaining for a promotion"""
        try:
            if not promotion_end_date:
                return 0
            
            current_date = datetime.now()
            end = datetime.fromisoformat(promotion_end_date.split()[0] if ' ' in promotion_end_date else promotion_end_date)
            
            days_remaining = (end - current_date).days
            return max(0, days_remaining)
        except Exception as e:
            print(f"Error calculating promotion days: {str(e)}")
            return 0

    def get_suppliers(self):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT id, name, email, contact_info, created_at 
                        FROM suppliers ORDER BY name''')
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def create_quote(self, customer_name, location, product_specs, quantity, total_price, user_id=None, status='pending_admin_approval',
                    ai_retail_price=None, ai_dealer_price=None, ai_zip_code=None, ai_generated_at=None):
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''INSERT INTO quotes 
                        (customer_name, location, product_specs, quantity, total_price, user_id, status,
                         ai_retail_price, ai_dealer_price, ai_zip_code, ai_generated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (customer_name, location, product_specs, quantity, total_price, user_id, status,
                       ai_retail_price, ai_dealer_price, ai_zip_code, ai_generated_at))
            conn.commit()
            return c.lastrowid
        finally:
            conn.close()

    def get_latest_quotes(self, limit: int = 50, user_id: int = None, is_admin: bool = False):
        """Get latest quotes with user filtering. Admins see all, regular users see only their quotes."""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            if is_admin or user_id is None:
                # Admin or no user specified - see all quotes
                c.execute('''SELECT id, customer_name, location, product_specs, quantity, final_price, user_id, created_at
                            FROM quotes ORDER BY created_at DESC LIMIT ?''', (limit,))
            else:
                # Regular user - see only their quotes
                c.execute('''SELECT id, customer_name, location, product_specs, quantity, final_price, user_id, created_at
                            FROM quotes WHERE user_id = ? OR user_id IS NULL
                            ORDER BY created_at DESC LIMIT ?''', (user_id, limit))
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def get_analytics_data(self, user_id: int = None, is_admin: bool = False):
        """Get comprehensive quote data for analytics, joined with customer info"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            query = '''
                SELECT 
                    q.id, 
                    q.customer_name, 
                    q.location, 
                    q.product_specs, 
                    q.quantity, 
                    q.final_price, 
                    q.created_at,
                    c.zip_code,
                    c.customer_type,
                    c.business_name
                FROM quotes q
                LEFT JOIN customers c ON q.customer_name = c.business_name OR q.customer_name = c.full_name
            '''
            
            params = []
            
            if not is_admin and user_id is not None:
                query += " WHERE q.user_id = ? OR q.user_id IS NULL"
                params.append(user_id)
                
            query += " ORDER BY q.created_at DESC"
            
            c.execute(query, params)
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def is_user_admin(self, user_id: int) -> bool:
        """Check if a user has admin privileges"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            # Check role first, fallback to is_admin flag
            c.execute("SELECT role, is_admin FROM users WHERE id = ?", (user_id,))
            result = c.fetchone()
            if not result:
                return False
            
            # If role column exists and is populated
            if 'role' in result.keys() and result['role']:
                return result['role'] in ('admin', 'super_admin')
                
            return bool(result['is_admin'])
        finally:
            conn.close()

    def is_user_super_admin(self, user_id: int) -> bool:
        """Check if a user is a super admin"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("SELECT role FROM users WHERE id = ?", (user_id,))
            result = c.fetchone()
            if not result or 'role' not in result.keys():
                return False
            return result['role'] == 'super_admin'
        finally:
            conn.close()

    def populate_sample_data(self):
        try:
            # Comprehensive mock data covering all important cases
            sample_products = [
                # Hardwood - Premium with multi-tier volume discounts
                ("White Oak", '5"', "Premium grade white oak flooring - prefinished", "Hardwood", 4.25, 4.50, 500, 10.0, "bulk", "Fall Sale 2025", "2025-11-01", "2025-11-30", "500-999 sqft: 5% off, 1000-1499 sqft: 8% off, 1500+ sqft: 10% off"),
                ("White Oak", '7"', "Wide plank white oak flooring - luxury grade", "Hardwood", 4.75, 5.00, 300, 12.0, "bulk", "Premium Wide Plank Special", "2025-11-15", "2025-12-15", "300-799 sqft: 7% off, 800-1199 sqft: 10% off, 1200+ sqft: 12% off"),
                
                # Hardwood - No promotion (edge case: NULL promotion)
                ("Red Oak", '5"', "Traditional red oak flooring - natural finish", "Hardwood", 3.85, 4.10, None, None, None, None, None, None, None),
                
                # Hardwood - Long promotion period with contractor discount
                ("Red Oak", '7"', "Classic red oak planks - hand-scraped texture", "Hardwood", 4.15, 4.40, 400, 8.0, "bulk", "Contractor Discount", "2025-11-01", "2026-01-31", "400-799 sqft: 5% off, 800-1199 sqft: 6% off, 1200+ sqft: 8% off"),
                
                # Premium Wood - No minimum quantity discount (edge case)
                ("Maple", '4"', "Select grade maple flooring - Canadian sourced", "Hardwood", 4.50, 4.85, None, None, None, None, None, None, None),
                
                # Premium Wood - High discount percentage (tiered pricing)
                ("Maple", '6"', "Wide plank maple flooring - engineered core", "Hardwood", 4.95, 5.25, 250, 15.0, "bulk", "Holiday Bundle Deal", "2025-12-01", "2025-12-31", "250-599 sqft: 8% off, 600-999 sqft: 12% off, 1000+ sqft: 15% off"),
                
                # Luxury - Ultra-premium with aggressive discounts
                ("Walnut", '5"', "Premium walnut flooring - exotic grade", "Hardwood", 5.95, 6.50, 200, 18.0, "bulk", "Luxury Flooring Promotion", "2025-11-20", "2025-12-20", "200-399 sqft: 10% off, 400-599 sqft: 14% off, 600+ sqft: 18% off"),
                
                # Luxury - Exclusive with high minimums
                ("Walnut", '7"', "Luxury wide plank walnut - hand-selected", "Hardwood", 6.75, 7.25, 150, 20.0, "bulk", "Exclusive Offer", "2025-11-01", "2025-11-30", "150-299 sqft: 12% off, 300-499 sqft: 16% off, 500+ sqft: 20% off"),
                
                # Eco-Friendly - Sustainability focus with moderate discounts
                ("Bamboo", '5"', "Sustainable bamboo flooring - LEED eligible", "Eco", 3.95, 4.25, 600, 7.0, "bulk", "Eco-Friendly Initiative", "2025-11-01", "2025-12-31", "600-999 sqft: 4% off, 1000-1499 sqft: 5% off, 1500+ sqft: 7% off"),
                
                # Eco-Friendly - Long campaign with high minimums
                ("Cork", '6"', "Natural cork planks - renewable resource", "Eco", 3.85, 4.15, 700, 9.0, "bulk", "Green Building Special", "2025-10-15", "2026-01-15", "700-999 sqft: 5% off, 1000-1499 sqft: 7% off, 1500+ sqft: 9% off"),
                
                # Budget Option - No discount (edge case: low-end pricing)
                ("Laminate", '4"', "Commercial grade laminate - high durability", "Budget", 1.95, 2.15, None, None, None, None, None, None, None),
            ]
            
            sample_suppliers = [
                ("Premium Hardwoods Inc", "sales@premiumhardwoods.com", "USA's leading hardwood supplier - established 1995"),
                ("EcoFloor Solutions", "info@ecofloorsolutions.com", "Sustainable flooring specialist - ISO certified"),
                ("Classic Woods International", "orders@classicwoods.com", "Traditional wood specialists - global sourcing"),
                ("Budget Flooring Direct", "contact@budgetflooring.com", "Cost-effective flooring solutions - bulk orders"),
                ("Luxury Imports Ltd", "premium@luxuryimports.com", "Exotic wood imports - white-glove service")
            ]
            
            conn = self.get_connection()
            try:
                c = conn.cursor()
                c.execute("DELETE FROM quotes")
                c.execute("DELETE FROM price_requests")
                c.execute("DELETE FROM products")
                c.execute("DELETE FROM suppliers")
                c.execute("DELETE FROM sqlite_sequence")
                conn.commit()
            finally:
                conn.close()
                
            # Add data with separate connections
            for product in sample_products:
                self.add_product(*product)
                
            for supplier in sample_suppliers:
                self.add_supplier(*supplier)
                    
            return True
            
        except Exception as e:
            print(f"Error populating sample data: {str(e)}")
            return False

    # ===================== AUTHENTICATION METHODS =====================
    
    def register_user(self, username: str, email: str, password_hash: str, full_name: str = None) -> dict:
        """Register a new user - returns user dict or error dict"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # Check if user already exists
            c.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username.lower(), email.lower()))
            if c.fetchone():
                return {"success": False, "error": "Username or email already exists"}
            
            c.execute('''INSERT INTO users (username, email, password_hash, full_name, is_active)
                        VALUES (?, ?, ?, ?, 1)''',
                     (username.lower(), email.lower(), password_hash, full_name))
            conn.commit()
            
            user_id = c.lastrowid
            return {"success": True, "user_id": user_id, "username": username}
            
        except Exception as e:
            return {"success": False, "error": f"Registration error: {str(e)}"}
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> dict:
        """Get user by username for login"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT id, username, email, password_hash, full_name, is_active, is_admin, role, last_login
                        FROM users WHERE username = ? AND is_active = 1''', (username.lower(),))
            result = c.fetchone()
            return dict(result) if result else None
        finally:
            conn.close()

    def get_all_users(self) -> list:
        """Get all users for management"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute('''SELECT id, username, email, full_name, is_active, is_admin, role, last_login, created_at
                        FROM users ORDER BY created_at DESC''')
            return [dict(row) for row in c.fetchall()]
        finally:
            conn.close()

    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user role"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # Update role and sync is_admin flag for backward compatibility
            is_admin_flag = 1 if new_role in ('admin', 'super_admin') else 0
            
            c.execute("UPDATE users SET role = ?, is_admin = ? WHERE id = ?", 
                     (new_role, is_admin_flag, user_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False
        finally:
            conn.close()

    def delete_user(self, user_id: int) -> bool:
        """Soft delete user"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
        finally:
            conn.close()

    def create_session(self, user_id: int, session_token: str, remember_me: bool = False, 
                      ip_address: str = None, user_agent: str = None) -> dict:
        """Create a new session - 45 mins default, extended if remember_me"""
        from datetime import datetime, timedelta
        
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # Set expiration: 45 mins or 30 days if remember_me
            if remember_me:
                expires_at = datetime.now() + timedelta(days=30)
            else:
                expires_at = datetime.now() + timedelta(minutes=45)
            
            c.execute('''INSERT INTO sessions 
                        (user_id, session_token, expires_at, ip_address, user_agent, remember_me)
                        VALUES (?, ?, ?, ?, ?, ?)''',
                     (user_id, session_token, expires_at, ip_address, user_agent, 1 if remember_me else 0))
            conn.commit()
            
            # Update last_login
            c.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            conn.commit()
            
            return {"success": True, "session_id": c.lastrowid, "expires_at": expires_at}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def validate_session(self, session_token: str) -> dict:
        """Validate a session token and return user info if valid"""
        from datetime import datetime
        
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # Get session and check expiration
            c.execute('''SELECT s.id, s.user_id, s.expires_at, s.is_active, u.username, u.email, u.full_name
                        FROM sessions s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.session_token = ? AND s.is_active = 1''', (session_token,))
            
            result = c.fetchone()
            if not result:
                return {"valid": False, "error": "Session not found"}
            
            session = dict(result)
            expires_at = datetime.fromisoformat(session['expires_at'])
            
            # Check if expired
            if datetime.now() > expires_at:
                # Invalidate expired session
                c.execute("UPDATE sessions SET is_active = 0 WHERE id = ?", (session['id'],))
                conn.commit()
                return {"valid": False, "error": "Session expired"}
            
            # Update last activity
            c.execute("UPDATE sessions SET last_activity = CURRENT_TIMESTAMP WHERE id = ?", (session['id'],))
            conn.commit()
            
            return {
                "valid": True,
                "user_id": session['user_id'],
                "username": session['username'],
                "email": session['email'],
                "full_name": session['full_name']
            }
            
        finally:
            conn.close()

    def invalidate_session(self, session_token: str) -> bool:
        """Invalidate/logout a session"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("UPDATE sessions SET is_active = 0 WHERE session_token = ?", (session_token,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error invalidating session: {str(e)}")
            return False
        finally:
            conn.close()

    def cleanup_expired_sessions(self):
        """Clean up expired sessions (run periodically)"""
        from datetime import datetime
        
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute("DELETE FROM sessions WHERE expires_at < ?", (datetime.now(),))
            conn.commit()
            return c.rowcount
        except Exception as e:
            print(f"Error cleaning up sessions: {str(e)}")
            return 0
        finally:
            conn.close()