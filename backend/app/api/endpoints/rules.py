from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import CurrentUser, SessionDep
from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate
from app.services.access import readable_accounts, writable_accounts


def _check_rule_account(db, user_id: int, action_json, auto_post: bool) -> None:
    """A rule may suggest any account the user can see, but auto-posting writes to
    it, so that needs an account the user may post to."""
    acc_id = (action_json or {}).get("assign_account_id")
    if acc_id is None:
        return
    try:
        acc_id = int(acc_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="assign_account_id must be an account id")
    if auto_post:
        writable_accounts(db, user_id, [acc_id])
    else:
        readable_accounts(db, user_id, [acc_id])

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
    _check_rule_account(db, current_user.id, rule_in.action_json, rule_in.auto_post)
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
    _check_rule_account(db, current_user.id, db_rule.action_json, db_rule.auto_post)
    
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
