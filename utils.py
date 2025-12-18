import pgeocode
import re
from typing import Dict, Any, Optional

# Initialize US ZIP code database
nomi = pgeocode.NominalData('us')

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
