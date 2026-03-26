from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from app.models.account import AccountType

class AccountBase(BaseModel):
    name: str
    type: AccountType
    currency: str = "USD"

class AccountCreate(AccountBase):
    pass

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[AccountType] = None
    currency: Optional[str] = None

class AccountResponse(AccountBase):
    id: int
    user_id: int
    balance: Decimal = Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)
