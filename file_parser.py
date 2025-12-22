"""
File parsing utilities for bulk product imports.
Supports CSV and Excel file formats.
"""

import pandas as pd
from typing import Dict, List, Any, Tuple
import streamlit as st

def validate_product_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate product data structure and content.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required columns
    required_columns = ['name', 'width', 'standard_price']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        return False, errors
    
    # Check for empty required fields
    for col in required_columns:
        if df[col].isnull().any():
            null_count = df[col].isnull().sum()
            errors.append(f"Column '{col}' has {null_count} empty values")
    
    # Validate price ranges
    if 'standard_price' in df.columns:
        invalid_prices = df[df['standard_price'] <= 0]
        if not invalid_prices.empty:
            errors.append(f"Found {len(invalid_prices)} products with invalid prices (must be > 0)")
    
    # Validate width format
    if 'width' in df.columns:
        # Width should be like: 5", 7", etc.
        invalid_widths = df[~df['width'].astype(str).str.match(r'^\d+(\.\d+)?"$')]
        if not invalid_widths.empty:
            errors.append(f"Found {len(invalid_widths)} products with invalid width format (should be like: 5\", 7\")")
    
    return len(errors) == 0, errors

def parse_csv_file(file) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse CSV file and return DataFrame with errors.
    """
    try:
        df = pd.read_csv(file)
        
        # Normalize column names (lowercase, strip spaces)
        df.columns = df.columns.str.lower().str.strip()
        
        # Validate
        is_valid, errors = validate_product_data(df)
        
        return df, errors
    except Exception as e:
        return None, [f"Error parsing CSV: {str(e)}"]

def parse_excel_file(file) -> Tuple[pd.DataFrame, List[str]]:
    """
    Parse Excel file and return DataFrame with errors.
    """
    try:
        df = pd.read_excel(file)
        
        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Validate
        is_valid, errors = validate_product_data(df)
        
        return df, errors
    except Exception as e:
        return None, [f"Error parsing Excel: {str(e)}"]

def prepare_product_dict(row: pd.Series) -> Dict[str, Any]:
    """
    Convert DataFrame row to product dictionary for database import.
    """
    product = {
        'name': str(row['name']).strip(),
        'width': str(row['width']).strip(),
        'standard_price': float(row['standard_price']),
    }
    
    # Optional fields
    if 'cost_price' in row and pd.notna(row['cost_price']):
        product['cost_price'] = float(row['cost_price'])
    
    if 'description' in row and pd.notna(row['description']):
        product['description'] = str(row['description'])
    
    if 'category' in row and pd.notna(row['category']):
        product['category'] = str(row['category'])
    
    if 'discount_percentage' in row and pd.notna(row['discount_percentage']):
        product['discount_percentage'] = float(row['discount_percentage'])
    
    if 'min_qty_discount' in row and pd.notna(row['min_qty_discount']):
        product['min_qty_discount'] = int(row['min_qty_discount'])
    
    if 'promotion_name' in row and pd.notna(row['promotion_name']):
        product['promotion_name'] = str(row['promotion_name'])
    
    if 'volume_discounts' in row and pd.notna(row['volume_discounts']):
        product['volume_discounts'] = str(row['volume_discounts'])
    
    return product

def create_sample_template() -> pd.DataFrame:
    """
    Create a sample template DataFrame for users to download.
    """
    sample_data = {
        'name': ['Red Oak', 'White Oak', 'Maple'],
        'width': ['5"', '7"', '5"'],
        'standard_price': [4.50, 5.00, 4.75],
        'cost_price': [3.50, 4.00, 3.75],
        'category': ['Hardwood – Solid', 'Hardwood – Solid', 'Hardwood – Engineered'],
        'description': ['Premium red oak flooring', 'Luxury white oak', 'Select grade maple'],
        'discount_percentage': [10, 12, 8],
        'min_qty_discount': [500, 300, 600],
        'promotion_name': ['Fall Sale', 'Premium Special', 'Holiday Deal'],
        'volume_discounts': ['500-999: 5%, 1000+: 10%', '300-799: 7%, 800+: 12%', '600-999: 5%, 1000+: 8%']
    }
    
    return pd.DataFrame(sample_data)
