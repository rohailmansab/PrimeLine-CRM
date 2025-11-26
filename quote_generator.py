import sqlite3
from gemini_client import GeminiClient
from typing import Dict, Any, Optional
import os

def get_gemini_client() -> Optional[GeminiClient]:
    """Initialize Gemini client with proper error handling"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set")
        return None
    
    try:
        return GeminiClient(api_key)
    except Exception as e:
        print(f"Error initializing Gemini client: {str(e)}")
        return None

def generate_quote(city: str, product: str, width: str, sqft: float) -> Dict[str, Any]:
    """Generate an intelligent quote using market data and AI analysis"""
    cost = 4.0
    try:
        conn = sqlite3.connect('data/crm.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT cost_price FROM products WHERE name=? AND width=?", (product, width))
        result = c.fetchone()
        if result:
            cost = result['cost_price']
        conn.close()
    except Exception as e:
        print(f"Error fetching product price: {str(e)}")

    # Try to get AI-enhanced pricing if possible
    client = get_gemini_client()
    if client:
        try:
            # Get market analysis
            product_specs = {
                "product": product,
                "width": width,
                "quantity": sqft
            }
            market_data = client.generate_market_analysis(city, product_specs)
            
            # Calculate optimal pricing
            pricing = client.calculate_quote(cost, float(market_data.get("recommended_price", cost * 1.5)))
            our_price = pricing["selling_price"]
            margin = pricing["margin"]
        except Exception as e:
            print(f"Warning: Using fallback pricing due to error: {str(e)}")
            our_price = cost * 1.3  # 30% margin fallback
            margin = 30.0
    else:
        # Fallback to simple pricing if AI is unavailable
        our_price = cost * 1.3
        margin = 30.0
    
    total = our_price * sqft

    return {
        "city": city,
        "product": f"{width} {product}",
        "sqft": sqft,
        "cost_per_sqft": cost,
        "selling_price": round(our_price, 2),
        "margin_percentage": round(margin, 1),
        "total": round(total, 2)
    }