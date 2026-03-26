from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Integer, ForeignKey, Numeric, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    receipt_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("receipts.id"), nullable=True)

    user: Mapped["User"] = relationship(back_populates="transactions")
    entries: Mapped[list["Entry"]] = relationship(back_populates="transaction", cascade="all, delete-orphan")

class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal('0.00'), nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    transaction: Mapped["Transaction"] = relationship(back_populates="entries")
    account: Mapped["Account"] = relationship(back_populates="entries")
