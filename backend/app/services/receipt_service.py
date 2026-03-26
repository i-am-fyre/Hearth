import os
import uuid
from typing import BinaryIO
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.receipt import Receipt
from app.models.transaction import Transaction
from app.models.user import User
from app.services.crypto_service import encrypt_data, decrypt_data
import hashlib
from app.db.database import SessionLocal

STORAGE_DIR = "storage/receipts"

def calculate_file_hash(file_content: bytes) -> str:
    """Calculates SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()

def store_receipt_file(file_content: bytes, user: User, original_filename: str) -> str:
    """Encrypts and saves the receipt to the filesystem, returns the path."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    filename = f"{uuid.uuid4()}_{original_filename}.enc"
    file_path = os.path.join(STORAGE_DIR, filename)

    if not user.encryption_key:
        raise ValueError("User missing encryption key.")

    encrypted_content = encrypt_data(file_content, user.encryption_key)

    with open(file_path, "wb") as f:
        f.write(encrypted_content)

    return file_path

def get_receipt(db: Session, receipt_id: int, user_id: int) -> Receipt:
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == user_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt

def create_receipt_record(db: Session, user: User, file_path: str, filename: str, mime_type: str, file_hash: str = None) -> Receipt:
    # Check for duplicates
    if file_hash:
        existing = db.query(Receipt).filter(Receipt.user_id == user.id, Receipt.file_hash == file_hash).first()
        if existing:
            # If it's already linked to a transaction, maybe we allow a new one? 
            # Or just return existing. Usually, same file for same user is a duplicate.
            return existing

    db_receipt = Receipt(
        user_id=user.id,
        file_path=file_path,
        original_filename=filename,
        mime_type=mime_type,
        status="pending",
        file_hash=file_hash
    )
    db.add(db_receipt)
    db.commit()
    db.refresh(db_receipt)
    return db_receipt

def process_receipt_background(receipt_id: int):
    """
    Background task to perform AI/OCR parsing on a receipt.
    Uses its own DB session to avoid "Session is closed" errors.
    """
    db = SessionLocal()
    try:
        db_receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if not db_receipt:
            print(f"DEBUG: Background task failed - receipt {receipt_id} not found.")
            return

        user = db.query(User).filter(User.id == db_receipt.user_id).first()
        if not user:
            print(f"DEBUG: Background task failed - user for receipt {receipt_id} not found.")
            return

        db_receipt.status = "processing"
        db.commit()

        # Decrypt content for processing
        decrypted_content = read_decrypted_receipt(db_receipt, user)
        
        if "image" in db_receipt.mime_type.lower():
            from app.core.config import settings
            import json
            
            parsed_successfully = False
            
            if settings.GEMINI_API_KEY:
                from app.services.ai_receipt_service import parse_receipt_with_gemini
                print(f"DEBUG: Starting Gemini AI parsing for receipt {db_receipt.original_filename}")
                try:
                    raw_text, parsed_dict, confidence = parse_receipt_with_gemini(decrypted_content, db_receipt.mime_type)
                    parsed_dict["extraction_method"] = "Gemini 2.5 Flash"
                    db_receipt.ocr_text = raw_text
                    db_receipt.parsed_json = json.dumps(parsed_dict)
                    db_receipt.confidence_score = confidence
                    db_receipt.status = "processed"
                    print(f"DEBUG: Gemini Parsed: {parsed_dict} Confidence: {confidence}")
                    parsed_successfully = True
                except Exception as e:
                    print(f"DEBUG: Gemini AI failed: {e}. Falling back to Tesseract OCR.")
                    
            if not parsed_successfully:
                from app.services.ocr_service import run_ocr, parse_receipt_text
                
                print(f"DEBUG: Starting Tesseract OCR for receipt {db_receipt.original_filename}")
                ocr_text = run_ocr(decrypted_content)
                if ocr_text:
                    print(f"DEBUG: OCR text found, length: {len(ocr_text)}")
                    parsed_dict, confidence = parse_receipt_text(ocr_text)
                    parsed_dict["extraction_method"] = "Tesseract OCR"
                    db_receipt.ocr_text = ocr_text
                    db_receipt.parsed_json = json.dumps(parsed_dict)
                    db_receipt.confidence_score = confidence
                    db_receipt.status = "processed"
                    print(f"DEBUG: OCR Parsed: {parsed_dict} Confidence: {confidence}")
                else:
                    print(f"DEBUG: OCR failed - no text extracted from {db_receipt.original_filename}")
                    db_receipt.status = "failed"
        else:
            db_receipt.status = "processed" # Non-image files might not need OCR but we mark them as processed
            
    except Exception as e:
        print(f"DEBUG: Background processing failed for receipt {receipt_id}: {e}")
        db_receipt.status = "failed"
    
    finally:
        db.commit()
        db.close()

def get_receipts_by_status(db: Session, user_id: int, status: str = None) -> list[Receipt]:
    query = db.query(Receipt).filter(Receipt.user_id == user_id)
    if status:
        query = query.filter(Receipt.status == status)
    else:
        # Default: Return all that haven't been linked to a transaction yet (the "Review Center")
        query = query.filter(Receipt.transaction_id == None)
        
    receipts = query.all()
    
    # Attach potential matches to each receipt for the frontend
    for r in receipts:
        attach_potential_matches(db, r, user_id)
        
    return receipts

def attach_potential_matches(db: Session, db_receipt: Receipt, user_id: int):
    db_receipt.potential_matches = []
    if not db_receipt.parsed_json:
        return

    try:
        import json
        from datetime import datetime, timedelta
        from decimal import Decimal
        pdict = json.loads(db_receipt.parsed_json)
        date_str = pdict.get("date")
        total_str = pdict.get("total")
        r_merchant = pdict.get("merchant", "").lower()

        if date_str and total_str:
            r_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            r_total = Decimal(str(total_str))
            start_date = r_date - timedelta(days=3)
            end_date = r_date + timedelta(days=3)
            
            txns = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.receipt_id == None,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).all()
            
            matches = []
            for txn in txns:
                amount = sum(e.debit for e in txn.entries)
                if abs(amount - r_total) <= Decimal('0.05'):
                    if not r_merchant or r_merchant in txn.description.lower() or txn.description.lower() in r_merchant:
                        matches.append(txn)
            
            db_receipt.potential_matches = matches
    except Exception as e:
        print(f"DEBUG: Match finding failed: {e}")

def read_decrypted_receipt(receipt: Receipt, user: User) -> bytes:
    if not os.path.exists(receipt.file_path):
        raise HTTPException(status_code=404, detail="Receipt file not found on disk")
        
    with open(receipt.file_path, "rb") as f:
        encrypted_content = f.read()

    return decrypt_data(encrypted_content, user.encryption_key)

def attach_to_transaction(db: Session, receipt: Receipt, transaction_id: int, user_id: int) -> Receipt:
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id, Transaction.user_id == user_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found or does not belong to user")
        
    # Bi-directional link
    receipt.transaction_id = transaction.id
    transaction.receipt_id = receipt.id
    receipt.status = "completed"
    
    db.commit()
    db.refresh(receipt)
    return receipt

def delete_receipt(db: Session, receipt_id: int, user_id: int) -> bool:
    receipt = db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == user_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
        
    # Nullify references in transactions
    db.query(Transaction).filter(Transaction.receipt_id == receipt_id).update({"receipt_id": None})
    
    # Delete the physical file if it exists
    if os.path.exists(receipt.file_path):
        os.remove(receipt.file_path)
        
    db.delete(receipt)
    db.commit()
    return True
