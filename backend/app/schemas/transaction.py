from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import date as datetime_date
from typing import List, Self, Optional
from decimal import Decimal
from app.schemas.tag import TagResponse

class EntryBase(BaseModel):
    account_id: int
    debit: Decimal = Field(default=Decimal('0.00'), max_digits=18, decimal_places=2)
    credit: Decimal = Field(default=Decimal('0.00'), max_digits=18, decimal_places=2)
    description: str | None = None
    tag_ids: Optional[List[int]] = None

    @model_validator(mode='after')
    def check_non_zero_balance(self) -> Self:
        if self.debit != Decimal('0.00') and self.credit != Decimal('0.00'):
            raise ValueError("Entry cannot have both debit and credit greater than zero.")
        return self

class EntryCreate(EntryBase):
    pass

class EntryResponse(EntryBase):
    id: int
    transaction_id: int
    tags: List[TagResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TransactionBase(BaseModel):
    date: datetime_date
    description: str
    receipt_id: int | None = None
    tag_ids: Optional[List[int]] = None
    cascade_tags_to_entries: bool = False

class TransactionCreate(TransactionBase):
    entries: List[EntryCreate]

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    entries: List[EntryResponse]
    tags: List[TagResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TransactionUpdate(BaseModel):
    description: str | None = None
    date: datetime_date | None = None
    receipt_id: int | None = None
    entries: List[EntryCreate] | None = None
    tag_ids: Optional[List[int]] = None
    cascade_tags_to_entries: bool = False
