from database import Database

def update_products():
    db = Database()
    
    new_products = [
        ("Hickory", '5"', "Durable hickory flooring - high shock resistance", "Hardwood", 4.75, 5.10, 400, 10.0, "bulk", "Winter Hardwood Sale", "2025-12-01", "2026-02-28", "400-799 sqft: 5% off, 800+ sqft: 10% off"),
        ("Hickory", '7"', "Wide plank hickory - rustic character", "Hardwood", 5.25, 5.60, 300, 12.0, "bulk", "Winter Hardwood Sale", "2025-12-01", "2026-02-28", "300-699 sqft: 6% off, 700+ sqft: 12% off"),
        ("E-Thermawood", '5"', "Thermally treated wood - enhanced stability", "Premium", 5.25, 5.75, 250, 15.0, "bulk", "Eco-Premium Launch", "2025-12-15", "2026-03-15", "250-499 sqft: 8% off, 500+ sqft: 15% off"),
        ("E-Thermawood", '6"', "Wide plank E-Thermawood - modern aesthetic", "Premium", 5.75, 6.25, 200, 18.0, "bulk", "Eco-Premium Launch", "2025-12-15", "2026-03-15", "200-399 sqft: 10% off, 400+ sqft: 18% off")
    ]
    
    print("Adding new products to database...")
    count = 0
    for product in new_products:
        try:
            db.add_product(*product)
            print(f"Added: {product[0]} ({product[1]})")
            count += 1
        except Exception as e:
            print(f"Error adding {product[0]}: {e}")
            
    print(f"\nSuccessfully added {count} product variants.")

if __name__ == "__main__":
    update_products()
