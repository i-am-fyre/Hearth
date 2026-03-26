from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, List

class RuleBase(BaseModel):
    priority: int = 0
    condition_json: Dict[str, Any]
    action_json: Dict[str, Any]
    active: bool = True
    auto_post: bool = False

class RuleCreate(RuleBase):
    pass

class RuleUpdate(BaseModel):
    priority: Optional[int] = None
    condition_json: Optional[Dict[str, Any]] = None
    action_json: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None
    auto_post: Optional[bool] = None

class RuleResponse(RuleBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
