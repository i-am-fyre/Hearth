import enum
from sqlalchemy import String, Integer, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

class Role(str, enum.Enum):
    owner = "owner"
    member = "member"
    read_only = "read_only"

class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    members: Mapped[list["HouseholdMember"]] = relationship(back_populates="household", cascade="all, delete-orphan")


class HouseholdMember(Base):
    __tablename__ = "household_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    household_id: Mapped[int] = mapped_column(Integer, ForeignKey("households.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.member, nullable=False)

    household: Mapped["Household"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship()

class HouseholdInvitation(Base):
    __tablename__ = "household_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    household_id: Mapped[int] = mapped_column(Integer, ForeignKey("households.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.member, nullable=False)

    household: Mapped["Household"] = relationship()
