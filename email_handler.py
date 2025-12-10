from typing import Dict, Any, Optional, List
import re
import json
from datetime import datetime
from database import Database
from gmail_service import GmailService
from config import GMAIL_CREDENTIALS_PATH

class EmailHandler:
    def __init__(self, database: Database):
        self.gmail = GmailService(GMAIL_CREDENTIALS_PATH)
        self.db = database
        self.sent_request_thread_ids = set()
    
    def verify_database_update(self, name: str, price: float, width: str = None) -> bool:
        try:
            products = self.db.get_products()
            for p in products:
                if p['name'] == name:
                    if width is None or p['width'] == width:
                        standard_price = p.get('standard_price', p.get('cost_price', 0))
                        if abs(standard_price - price) < 0.01:
                            return True
            return False
        except Exception as e:
            print(f"Error verifying database update: {str(e)}")
            return False
        
    def _is_valid_price(self, price: float) -> bool:
        MIN_PRICE = 0.01
        MAX_PRICE = 1000.0
        return MIN_PRICE <= price <= MAX_PRICE
    
    def _normalize_product_name(self, name: str) -> str:
        name = ' '.join(name.split())
        name = name.title()
        return name
    
    def _normalize_width(self, width: str) -> Optional[str]:
        if not width:
            return None
        
        width = str(width).strip()
        
        number_match = re.search(r'(\d+(?:\.\d+)?)', width)
        if number_match:
            number = number_match.group(1)
            return f'{number}"'
        
        return None
    
    def _parse_volume_discounts(self, discount_text: str) -> dict:
        try:
            discounts = {}
            lines = discount_text.split('\n')
            for line in lines:
                match = re.search(r'(\d+)\s*(?:to|-)?\s*(?:(\d+)\s*)?sqft\s*[:-]\s*(\d+(?:\.\d+)?)\s*%', line, re.IGNORECASE)
                if match:
                    min_qty = int(match.group(1))
                    max_qty = int(match.group(2)) if match.group(2) else None
                    discount = float(match.group(3))
                    key = f"{min_qty}-{max_qty if max_qty else 'inf'}"
                    discounts[key] = discount
            return discounts if discounts else None
        except Exception as e:
            print(f"Error parsing volume discounts: {str(e)}")
            return None
    
    def _extract_promotion_info(self, email_body: str) -> Dict[str, Any]:
        promo_info = {}
        
        promo_patterns = [
            (r'(?:promo|promotion|discount|special|offer)\s*(?:name|code)?\s*[:-]\s*([^\n,]+)', 'name'),
            (r'(?:valid|active|starts?|from)\s*(?:on|from)?\s*([\d\-/]+)', 'start_date'),
            (r'(?:until|ends?|through|until)\s*([\d\-/]+)', 'end_date'),
            (r'(\d+\s*%\s*(?:discount|off))', 'discount'),
        ]
        
        for pattern, key in promo_patterns:
            match = re.search(pattern, email_body, re.IGNORECASE)
            if match:
                promo_info[key] = match.group(1).strip()
        
        return promo_info if promo_info else None
        
    def send_price_request(self, supplier_email: str, products: list) -> Dict[str, Any]:
        subject = "Price Update Request - PrimeLine Flooring"
        
        product_list = "\n".join([f"• {product}: $_______ per sq.ft" for product in products])
        
        body = f"""
Dear Valued Supplier Partner,

Thank you for being a key part of our flooring supply chain. We're reaching out to request 
the most current pricing and promotional information for the following products:

{product_list}

📋 PRICING & PROMOTIONS REQUEST

We track both standard pricing AND promotional offers. Please provide:

1. STANDARD PRICING per sq.ft (required) for each product:
   Example: "Red Oak 7\": $5.14/sqft"

2. PROMOTIONS & DISCOUNTS (if applicable):

   → Promotion Name (e.g., "Fall Sale 2025", "Contractor Discount")
   → Discount Percentage (e.g., 10% off, 15% off)
   → Promotion Valid Dates (Critical: Start date and End date)
   → VOLUME DISCOUNTS - tiered pricing by quantity
     Example: "500-999 sqft: 5% off, 1000+ sqft: 10% off"

RESPONSE FORMAT EXAMPLES:
✓ "Red Oak 7\" is now $5.14/sqft"
✓ "White Oak 5\": $4.50/sqft (10% off - Fall Sale 2025 - ends Nov 30)"
✓ "Maple 6\" - Standard: $5.25 | Promo: Holiday Bundle (12% off until 12/31) | Volume: 500-999 sqft: 8% off, 1000+ sqft: 12% off"

⚠️  WHY THIS MATTERS

• Promotion expiry dates ensure we quote customers accurately
• Volume discount tiers determine bid competitiveness 
• Our AI learns patterns to serve you and customers better

Please reply within 24 hours.

Thank you for your continued partnership.

Best regards,
PrimeLine Flooring
Smart Flooring Solutions through Artificial Intelligence

Note: This is an automated request. If you have any questions, please contact your PrimeLine Flooring representative.
"""
        
        result = self.gmail.send_email(supplier_email, subject, body)
        
        if result.get('status') == 'success':
            thread_id = result.get('thread_id')
            if thread_id:
                self.sent_request_thread_ids.add(thread_id)
                print(f"Tracking thread ID: {thread_id} for supplier: {supplier_email}")
        
        return result
    
    def check_replies_and_save(self, gemini_client=None) -> list:
        # Get our own email address first
        try:
            own_email = self.gmail.get_user_email()
        except:
            print("Warning: Could not get user email, using default filters")
            own_email = None

        # Query for replies - try multiple approaches in order of specificity
        queries_to_try = [
            ('subject:"Re: Price Update Request - PrimeLine Flooring" is:unread', 'Unread replies to PrimeLine'),
            ('subject:"Re: Price Update Request - FloorCraft AI" is:unread', 'Unread replies to FloorCraft'),
            ('subject:"Re: Price Update Request" is:unread', 'Any unread replies'),
            ('subject:"Re: Price Update Request - PrimeLine Flooring"', 'All replies to PrimeLine'),
            ('subject:"Re: Price Update Request - FloorCraft AI"', 'All replies to FloorCraft'),
            ('subject:"Re: Price Update Request"', 'Any Price Update replies'),
            ('subject:"Price Update"', 'Any Price Update related emails'),
        ]
        
        messages = []
        for query, description in queries_to_try:
            if not query.strip():  # Skip empty queries
                continue
            print(f"Attempting: {description}")
            print(f"  Query: {query}")
            messages = self.gmail.check_inbox(query=query, max_results=20)
            if messages:
                print(f"  [SUCCESS] Found {len(messages)} message(s)\n")
                break
            else:
                print(f"  [No results]\n")
        
        if not messages:
            print("No messages found in any query")
            return []
        
        results = []
        for message in messages:
            try:
                sender = message.get('sender', 'Unknown')
                
                # Only filter exact match of our email
                if own_email and sender.lower() == own_email.lower():
                    print(f"Skipping message from self: {sender}")
                    continue
                
                print(f"\nProcessing message from: {sender}")
                print(f"Subject: {message.get('subject', 'N/A')}")
                print(f"Body preview: {message.get('body', '')[:200]}...")
                
                response = self._extract_prices_with_gemini(message['body'], gemini_client)
                
                if not response:
                    print(f"No prices extracted from message")
                    continue
                
                products = response.get("products", [])
                if not products or not isinstance(products, list):
                    print(f"Invalid products format in response")
                    continue
                
                print(f"Found {len(products)} products in email")
                
                updated_products = []
                
                for product in products:
                    if not isinstance(product, dict):
                        continue
                    
                    name = product.get("name")
                    width = product.get("width")
                    price = product.get("price_per_sqft")
                    
                    if not name or not price:
                        print(f"Skipping product with missing name or price: {product}")
                        continue
                    
                    try:
                        price_float = float(price)
                        if not self._is_valid_price(price_float):
                            print(f"Invalid price for {name}: ${price_float}")
                            continue
                        
                        name = self._normalize_product_name(name)
                        width = self._normalize_width(width) if width else None
                        
                        print(f"Attempting to update: {name} {width or '(no width)'} = ${price_float}")
                        
                        discount_pct = product.get('discount_percentage')
                        min_qty = product.get('min_qty_discount')
                        promo = product.get('promotion', {})
                        vol_disc = product.get('volume_discounts')
                        
                        # Convert volume_discounts dict to JSON string if needed
                        if isinstance(vol_disc, dict):
                            vol_disc = json.dumps(vol_disc)
                        
                        promo_name = None
                        if isinstance(promo, dict):
                            promo_name = promo.get('name')
                        
                        success = self.db.update_product_price(
                            name, price_float, width,
                            discount_percentage=discount_pct,
                            min_qty=min_qty,
                            promotion_name=promo_name,
                            volume_discounts=vol_disc
                        )
                        
                        if success:
                            verified = self.verify_database_update(name, price_float, width)
                            if verified:
                                display_name = f"{name} ({width})" if width else name
                                updated_products.append({
                                    "name": display_name,
                                    "price": price_float,
                                    "discount": discount_pct,
                                    "promotion": promo_name,
                                    "volume_discounts": vol_disc
                                })
                                promo_info = f" - {promo_name}" if promo_name else ""
                                discount_info = f" ({discount_pct}% off)" if discount_pct else ""
                                print(f"✓ Updated and verified: {display_name} = ${price_float}{discount_info}{promo_info}")
                            else:
                                print(f"⚠ Update reported success but verification failed for {name} {width or ''}")
                        else:
                            print(f"✗ Failed to update {name} {width or ''} - product may not exist in database")
                            
                            existing_products = self.db.get_products()
                            print(f"Available products in DB: {[(p['name'], p.get('width')) for p in existing_products]}")
                    
                    except (ValueError, TypeError) as e:
                        print(f"Error processing product {name}: {str(e)}")
                        continue
                
                if updated_products:
                    thread_id = message.get('thread_id')
                    
                    self.gmail.mark_as_read(message['id'])
                    self.gmail.archive_message(message['id'])
                    
                    if thread_id and thread_id in self.sent_request_thread_ids:
                        self.sent_request_thread_ids.remove(thread_id)
                    
                    results.append({
                        'supplier': sender,
                        'products': updated_products,
                        'status': 'processed',
                        'message': f"Updated {len(updated_products)} product(s)"
                    })
                    print(f"✓ Successfully processed {len(updated_products)} product(s) from {sender}")
                else:
                    print(f"No products were successfully updated for this message")
            
            except Exception as e:
                print(f"Error processing message from {message.get('sender', 'unknown')}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        return results
    
    def _extract_prices_with_gemini(self, email_body: str, gemini_client) -> Optional[Dict[str, Any]]:
        if not gemini_client or not gemini_client.initialized:
            print("Gemini not available, using fallback parser")
            return self._fallback_email_parse(email_body)
            
        try:
            print("Attempting Gemini parsing...")
            parsed_data = gemini_client.parse_email_response(email_body)
            
            if not parsed_data or 'products' not in parsed_data:
                print("Gemini returned no data, using fallback")
                return self._fallback_email_parse(email_body)
            
            for product in parsed_data.get('products', []):
                promo_info = self._extract_promotion_info(email_body)
                if promo_info:
                    product['promotion'] = promo_info
                volume_disc = self._parse_volume_discounts(email_body)
                if volume_disc:
                    product['volume_discounts'] = volume_disc
            
            print(f"Gemini parsed: {parsed_data}")
            return parsed_data
            
        except Exception as e:
            print(f"Error in Gemini price extraction: {str(e)}")
            return self._fallback_email_parse(email_body)
    
    def _fallback_email_parse(self, email_content: str) -> Optional[Dict[str, Any]]:
        print("Using fallback regex parsing with promotion detection...")
        products = []
        clean_content = re.sub(r'<[^>]+>', '', email_content)
        
        promo_info = self._extract_promotion_info(clean_content)
        volume_discounts = self._parse_volume_discounts(clean_content)
        
        # Enhanced discount detection - look for various formats
        discount_match = re.search(r'(?:discount\s+of\s+)?(\d+(?:\.\d+)?)\s*%\s*(?:off|discount)?', clean_content, re.IGNORECASE)
        discount_pct = float(discount_match.group(1)) if discount_match else None
        
        # Extract minimum quantity (can be in terms of sqft or other units)
        min_qty_match = re.search(r'(?:above|over|minimum|min)\s*(?:the\s+range\s+of|order|qty|quantity)?\s*(\d+)\s*(?:sq\.?\s*ft|sqft|square\s+feet)?', clean_content, re.IGNORECASE)
        min_qty = int(min_qty_match.group(1)) if min_qty_match else None
        
        patterns = [
            # "Red Oak 5" now costs $3.95 with a discount of 12%"
            r'([A-Za-z\s]+?)\s+(\d+)\s*(?:inch|in|\"|\'\'|")\s+(?:now\s+)?(?:costs?|is|will\s+be)\s*\$?(\d+\.?\d*)',
            r'(?:updated?\s+)?(?:the\s+)?price\s+(?:of\s+)?(\d+)\s*(?:inch|in|\"|\'\'|")\s+(?:width\s+)?(?:of\s+)?([A-Za-z\s]+?)\s+(?:to|is|now|:)?\s*\$?(\d+\.?\d*)',
            r'([A-Za-z\s]+?)\s+(\d+)\s*(?:inch|in|\"|\'\'|")\s+(?:is\s+)?(?:now\s+)?(?:will\s+be\s+)?\$?(\d+\.?\d*)\s*(?:/sqft|per\s+sq\.?\s*ft\.?)?',
            r'([A-Za-z\s]+?)\s+(\d+)\s*(?:inch|in|\"|\'\'|")\s*[:]\s*\$?(\d+\.?\d*)\s*(?:/sqft|per\s+sq\.?\s*ft\.?)?',
            r'(\d+)\s*(?:inch|in|\"|\'\'|")\s+([A-Za-z\s]+?)\s+(?:is\s+)?(?:now\s+)?(?:will\s+be\s+)?\$?(\d+\.?\d*)\s*(?:/sqft|per\s+sq\.?\s*ft\.?)?',
            r'([A-Za-z\s]+?)\s*[:|-]\s*\$?(\d+\.?\d*)\s*(?:/sqft|per\s+sq\.?\s*ft\.?)?',
            r'•\s*([A-Za-z\s]+?)(?:\s+(\d+)\s*(?:inch|in|\"|\'\'|"))?\\s*[:|-]?\s*\$?(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, clean_content, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    name = None
                    width = None
                    price = None
                    
                    if len(groups) == 3:
                        if groups[0].strip().isdigit():
                            width = groups[0]
                            name = groups[1]
                            price = groups[2]
                        elif len(groups) > 1 and groups[1] and groups[1].strip().isdigit():
                            name = groups[0]
                            width = groups[1]
                            price = groups[2]
                        else:
                            name = groups[0]
                            price = groups[1] if groups[1] else groups[2]
                            width = None
                    elif len(groups) == 2:
                        name = groups[0]
                        price = groups[1]
                        width = None
                    else:
                        continue
                    
                    if not name or not price:
                        continue
                    
                    name = self._normalize_product_name(name)
                    price_float = float(price)
                    
                    wood_types = ['oak', 'maple', 'walnut', 'bamboo', 'cork', 'cherry', 'hickory', 'ash']
                    if any(wood in name.lower() for wood in wood_types):
                        if len(name) > 2 and self._is_valid_price(price_float):
                            product = {
                                "name": name,
                                "price_per_sqft": price_float,
                                "width": self._normalize_width(width) if width else None,
                                "discount_percentage": discount_pct,
                                "min_qty_discount": min_qty,
                                "promotion": promo_info,
                                "volume_discounts": volume_discounts
                            }
                            
                            already_exists = any(
                                p["name"] == product["name"] and 
                                p.get("width") == product.get("width") and
                                p["price_per_sqft"] == product["price_per_sqft"]
                                for p in products
                            )
                            
                            if not already_exists:
                                products.append(product)
                                discount_str = f" - {discount_pct}% off" if discount_pct else ""
                                print(f"Regex found: {product['name']} {product['width'] or ''} @ ${price_float}{discount_str}")
                
                except (ValueError, IndexError, AttributeError) as e:
                    continue
        
        if products:
            return {
                "products": products,
                "notes": "Parsed using regex fallback"
            }
        
        print("No products found by regex parser")
        return None