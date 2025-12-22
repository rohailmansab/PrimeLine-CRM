import pgeocode
import re
from typing import Dict, Any, Optional

# Initialize US ZIP code database
nomi = pgeocode.Nominatim('us')

def validate_zip_code(zip_code: str) -> Optional[Dict[str, Any]]:
    """
    Validates a US ZIP code format and authenticity.
    Returns location details if valid, else None.
    """
    if not zip_code:
        return None
        
    # Clean input
    clean_zip = str(zip_code).strip()
    
    # Format check: Must be 5 digits
    if not re.match(r'^\d{5}$', clean_zip):
        return None
        
    # Authenticity check using pgeocode
    location = nomi.query_postal_code(clean_zip)
    
    # pgeocode returns NaN for invalid ZIPs
    if location is None or (isinstance(location.place_name, float) and str(location.place_name) == 'nan'):
        return None
        
    return {
        "zip_code": clean_zip,
        "city": location.place_name,
        "state": location.state_name,
        "state_code": location.state_code,
        "county": location.county_name,
        "latitude": location.latitude,
        "longitude": location.longitude
    }

def validate_width(width_str: str) -> str:
    """
    Ensures width follows the required format (number + " or 'Custom').
    Returns formatted width string.
    """
    if not width_str:
        return ""
    
    width_str = str(width_str).strip()
    if width_str.lower() == "custom":
        return "Custom"
        
    # If it's just a number, add the " suffix
    if re.match(r'^\d+(\.\d+)?$', width_str):
        return f'{width_str}"'
        
    # Ensure it ends with " if it's a number
    if re.match(r'^\d+(\.\d+)?\"$', width_str):
        return width_str
        
    return width_str

def parse_volume_discounts(discount_str: str, quantity: float) -> float:
    """
    Parses a volume discount string and returns the discount percentage for the given quantity.
    Example string: "500-999 sqft: 5% off, 1000-1499 sqft: 8% off, 1500+ sqft: 10% off"
    """
    if not discount_str or not quantity:
        return 0.0
        
    try:
        # Split by comma to get individual tiers
        tiers = discount_str.split(',')
        best_discount = 0.0
        
        for tier in tiers:
            tier = tier.strip().lower()
            if not tier:
                continue
                
            # Extract percentage
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', tier)
            if not pct_match:
                continue
            pct = float(pct_match.group(1))
            
            # Check for "+" format (e.g., "1500+ sqft")
            if '+' in tier:
                min_qty_match = re.search(r'(\d+)\s*\+', tier)
                if min_qty_match:
                    min_qty = int(min_qty_match.group(1))
                    if quantity >= min_qty:
                        best_discount = max(best_discount, pct)
            
            # Check for range format (e.g., "500-999 sqft")
            elif '-' in tier:
                range_match = re.search(r'(\d+)\s*-\s*(\d+)', tier)
                if range_match:
                    min_qty = int(range_match.group(1))
                    max_qty = int(range_match.group(2))
                    if min_qty <= quantity <= max_qty:
                        best_discount = max(best_discount, pct)
        
        return best_discount
    except Exception as e:
        print(f"Error parsing volume discounts: {e}")
        return 0.0
