from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import Optional
from app.models.bank_transaction import MatchStatus

class BankTransactionResponse(BaseModel):
    id: int
    user_id: int
    date: date
    description: str
    amount: Decimal
    matched_transaction_id: Optional[int]
    status: MatchStatus
    suggested_account_id: Optional[int] = None
    suggested_account_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
