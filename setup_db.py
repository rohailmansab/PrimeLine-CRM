from database import Database
import os
import time

def setup_database():
    # Ensure data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Remove existing database if it exists
    if os.path.exists('data/crm.db'):
        try:
            os.remove('data/crm.db')
        except Exception as e:
            print(f"Could not remove existing database: {e}")
            return False
    
    # Wait a moment to ensure file handle is released
    time.sleep(1)
    
    try:
        db = Database()
        success = db.populate_sample_data()
        if success:
            print("Database populated successfully!")
            return True
        else:
            print("Failed to populate database.")
            return False
    except Exception as e:
        print(f"Error setting up database: {e}")
        return False

if __name__ == "__main__":
    setup_database()