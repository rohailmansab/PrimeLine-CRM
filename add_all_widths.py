#!/usr/bin/env python3
"""
Script to add all supported widths for each product in the database.
This ensures every product has every width option available.
Can be run standalone or imported as a module.
"""

import sqlite3

DATABASE_PATH = "data/crm.db"
SUPPORTED_WIDTHS = ["2.5\"", "3.5\"", "4\"", "5\"", "6\"", "7\"", "8\"", "10\"", "11\"", "12\"", "13\"", "14\""]

def ensure_all_widths(db):
    """
    Ensure all supported widths exist for each product.
    Can be called with a Database instance.
    
    Args:
        db: Database instance
        
    Returns:
        int: Number of width variants added
    """
    try:
        conn = db.get_connection()
        c = conn.cursor()
        
        # Get all unique products (by name)
        c.execute("SELECT DISTINCT name FROM products ORDER BY name")
        products = [row['name'] for row in c.fetchall()]
        
        if not products:
            conn.close()
            return 0
        
        added_count = 0
        
        for product_name in products:
            # Get a template product to copy attributes from
            c.execute("""SELECT * FROM products WHERE name = ? LIMIT 1""", (product_name,))
            template_row = c.fetchone()
            if not template_row:
                continue
            template = dict(template_row)
            
            for width in SUPPORTED_WIDTHS:
                # Check if this product-width combination exists
                c.execute("SELECT id FROM products WHERE name = ? AND width = ?", (product_name, width))
                if c.fetchone() is None:
                    # Add this width for this product
                    c.execute("""
                        INSERT INTO products (
                            name, width, description, category, cost_price, standard_price,
                            min_qty_discount, discount_percentage, discount_type,
                            promotion_name, promotion_start_date, promotion_end_date,
                            volume_discounts, supplier_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product_name,
                        width,
                        template.get('description', f"{product_name} flooring - {width} width"),
                        template.get('category', 'Hardwood'),
                        template.get('cost_price', 4.0),
                        template.get('standard_price', 4.5),
                        template.get('min_qty_discount'),
                        template.get('discount_percentage'),
                        template.get('discount_type'),
                        template.get('promotion_name'),
                        template.get('promotion_start_date'),
                        template.get('promotion_end_date'),
                        template.get('volume_discounts'),
                        template.get('supplier_id')
                    ))
                    added_count += 1
        
        conn.commit()
        conn.close()
        
        if added_count > 0:
            print(f"✅ Added {added_count} missing width variants")
        
        return added_count
        
    except Exception as e:
        print(f"Error ensuring width variants: {e}")
        return 0

def add_missing_widths():
    """Standalone function for running as a script"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    try:
        # Get all unique products (by name)
        c.execute("SELECT DISTINCT name FROM products ORDER BY name")
        products = [row['name'] for row in c.fetchall()]
        
        print(f"Found {len(products)} unique products")
        print(f"Supported widths: {SUPPORTED_WIDTHS}")
        
        added_count = 0
        
        for product_name in products:
            # Get a template product to copy attributes from
            c.execute("""SELECT * FROM products WHERE name = ? LIMIT 1""", (product_name,))
            template = dict(c.fetchone())
            
            for width in SUPPORTED_WIDTHS:
                # Check if this product-width combination exists
                c.execute("SELECT id FROM products WHERE name = ? AND width = ?", (product_name, width))
                if c.fetchone() is None:
                    # Add this width for this product
                    c.execute("""
                        INSERT INTO products (
                            name, width, description, category, cost_price, standard_price,
                            min_qty_discount, discount_percentage, discount_type,
                            promotion_name, promotion_start_date, promotion_end_date,
                            volume_discounts
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product_name,
                        width,
                        template.get('description', f"{product_name} flooring - {width} width"),
                        template.get('category', 'Hardwood'),
                        template.get('cost_price', 4.0),
                        template.get('standard_price', 4.5),
                        template.get('min_qty_discount'),
                        template.get('discount_percentage'),
                        template.get('discount_type'),
                        template.get('promotion_name'),
                        template.get('promotion_start_date'),
                        template.get('promotion_end_date'),
                        template.get('volume_discounts')
                    ))
                    added_count += 1
                    print(f"✓ Added {product_name} {width}")
        
        conn.commit()
        print(f"\n✅ Successfully added {added_count} new product-width combinations!")
        
        # Show final count
        c.execute("SELECT COUNT(*) as count FROM products")
        total = c.fetchone()['count']
        print(f"Total products in database: {total}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_missing_widths()
