from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import CurrentUser, SessionDep
from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter()

@router.get("/", response_model=List[RuleResponse])
def read_rules(
    db: SessionDep,
    current_user: CurrentUser,
):
    return db.query(Rule).filter(Rule.user_id == current_user.id).order_by(Rule.priority.desc()).all()

@router.post("/", response_model=RuleResponse)
def create_rule(
    rule_in: RuleCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    db_rule = Rule(
        user_id=current_user.id,
        priority=rule_in.priority,
        condition_json=rule_in.condition_json,
        action_json=rule_in.action_json,
        active=rule_in.active,
        auto_post=rule_in.auto_post
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.patch("/{rule_id}", response_model=RuleResponse)
def update_rule(
    rule_id: int,
    rule_in: RuleUpdate,
    db: SessionDep,
    current_user: CurrentUser,
):
    db_rule = db.query(Rule).filter(Rule.id == rule_id, Rule.user_id == current_user.id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    db_rule = db.query(Rule).filter(Rule.id == rule_id, Rule.user_id == current_user.id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(db_rule)
    db.commit()
    return {"status": "ok"}
