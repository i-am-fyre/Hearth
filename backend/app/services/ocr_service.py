import re
import json
from decimal import Decimal
from typing import Dict, Any, Tuple
import pytesseract
from PIL import Image
import io

# Regular expressions for receipt parsing
TOTAL_REGEX = re.compile(r'(?:total|amount|balance)[\s\:\-\$]*([0-9]+\.[0-9]{2})', re.IGNORECASE)
DATE_REGEX = re.compile(r'(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})')
CURRENCY_REGEX = re.compile(r'(\$|USD|EUR|GBP)')

def run_ocr(image_bytes: bytes) -> str:
    """Run Tesseract OCR on a decrypted image byte stream."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        # In a real app we would log this properly
        print(f"OCR Error: {e}")
        return ""

def parse_receipt_text(text: str) -> Tuple[Dict[str, Any], float]:
    """
    Parse OCR text using regex to extract structured data.
    Returns (parsed_json_dict, confidence_score).
    """
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    parsed_data = {
        "merchant": "Unknown Merchant",
        "date": None,
        "currency": "USD",
        "items": [],
        "subtotal": "0.00",
        "tax": "0.00",
        "total": "0.00"
    }
    
    # Very basic heuristic for merchant (often the first line)
    if lines:
        parsed_data["merchant"] = lines[0]
        
    date_match = DATE_REGEX.search(text)
    if date_match:
        parsed_data["date"] = date_match.group(1)
        
    currency_match = CURRENCY_REGEX.search(text)
    if currency_match:
        # Normalize dollar sign to USD for the JSON standard
        parsed_data["currency"] = "USD" if currency_match.group(1) == '$' else currency_match.group(1)
        
    # Find totals
    total_matches = TOTAL_REGEX.findall(text)
    if total_matches:
        # Usually the last matched total is the final total, but let's just take the max for safety
        parsed_data["total"] = str(max([Decimal(match) for match in total_matches]))

    # Simplistic Line Item detection (Looking for lines ending in a price)
    item_regex = re.compile(r'^(.*?)\s+([0-9]+\.[0-9]{2})$')
    calculated_sum = Decimal('0.00')
    
    for line in lines:
        # Skip lines that look like totals
        if re.search(r'(total|tax|subtotal|balance|amount|change|cash)', line, re.IGNORECASE):
            continue
            
        match = item_regex.match(line)
        if match:
            name = match.group(1).strip()
            # Ignore items that are too short to be real things
            if len(name) < 3:
                continue
            price_str = match.group(2)
            parsed_data["items"].append({"name": name, "price": price_str})
            calculated_sum += Decimal(price_str)
            
    # Calculate confidence score based on the rules requested
    confidence = 0.0
    parsed_total = Decimal(parsed_data["total"])
    
    if parsed_total > Decimal('0.00'):
        if calculated_sum > Decimal('0.00') and calculated_sum == parsed_total:
            # Rule: 1.0 if total matches sum of items
            confidence = 1.0
        else:
            # Rule: 0.6 if total only
            confidence = 0.6
    else:
        # Rule: <0.5 if uncertain (0 in this case since we failed to parse anything meaningful)
        confidence = 0.3
        
    return parsed_data, confidence
