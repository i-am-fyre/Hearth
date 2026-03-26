from pydantic import BaseModel
from typing import Optional

class MappingConfig(BaseModel):
    has_header: bool = True
    date_col: int = 0
    desc_col: int = 1
    amount_col: Optional[int] = None
    debit_col: Optional[int] = None
    credit_col: Optional[int] = None
    date_format: str = "%Y-%m-%d"
    source_account_id: Optional[int] = None
