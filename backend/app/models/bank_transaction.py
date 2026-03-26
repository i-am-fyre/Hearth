import enum
from datetime import date
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, Date, Numeric, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class MatchStatus(str, enum.Enum):
    unmatched = "unmatched"
    matched = "matched"
    flagged = "flagged"

class BankTransaction(Base):
    __tablename__ = "bank_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    
    matched_transaction_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=True)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.unmatched, nullable=False)
    
    suggested_account_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suggested_account_name: Mapped[str | None] = mapped_column(String, nullable=True)

    user: Mapped["User"] = relationship()
    transaction: Mapped["Transaction"] = relationship()
