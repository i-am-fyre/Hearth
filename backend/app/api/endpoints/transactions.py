from typing import Any
from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate
from app.services import transaction_service
from app.services.household_service import get_household_user_ids

router = APIRouter()

@router.post("/", response_model=TransactionResponse)
def create_transaction(
    *,
    db: SessionDep,
    transaction_in: TransactionCreate,
    current_user: CurrentUser,
) -> Any:
    """
    Create new transaction with double-entry validation.
    """
    transaction = transaction_service.create_transaction(
        db=db, transaction_in=transaction_in, user_id=current_user.id
    )
    return transaction

@router.get("/", response_model=list[TransactionResponse])
def read_transactions(
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Retrieve transactions for user.
    """
    transactions = transaction_service.get_transactions(db=db, user_id=current_user.id)
    return transactions

@router.patch("/{id}", response_model=TransactionResponse)
def update_transaction(
    *,
    db: SessionDep,
    id: int,
    transaction_in: TransactionUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update a transaction.
    """
    user_ids = get_household_user_ids(db, current_user.id)
    db_txn = db.query(transaction_service.Transaction).filter(
        transaction_service.Transaction.id == id,
        transaction_service.Transaction.user_id.in_(user_ids)
    ).first()
    if not db_txn:
        raise HTTPException(status_code=404, detail="Transaction not found or not in your household")
    
    transaction = transaction_service.update_transaction(
        db=db, db_txn=db_txn, transaction_in=transaction_in, user_id=current_user.id
    )
    return transaction

@router.delete("/{id}")
def delete_transaction(
    *,
    db: SessionDep,
    id: int,
    current_user: CurrentUser,
) -> Any:
    """
    Delete a transaction.
    """
    user_ids = get_household_user_ids(db, current_user.id)
    db_txn = db.query(transaction_service.Transaction).filter(
        transaction_service.Transaction.id == id,
        transaction_service.Transaction.user_id.in_(user_ids)
    ).first()
    if not db_txn:
        raise HTTPException(status_code=404, detail="Transaction not found or not in your household")
    
    transaction_service.delete_transaction(db=db, db_txn=db_txn)
    return {"status": "success"}
