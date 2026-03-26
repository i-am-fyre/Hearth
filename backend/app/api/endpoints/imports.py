from fastapi import APIRouter, UploadFile, File, Form, Body
from typing import Any, List, Optional
import json
from app.api.deps import CurrentUser, SessionDep
from app.schemas.bank_transaction import BankTransactionResponse
from app.schemas.import_config import MappingConfig
from app.schemas.reconciliation import ReconciliationRequest
from app.services import import_service

router = APIRouter()

@router.get("/unmatched", response_model=List[BankTransactionResponse])
async def list_unmatched_transactions(
    db: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    List bank transactions that haven't been reconciled yet.
    """
    return import_service.get_unmatched_transactions(db, current_user.id)

@router.post("/reconcile")
async def reconcile_bank_transaction(
    db: SessionDep,
    current_user: CurrentUser,
    request: ReconciliationRequest
) -> Any:
    """
    Reconcile a bank transaction by posting it to the core ledger.
    """
    try:
        txn = import_service.reconcile_transaction(
            db, 
            current_user, 
            request.bank_txn_id, 
            request.source_account_id, 
            request.target_account_id
        )
        return {"status": "success", "transaction_id": txn.id}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/bulk")
async def bulk_delete_bank_transactions(
    db: SessionDep,
    current_user: CurrentUser
) -> Any:
    """
    Discard all unreconciled bank transactions for the current user.
    """
    from app.models.bank_transaction import BankTransaction, MatchStatus
    db.query(BankTransaction).filter(
        BankTransaction.user_id == current_user.id,
        BankTransaction.status != MatchStatus.matched
    ).delete()
    db.commit()
    return {"status": "success"}

@router.delete("/{bank_txn_id}")
async def delete_bank_transaction(
    db: SessionDep,
    current_user: CurrentUser,
    bank_txn_id: int
) -> Any:
    """
    Discard an unreconciled bank transaction.
    """
    from app.models.bank_transaction import BankTransaction
    txn = db.query(BankTransaction).filter(
        BankTransaction.id == bank_txn_id,
        BankTransaction.user_id == current_user.id
    ).first()
    
    if not txn:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    db.delete(txn)
    db.commit()
    return {"status": "success"}

@router.post("/preview")
async def get_import_preview(
    file: UploadFile = File(...)
) -> Any:
    """
    Get a preview of the CSV file to help with mapping.
    """
    content = await file.read()
    preview = import_service.get_csv_preview(content)
    return {"preview": preview}

@router.post("/csv", response_model=List[BankTransactionResponse])
async def upload_bank_csv(
    db: SessionDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
    config: str = Form(...) # JSON string of MappingConfig
) -> Any:
    """
    Upload a bank CSV with mapping configuration.
    """
    content = await file.read()
    mapping_config = MappingConfig.model_validate_json(config)
    results = import_service.process_csv_import(db, current_user, content, mapping_config)
    return results
