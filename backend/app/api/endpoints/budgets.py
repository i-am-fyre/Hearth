from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any
from app.api.deps import CurrentUser, SessionDep
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetLineCreate
from app.services import budget_service

router = APIRouter()

@router.get("/", response_model=List[BudgetResponse])
def read_budgets(
    db: SessionDep,
    current_user: CurrentUser,
):
    return budget_service.get_budgets(db, current_user.id)

@router.post("/", response_model=BudgetResponse)
def create_budget(
    budget_in: BudgetCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    return budget_service.create_budget(db, budget_in, current_user.id)

@router.post("/{budget_id}/lines")
def add_line(
    budget_id: int,
    line_in: BudgetLineCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    return budget_service.create_budget_line(db, line_in, budget_id, current_user.id)

@router.get("/{budget_id}/variance")
def get_variance(
    budget_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    return budget_service.calculate_budget_variance(db, budget_id, current_user.id)

@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    budget_service.delete_budget(db, budget_id, current_user.id)
    return {"status": "ok"}
