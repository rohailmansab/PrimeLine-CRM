import google.generativeai as genai
import json
import re
from typing import Dict, Any, Optional, List

class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.initialized = False
        self.model = None
        
        try:
            if not api_key or not api_key.startswith("AI"):
                raise ValueError("Invalid API key format")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            
            test_response = self.model.generate_content("Hello")
            if test_response:
                self.initialized = True
                print(f"[OK] Successfully initialized gemini-2.0-flash-lite")
        except Exception as e:
            print(f"[ERROR] Gemini initialization error: {str(e)}")
            self.initialized = False
    
    def _parse_json_response(self, text: str) -> Optional[Dict]:
        try:
            cleaned = text.strip()
            
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {str(e)}")
            return None
        except Exception as e:
            print(f"Unexpected parse error: {str(e)}")
            return None
    
    def generate_supplier_email(self, supplier_name: str, products: List[str]) -> str:
        if not self.initialized:
            product_list = "\n".join([f"• {product}: $_______ per sq.ft" for product in products])
            return f"""Dear {supplier_name},

We hope this email finds you well. As part of our regular price update process, 
we kindly request your current pricing information for the following products:

{product_list}

Please reply with your current prices per square foot.

Thank you for your continued partnership.

Best regards,
PrimeLine Flooring Development Team
Smart Flooring Solutions through Artificial Intelligence"""
        
        try:
            prompt = f"""
Generate a professional supplier price request email.

Supplier: {supplier_name}
Products: {', '.join(products)}

Requirements:
- Professional and courteous tone
- Request current pricing per square foot
- Ask for volume discounts if available
- Set 3 business day response deadline
- Include thank you for partnership

Write the complete email body only, no subject line.
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Email generation error: {str(e)}, using template")
            product_list = "\n".join([f"• {product}: $_______ per sq.ft" for product in products])
            return f"""Dear {supplier_name},

We hope this email finds you well. As part of our regular price update process, 
we kindly request your current pricing information for the following products:

{product_list}

Please reply with your current prices per square foot. If you have any volume 
discounts or ongoing promotions, please include those details as well.

We would appreciate a response within 3 business days.

Thank you for your continued partnership.

Best regards,
PrimeLine Flooring Team
Smart Flooring Solutions"""
    
    def parse_email_response(self, email_content: str) -> Optional[Dict[str, Any]]:
        if not self.initialized:
            return self._fallback_email_parse(email_content)
        
        try:
            prompt = f"""
Extract ALL product pricing and promotion information from this supplier email response.

Email Content:
{email_content[:2000]}

Instructions:
1. Find ALL products with prices mentioned in ANY format
2. Products may be mentioned as: "Red Oak", "RedOak", "red oak", "Red  Oak" (normalize spacing/case)
3. Widths may be: 7", 7 inch, 7-inch, 7inch (convert to format like "7\\"")
4. Prices may be: $5.14, 5.14, USD 5.14, 5.14/sqft (extract number only)
5. ALSO extract if mentioned: discount percentage, promotion name, volume discounts, minimum quantities
6. If no width specified, set width to null
7. Look for phrases like: "discount of X%", "X% off", "volume discount", "bulk pricing", "min order", "above X sqft"

Return ONLY valid JSON with this structure:
{{
  "products": [
    {{
      "name": "Product Name",
      "width": "5\\"",
      "price_per_sqft": 4.25,
      "discount_percentage": 10,
      "min_qty_discount": 500,
      "promotion": "Promotion Name",
      "volume_discounts": "500-999 sqft: 5% off, 1000+ sqft: 10% off"
    }}
  ],
  "notes": "any additional information"
}}

Example for "Red Oak 5\" now costs $3.95 with a discount of 12% for 20 days above 550 sq. feet":
{{
  "products": [
    {{
      "name": "Red Oak",
      "width": "5\\"",
      "price_per_sqft": 3.95,
      "discount_percentage": 12,
      "min_qty_discount": 550,
      "promotion": "20-day promotion",
      "volume_discounts": null
    }}
  ],
  "notes": "12% discount applies for purchases over 550 sq. feet for 20 days"
}}

IMPORTANT RULES:
- Extract ALL discount/promotion info mentioned in the email
- Return ALL products found (list can have 1 or more items)
- Discount percentage as number (not string with %)
- Min quantity as number in sqft
- Normalize product names to title case
- Only include promotion/volume/min_qty fields if mentioned in the email (otherwise null)
"""
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            if result and "products" in result and isinstance(result["products"], list):
                validated_products = []
                
                for product in result["products"]:
                    if not isinstance(product, dict):
                        continue
                        
                    name = product.get("name", "").strip()
                    price = product.get("price_per_sqft")
                    width = product.get("width")
                    
                    if name and price:
                        try:
                            price_float = float(price)
                            if 0.01 <= price_float <= 1000.0:
                                validated_product = {
                                    "name": name,
                                    "price_per_sqft": price_float
                                }
                                
                                if width:
                                    width_str = str(width).strip()
                                    if width_str and not width_str.endswith('"'):
                                        width_str = f'{width_str}"'
                                    validated_product["width"] = width_str
                                else:
                                    validated_product["width"] = None
                                
                                # Preserve promotion and discount fields if present
                                if "discount_percentage" in product and product["discount_percentage"] is not None:
                                    try:
                                        validated_product["discount_percentage"] = float(product["discount_percentage"])
                                    except (ValueError, TypeError):
                                        pass
                                
                                if "min_qty_discount" in product and product["min_qty_discount"] is not None:
                                    try:
                                        validated_product["min_qty_discount"] = int(product["min_qty_discount"])
                                    except (ValueError, TypeError):
                                        pass
                                
                                if "promotion" in product and product["promotion"]:
                                    validated_product["promotion"] = str(product["promotion"]).strip()
                                
                                if "volume_discounts" in product and product["volume_discounts"]:
                                    validated_product["volume_discounts"] = str(product["volume_discounts"]).strip()
                                
                                validated_products.append(validated_product)
                        except (ValueError, TypeError):
                            continue
                
                if validated_products:
                    return {
                        "products": validated_products,
                        "notes": result.get("notes", "")
                    }
            
            return self._fallback_email_parse(email_content)
            
        except Exception as e:
            print(f"Email parsing error: {str(e)}, using fallback")
            return self._fallback_email_parse(email_content)
    
    def _fallback_email_parse(self, email_content: str) -> Optional[Dict[str, Any]]:
        products = []
        clean_content = re.sub(r'<[^>]+>', '', email_content)
        
        patterns = [
            r'(?:updated?\s+)?(?:the\s+)?price\s+(?:of\s+)?(\d+)\s*(?:inch|in|"|\'\'|")\s+(?:width\s+)?(?:of\s+)?([A-Za-z\s]+?)\s+(?:to|is|now|:)?\s*\$?(\d+\.?\d*)',
            r'([A-Za-z\s]+?)\s+(\d+)\s*(?:inch|in|"|\'\'|")\s+(?:is\s+)?(?:now\s+)?\$?(\d+\.?\d*)\s*(?:/sqft|per\s+sq\.?\s*ft\.?)?',
            r'(\d+)\s*(?:inch|in|"|\'\'|")\s+([A-Za-z\s]+?)\s+(?:is\s+)?(?:now\s+)?\$?(\d+\.?\d*)\s*(?:/sqft|per\s+sq\.?\s*ft\.?)?',
            r'([A-Za-z\s]+?)\s*[:|-]\s*\$?(\d+\.?\d*)\s*(?:/sqft|per\s+sq\.?\s*ft\.?)?',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, clean_content, re.IGNORECASE)
            for match in matches:
                try:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        if groups[0].isdigit():
                            width = f'{groups[0]}"'
                            name = groups[1].strip()
                            price = float(groups[2])
                        elif groups[1].isdigit():
                            name = groups[0].strip()
                            width = f'{groups[1]}"'
                            price = float(groups[2])
                        else:
                            name = groups[0].strip()
                            price = float(groups[1])
                            width = None
                    elif len(groups) == 2:
                        name = groups[0].strip()
                        price = float(groups[1])
                        width = None
                    else:
                        continue
                    
                    name = ' '.join(name.split())
                    name = name.title()
                    
                    wood_types = ['oak', 'maple', 'walnut', 'bamboo', 'cork', 'cherry', 'hickory', 'ash']
                    if any(wood in name.lower() for wood in wood_types):
                        if len(name) > 2 and 0.01 <= price <= 1000.0:
                            product = {
                                "name": name,
                                "price_per_sqft": price,
                                "width": width
                            }
                            
                            if product not in products:
                                products.append(product)
                except (ValueError, IndexError, AttributeError) as e:
                    continue
        
        if products:
            return {
                "products": products,
                "notes": "Parsed using regex fallback"
            }
        
        return None
    
    def generate_market_analysis(self, location: str, product_specs: Dict[str, Any]) -> Dict[str, Any]:
        base_price = product_specs.get("cost", product_specs.get("base_price", 4.0))
        
        fallback_response = {
            "recommended_price_range": {
                "low": round(base_price * 1.2, 2),
                "high": round(base_price * 1.6, 2),
                "optimal": round(base_price * 1.35, 2)
            },
            "market_factors": ["Standard market conditions"],
            "competitor_analysis": {
                "average_market_price": round(base_price * 1.4, 2),
                "price_positioning": "mid-range"
            },
            "seasonal_adjustment": 0,
            "demand_indicator": "medium"
        }
        
        if not self.initialized:
            return fallback_response
        
        try:
            product_name = product_specs.get("name", "Unknown Product")
            
            prompt = f"""
Analyze the flooring market for pricing strategy.

Location: {location}
Product: {product_name}
Base Cost: ${base_price:.2f} per sqft
Specifications: {json.dumps(product_specs)}

Provide market analysis with competitive pricing recommendations.

Return ONLY valid JSON with this exact structure:
{{
  "recommended_price_range": {{
    "low": <float>,
    "high": <float>,
    "optimal": <float>
  }},
  "market_factors": ["<factor1>", "<factor2>", "<factor3>"],
  "competitor_analysis": {{
    "average_market_price": <float>,
    "price_positioning": "<low-end|mid-range|premium>"
  }},
  "seasonal_adjustment": <float between -0.1 and 0.1>,
  "demand_indicator": "<low|medium|high>"
}}

Example:
{{
  "recommended_price_range": {{"low": 5.20, "high": 6.40, "optimal": 5.75}},
  "market_factors": ["Strong demand in Raleigh market", "Oak flooring trending", "Competitive pricing landscape"],
  "competitor_analysis": {{"average_market_price": 5.60, "price_positioning": "mid-range"}},
  "seasonal_adjustment": 0.05,
  "demand_indicator": "high"
}}

Important: Ensure optimal price is between low and high, and all prices are realistic for flooring.
"""
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            if result and "recommended_price_range" in result:
                price_range = result["recommended_price_range"]
                if all(k in price_range for k in ["low", "high", "optimal"]):
                    try:
                        low = float(price_range["low"])
                        high = float(price_range["high"])
                        optimal = float(price_range["optimal"])
                        
                        if low > 0 and high > low and low <= optimal <= high:
                            return result
                    except (ValueError, TypeError):
                        pass
            
            print("Market analysis returned invalid format, using fallback")
            return fallback_response
            
        except Exception as e:
            print(f"Market analysis error: {str(e)}, using fallback")
            return fallback_response
    
    def calculate_quote(self, base_cost: float, market_data: Any) -> Dict[str, float]:
        if isinstance(market_data, dict):
            recommended_price = market_data.get("recommended_price_range", {}).get("optimal", base_cost * 1.35)
        elif isinstance(market_data, (int, float)):
            recommended_price = float(market_data)
        else:
            recommended_price = base_cost * 1.35
        
        markup_percentage = ((recommended_price - base_cost) / base_cost) * 100 if base_cost > 0 else 30.0
        
        fallback_response = {
            "selling_price": round(recommended_price, 2),
            "margin": round(markup_percentage, 1),
            "confidence": 0.7,
            "suggested_retail_price": round(base_cost * 2.0, 2),
            "suggested_dealer_price": round(base_cost * 1.4, 2)
        }
        
        if not self.initialized or not self.model:
            print(f"Gemini not initialized (initialized={self.initialized}, model={self.model is not None})")
            return fallback_response
        
        try:
            market_factors = []
            if isinstance(market_data, dict):
                market_factors = market_data.get("market_factors", [])
                demand = market_data.get("demand_indicator", "medium")
            else:
                demand = "medium"
            
            prompt = f"""
Calculate optimal selling price for flooring product.

Base Cost: ${base_cost:.2f} per sqft
Recommended Market Price: ${recommended_price:.2f} per sqft
Current Markup: {markup_percentage:.1f}%
Market Demand: {demand}
Market Factors: {', '.join(market_factors) if market_factors else 'Standard conditions'}

Return ONLY valid JSON:
{{
  "selling_price": <float>,
  "margin": <percentage as float>,
  "confidence": <float between 0 and 1>,
  "suggested_retail_price": <float>,
  "suggested_dealer_price": <float>
}}

Rules:
- Selling price should be competitive but profitable
- Margin should typically be 20-50% for flooring
- Confidence reflects market data quality
- Consider demand when setting price
- suggested_retail_price: Market rate for end consumers (usually higher)
- suggested_dealer_price: Market rate for contractors/dealers (usually lower)

Example: {{"selling_price": 5.67, "margin": 32.5, "confidence": 0.85, "suggested_retail_price": 6.50, "suggested_dealer_price": 5.20}}
"""
            
            response = self.model.generate_content(prompt)
            result = self._parse_json_response(response.text)
            
            if result and "selling_price" in result:
                try:
                    selling_price = float(result["selling_price"])
                    margin = float(result.get("margin", markup_percentage))
                    confidence = float(result.get("confidence", 0.8))
                    retail = float(result.get("suggested_retail_price", base_cost * 2.0))
                    dealer = float(result.get("suggested_dealer_price", base_cost * 1.4))
                    
                    if selling_price > base_cost and 0 <= confidence <= 1:
                        return {
                            "selling_price": round(selling_price, 2),
                            "margin": round(margin, 1),
                            "confidence": round(confidence, 2),
                            "suggested_retail_price": round(retail, 2),
                            "suggested_dealer_price": round(dealer, 2)
                        }
                except (ValueError, TypeError) as e:
                    print(f"Error parsing quote values: {str(e)}")
            
            return fallback_response
            
        except Exception as e:
            print(f"Quote calculation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return fallback_response
    
    def generate_customer_quote_email(self, quote_data: Dict[str, Any]) -> str:
        if not self.initialized:
            return self._fallback_customer_email(quote_data)
        
        try:
            prompt = f"""
Generate a professional quote email for a flooring customer.

Quote Details:
- Customer: {quote_data.get('customer_name', 'Valued Customer')}
- Location: {quote_data.get('location', 'N/A')}
- Product: {quote_data.get('product', 'N/A')}
- Quantity: {quote_data.get('quantity', 0)} square feet
- Price per sqft: ${quote_data.get('price_per_sqft', 0):.2f}
- Total Amount: ${quote_data.get('total', 0):,.2f}

Requirements:
- Professional and friendly tone
- Thank them for interest
- Present quote clearly
- Mention 30-day validity
- Include next steps
- Offer to answer questions

Write the complete email body only.
"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Customer email generation error: {str(e)}")
            return self._fallback_customer_email(quote_data)
    
    def _fallback_customer_email(self, quote_data: Dict[str, Any]) -> str:
        return f"""Dear {quote_data.get('customer_name', 'Valued Customer')},

Thank you for your interest in our flooring products. We are pleased to provide you with the following quote:

QUOTE DETAILS:
--------------
Location: {quote_data.get('location', 'N/A')}
Product: {quote_data.get('product', 'N/A')}
Quantity: {quote_data.get('quantity', 0):,} square feet
Price per sq ft: ${quote_data.get('price_per_sqft', 0):.2f}

TOTAL AMOUNT: ${quote_data.get('total', 0):,.2f}

This quote is valid for 30 days from the date of this email. 

We pride ourselves on quality products and excellent customer service. If you have any questions or would like to proceed with this order, please don't hesitate to contact us.

We look forward to working with you on your flooring project!

Best regards,
PrimeLine Flooring AI Team
Smart Flooring Solutions through Artificial Intelligence"""