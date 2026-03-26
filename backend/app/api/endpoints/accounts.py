from typing import Any
from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.schemas.account import AccountCreate, AccountUpdate, AccountResponse
from app.services import account_service
from app.services.household_service import get_household_user_ids

router = APIRouter()

@router.post("/", response_model=AccountResponse)
def create_account(
    *,
    db: SessionDep,
    account_in: AccountCreate,
    current_user: CurrentUser,
) -> Any:
    """
    Create new account.
    """
    account = account_service.create_account(db=db, account_in=account_in, user_id=current_user.id)
    return account

@router.get("/{id}", response_model=AccountResponse)
def read_account(
    *,
    db: SessionDep,
    id: int,
    current_user: CurrentUser,
) -> Any:
    user_ids = get_household_user_ids(db, current_user.id)
    account = db.query(account_service.Account).filter(
        account_service.Account.id == id,
        account_service.Account.user_id.in_(user_ids)
    ).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found or not in your household")
    # Balance calculation is done in service, but let's just use service if needed.
    # Actually get_accounts calls calculate balance for all.
    # For a single one, let's just returning the one from get_accounts (inefficient but works)
    accounts = account_service.get_accounts(db, current_user.id)
    for a in accounts:
        if a.id == id:
            return a
    raise HTTPException(status_code=404, detail="Account not found")


@router.get("/", response_model=list[AccountResponse])
def read_accounts(
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Retrieve accounts for user.
    """
    accounts = account_service.get_accounts(db=db, user_id=current_user.id)
    return accounts

@router.put("/{id}", response_model=AccountResponse)
def update_account(
    *,
    db: SessionDep,
    id: int,
    account_in: AccountUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update an account.
    """
    account = account_service.update_account(db=db, account_id=id, account_in=account_in, user_id=current_user.id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.delete("/{id}")
def delete_account(
    *,
    db: SessionDep,
    id: int,
    current_user: CurrentUser,
) -> Any:
    """
    Delete an account.
    """
    try:
        success = account_service.delete_account(db=db, account_id=id, user_id=current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
