from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from app.schemas.transaction import TransactionResponse

class ReceiptAttach(BaseModel):
    transaction_id: int

class ReceiptResponse(BaseModel):
    id: int
    user_id: int
    transaction_id: Optional[int]
    original_filename: str
    mime_type: str
    ocr_text: Optional[str]
    parsed_json: Optional[str]
    confidence_score: Optional[float]
    status: str
    created_at: datetime
    
    potential_matches: Optional[List[TransactionResponse]] = []
    
    model_config = ConfigDict(from_attributes=True)
