import os
import json
from typing import Dict, Any, Tuple
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.core.config import settings

class ReceiptItem(BaseModel):
    name: str = Field(description="Name of the purchased item")
    price: str = Field(description="Price of the item formatted as a string without currency symbols, e.g., '12.34'")

class ReceiptData(BaseModel):
    merchant: str = Field(description="Name of the store or merchant")
    date: str = Field(description="Date of the transaction formatted STRICTLY as YYYY-MM-DD. Convert dates like 02/23/2026 to 2026-02-23 so it perfectly parses.")
    currency: str = Field(description="3-letter currency code (e.g., USD, CAD, EUR). Default to USD if unknown.")
    items: list[ReceiptItem] = Field(description="List of all purchased items on the receipt.")
    subtotal: str = Field(description="Subtotal amount before tax formatted as a string.")
    tax: str = Field(description="Total tax amount formatted as a string.")
    total: str = Field(description="Final total amount paid formatted as a string.")

def parse_receipt_with_gemini(image_bytes: bytes, mime_type: str = "image/jpeg") -> Tuple[str, Dict[str, Any], float]:
    """
    Parse a receipt image using Gemini 1.5 Flash.
    Returns (raw_text, parsed_json_dict, confidence_score).
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")
        
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = """
    Carefully transcribe this receipt. Identify the merchant, exact transaction date, currency, and extract EVERY single line item purchased into the requested schema. 
    
    CRITICAL TAX INSTRUCTION: 
    If there are taxes (like GST/PST) applied to specific items on the receipt (e.g., a $3 Deli item with 12% tax listed at the bottom), you must calculate and add that proportional tax directly into the individual item's `price`. The final sum of all item prices in your JSON array MUST exactly equal the total amount paid. Do not list "Tax" as a separate line item if it can be allocated to the items it belongs to.
    """
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ReceiptData,
            temperature=0.1,
        )
    )
    
    raw_text = response.text
    parsed_data = json.loads(raw_text.strip())
    confidence = 0.95 
    return raw_text, parsed_data, confidence
