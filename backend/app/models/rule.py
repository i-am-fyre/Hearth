from sqlalchemy import String, Integer, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Store conditions and actions as flexible JSON blocks
    # Example Condition: {"merchant_contains": "Walmart", "amount_less_than": 200}
    # Example Action: {"assign_account_id": 5}
    condition_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    action_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_post: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship()
