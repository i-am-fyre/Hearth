from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from decimal import Decimal

class BudgetLineBase(BaseModel):
    account_id: int
    planned_amount: Decimal

class BudgetLineCreate(BudgetLineBase):
    pass

class BudgetLineResponse(BudgetLineBase):
    id: int
    budget_id: int
    actual_amount: Decimal = Decimal("0.00") # Calculated in service

    model_config = ConfigDict(from_attributes=True)

class BudgetBase(BaseModel):
    name: str
    month: int
    year: int

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    lines: List[BudgetLineResponse] = []

    model_config = ConfigDict(from_attributes=True)
