from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from fastapi import HTTPException
from app.models.budget import Budget, BudgetLine
from app.models.user import User
from app.models.transaction import Transaction, Entry
from decimal import Decimal
from typing import Dict, Any, List
from app.services.household_service import get_household_user_ids
from app.schemas.budget import BudgetCreate, BudgetLineCreate

def calculate_budget_variance(db: Session, budget_id: int, user_id: int) -> Dict[str, Any]:
    """Calculate planned vs actuals for a specific budget month."""
    user_ids = get_household_user_ids(db, user_id)
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id.in_(user_ids)).first()
    if not budget:
        return {}

    results = {
        "budget_name": budget.name,
        "period": f"{budget.year}-{budget.month:02d}",
        "lines": [],
        "total_planned": Decimal('0.00'),
        "total_actual": Decimal('0.00'),
        "total_variance": Decimal('0.00')
    }

    for line in budget.lines:
        # Sum all debits for this account in this month
        actual_spent = db.query(func.sum(Entry.debit)).join(Transaction).filter(
            Entry.account_id == line.account_id,
            Transaction.user_id.in_(user_ids),
            extract('year', Transaction.date) == budget.year,
            extract('month', Transaction.date) == budget.month
        ).scalar() or Decimal('0.00')

        variance = line.planned_amount - actual_spent

        results["lines"].append({
            "account_name": line.account.name,
            "planned": line.planned_amount,
            "actual": actual_spent,
            "variance": variance
        })

        results["total_planned"] += line.planned_amount
        results["total_actual"] += actual_spent

    results["total_variance"] = results["total_planned"] - results["total_actual"]
    return results

def get_budgets(db: Session, user_id: int) -> List[Budget]:
    user_ids = get_household_user_ids(db, user_id)
    return db.query(Budget).filter(Budget.user_id.in_(user_ids)).all()

def create_budget(db: Session, budget_in: BudgetCreate, user_id: int) -> Budget:
    db_budget = Budget(
        user_id=user_id,
        name=budget_in.name,
        month=budget_in.month,
        year=budget_in.year
    )
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

def create_budget_line(db: Session, line_in: BudgetLineCreate, budget_id: int, user_id: int) -> BudgetLine:
    from app.models.account import Account
    user_ids = get_household_user_ids(db, user_id)
    
    # 1. Verify budget belongs to household
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id.in_(user_ids)).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
        
    # 2. Verify account belongs to household
    account = db.query(Account).filter(Account.id == line_in.account_id, Account.user_id.in_(user_ids)).first()
    if not account:
        raise HTTPException(status_code=400, detail="Account not found or not in your household")

    db_line = BudgetLine(
        budget_id=budget_id,
        account_id=line_in.account_id,
        planned_amount=line_in.planned_amount
    )
    db.add(db_line)
    db.commit()
    db.refresh(db_line)
    return db_line

def delete_budget(db: Session, budget_id: int, user_id: int):
    user_ids = get_household_user_ids(db, user_id)
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id.in_(user_ids)).first()
    if budget:
        db.delete(budget)
        db.commit()

