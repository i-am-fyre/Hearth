from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.household import Role

class HouseholdMemberBase(BaseModel):
    user_id: int
    role: Role

class HouseholdMemberCreate(BaseModel):
    email: str # Invite by email
    role: Role = Role.member

class HouseholdMemberResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    role: Role
    household_id: int
    email: str
    status: str = "active"

    model_config = ConfigDict(from_attributes=True)

class HouseholdBase(BaseModel):
    name: str

class HouseholdCreate(HouseholdBase):
    pass

class HouseholdResponse(HouseholdBase):
    id: int
    members: List[HouseholdMemberResponse] = []

    model_config = ConfigDict(from_attributes=True)
