from sqlalchemy import String, Integer, ForeignKey, Date, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from app.db.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship()
    lines: Mapped[list["BudgetLine"]] = relationship(back_populates="budget", cascade="all, delete-orphan")

class BudgetLine(Base):
    __tablename__ = "budget_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    budget_id: Mapped[int] = mapped_column(Integer, ForeignKey("budgets.id"), nullable=False, index=True)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    
    planned_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    budget: Mapped["Budget"] = relationship(back_populates="lines")
    account: Mapped["Account"] = relationship()
