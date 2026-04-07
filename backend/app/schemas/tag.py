from pydantic import BaseModel, constr
from typing import Optional

class TagBase(BaseModel):
    name: str
    color_hex: constr(pattern=r'^#[0-9a-fA-F]{6}$') = "#3b82f6"

class TagCreate(TagBase):
    pass

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color_hex: Optional[constr(pattern=r'^#[0-9a-fA-F]{6}$')] = None

class TagResponse(TagBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
