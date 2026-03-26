from pydantic import BaseModel
from typing import Optional

class ReconciliationRequest(BaseModel):
    bank_txn_id: int
    source_account_id: int # The bank account (e.g. Credit Card, Savings)
    target_account_id: int # The category (e.g. Food, Salary)
    amount: Optional[float] = None # Optionally pass in case user wants to override (but usually matches bank)
