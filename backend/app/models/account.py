import enum
from sqlalchemy import String, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class AccountType(str, enum.Enum):
    asset = "asset"
    liability = "liability"
    income = "income"
    expense = "expense"
    equity = "equity"

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    currency: Mapped[str] = mapped_column(String, default="USD", nullable=False)

    user: Mapped["User"] = relationship(back_populates="accounts")
    entries: Mapped[list["Entry"]] = relationship(back_populates="account")
