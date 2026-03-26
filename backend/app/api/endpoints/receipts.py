from fastapi import APIRouter, UploadFile, File, Response, BackgroundTasks
from typing import Any, List
from app.api.deps import CurrentUser, SessionDep
from app.schemas.receipt import ReceiptResponse, ReceiptAttach
from app.services import receipt_service

router = APIRouter()

@router.post("/", response_model=ReceiptResponse)
async def upload_receipt(
    db: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
) -> Any:
    """
    Upload a receipt image. File is encrypted before storage.
    Processing happens in the background.
    """
    content = await file.read()
    file_hash = receipt_service.calculate_file_hash(content)
    
    # Check if duplicate exists before storing file
    receipt = receipt_service.create_receipt_record(
        db=db, 
        user=current_user, 
        file_path="", # Will be updated if not duplicate
        filename=file.filename, 
        mime_type=file.content_type,
        file_hash=file_hash
    )
    
    # If the receipt already has a file_path, it's a duplicate
    if receipt.file_path:
        # If it was failed, maybe re-trigger?
        if receipt.status == "failed":
            receipt.status = "pending"
            db.commit()
            background_tasks.add_task(receipt_service.process_receipt_background, receipt.id)
        return receipt

    # Not a duplicate, store and update
    file_path = receipt_service.store_receipt_file(content, current_user, file.filename)
    receipt.file_path = file_path
    db.commit()
    
    # Trigger background AI processing
    background_tasks.add_task(receipt_service.process_receipt_background, receipt.id)
    
    return receipt

@router.post("/batch", response_model=List[ReceiptResponse])
async def upload_receipts_batch(
    db: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
) -> Any:
    """
    Upload multiple receipt images.
    """
    results = []
    for file in files:
        content = await file.read()
        file_hash = receipt_service.calculate_file_hash(content)
        
        receipt = receipt_service.create_receipt_record(
            db=db, 
            user=current_user, 
            file_path="", 
            filename=file.filename, 
            mime_type=file.content_type,
            file_hash=file_hash
        )
        
        if not receipt.file_path:
            file_path = receipt_service.store_receipt_file(content, current_user, file.filename)
            receipt.file_path = file_path
            db.commit()
            background_tasks.add_task(receipt_service.process_receipt_background, receipt.id)
        elif receipt.status == "failed":
            receipt.status = "pending"
            db.commit()
            background_tasks.add_task(receipt_service.process_receipt_background, receipt.id)
            
        results.append(receipt)
        
    return results

@router.get("/", response_model=List[ReceiptResponse])
def get_receipts(
    db: SessionDep,
    current_user: CurrentUser,
    status: str = None
) -> Any:
    """
    Get all receipts (default: only those not yet linked to a transaction).
    """
    return receipt_service.get_receipts_by_status(db, current_user.id, status)

@router.get("/{receipt_id}/download", response_class=Response)
def download_receipt(
    receipt_id: int,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Download a decrypted receipt image.
    """
    receipt = receipt_service.get_receipt(db, receipt_id, current_user.id)
    decrypted_content = receipt_service.read_decrypted_receipt(receipt, current_user)
    
    return Response(content=decrypted_content, media_type=receipt.mime_type)

@router.patch("/{receipt_id}/attach", response_model=ReceiptResponse)
def attach_receipt(
    receipt_id: int,
    attach_in: ReceiptAttach,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Attach a receipt to a transaction.
    """
    receipt = receipt_service.get_receipt(db, receipt_id, current_user.id)
    receipt = receipt_service.attach_to_transaction(db, receipt, attach_in.transaction_id, current_user.id)
    return receipt

@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int,
    db: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Delete a receipt and its associated file.
    """
    receipt_service.delete_receipt(db, receipt_id, current_user.id)
    return {"message": "Receipt deleted successfully"}

@router.post("/reprocess")
def reprocess_stuck_receipts(
    db: SessionDep,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Re-trigger processing for all pending or failed receipts.
    """
    pending = db.query(Receipt).filter(
        Receipt.user_id == current_user.id,
        Receipt.status.in_(["pending", "failed"])
    ).all()
    
    for r in pending:
        r.status = "pending"
        background_tasks.add_task(receipt_service.process_receipt_background, r.id)
    
    db.commit()
    return {"message": f"Queued {len(pending)} receipts for re-processing"}
