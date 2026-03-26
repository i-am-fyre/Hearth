from typing import Dict, Any, List
from sqlalchemy.orm import Session
from decimal import Decimal
from app.models.rule import Rule
from app.models.user import User

def evaluate_conditions(conditions: Dict[str, Any], data: Dict[str, Any]) -> bool:
    """Evaluate a JSON condition block against a flat data dictionary."""
    for key, expected_val in conditions.items():
        if key == "merchant_contains":
            merchant = str(data.get("merchant", "")).lower()
            if str(expected_val).lower() not in merchant:
                return False
        elif key == "amount_less_than":
            amount = Decimal(str(data.get("amount", "0")))
            if amount >= Decimal(str(expected_val)):
                return False
        elif key == "amount_greater_than":
            amount = Decimal(str(data.get("amount", "0")))
            if amount <= Decimal(str(expected_val)):
                return False
        # Future conditions can be added here
        else:
            return False
            
    return True

def apply_rules(db: Session, user: User, source_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch all active rules for the user, sort by priority (highest first),
    evaluate them sequentially, and apply the first matching action.
    Returns a dictionary including the actions and auto_post status.
    """
    rules = db.query(Rule).filter(Rule.user_id == user.id, Rule.active == True)\
              .order_by(Rule.priority.desc()).all()
              
    for rule in rules:
        if evaluate_conditions(rule.condition_json, source_data):
            return {
                "actions": rule.action_json,
                "auto_post": rule.auto_post
            }
            
    return {"actions": {}, "auto_post": False}
