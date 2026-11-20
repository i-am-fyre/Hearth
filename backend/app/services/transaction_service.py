from sqlalchemy.orm import Session
from decimal import Decimal
from fastapi import HTTPException
from app.models.transaction import Transaction, Entry
from app.models.account import Account
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.models.receipt import Receipt
from app.services.household_service import get_household_user_ids
from app.services.access import mark_editable, writable_accounts, writable_user_ids
from app.services.tag_service import get_tags_by_ids

def _check_receipt(db: Session, receipt_id: int | None, user_id: int) -> None:
    """A transaction may only point at one of the user's own receipts."""
    if receipt_id is None:
        return
    if not db.query(Receipt).filter(Receipt.id == receipt_id, Receipt.user_id == user_id).first():
        raise HTTPException(status_code=404, detail="Receipt not found")


def create_transaction(db: Session, transaction_in: TransactionCreate, user_id: int) -> Transaction:
    # 1. Total debits MUST equal total credits.
    total_debit = sum(entry.debit for entry in transaction_in.entries)
    total_credit = sum(entry.credit for entry in transaction_in.entries)

    # Reject transaction if imbalance > 0.0001
    imbalance = abs(total_debit - total_credit)
    if imbalance > Decimal('0.0001'):
        raise HTTPException(
            status_code=400,
            detail=f"Transaction unbalanced. Debits: {total_debit}, Credits: {total_credit}, Imbalance: {imbalance}"
        )

    # 2. Every account must be in the household and writable by this user
    #    (read-only members can't post to other members' accounts).
    writable_accounts(db, user_id, {entry.account_id for entry in transaction_in.entries})
    _check_receipt(db, transaction_in.receipt_id, user_id)

    # 3. Create Transaction
    db_transaction = Transaction(
        user_id=user_id,
        date=transaction_in.date,
        description=transaction_in.description,
        receipt_id=transaction_in.receipt_id
    )
    
    # Handle Transaction Tags
    if transaction_in.tag_ids:
        db_transaction.tags = get_tags_by_ids(db, transaction_in.tag_ids, user_id)
        
    db.add(db_transaction)
    db.flush() # Get transaction ID

    # 4. Create Entries
    for entry_in in transaction_in.entries:
        db_entry = Entry(
            transaction_id=db_transaction.id,
            account_id=entry_in.account_id,
            debit=entry_in.debit,
            credit=entry_in.credit,
            description=entry_in.description
        )
        
        # Handle Entry Tags (Cascade from transaction if requested, otherwise use entry's own tags)
        if transaction_in.cascade_tags_to_entries and transaction_in.tag_ids:
            db_entry.tags = db_transaction.tags
        elif entry_in.tag_ids:
            db_entry.tags = get_tags_by_ids(db, entry_in.tag_ids, user_id)
            
        db.add(db_entry)

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions(db: Session, user_id: int) -> list[Transaction]:
    user_ids = get_household_user_ids(db, user_id)
    transactions = db.query(Transaction).filter(Transaction.user_id.in_(user_ids)).all()
    return mark_editable(transactions, writable_user_ids(db, user_id))

def update_transaction(db: Session, db_txn: Transaction, transaction_in: TransactionUpdate, user_id: int) -> Transaction:
    # Validate before changing anything. New entries must use accounts this user
    # may post to; previously any account ID in the database was accepted.
    if transaction_in.entries is not None:
        writable_accounts(db, user_id, {entry.account_id for entry in transaction_in.entries})
    if transaction_in.receipt_id is not None and transaction_in.receipt_id != db_txn.receipt_id:
        _check_receipt(db, transaction_in.receipt_id, user_id)

    update_data = transaction_in.model_dump(exclude_unset=True)
    
    cascade_tags = update_data.pop("cascade_tags_to_entries", False)
    
    if "tag_ids" in update_data:
        tag_ids = update_data.pop("tag_ids")
        if tag_ids is not None:
            db_txn.tags = get_tags_by_ids(db, tag_ids, user_id)
        else:
            db_txn.tags = []
    
    # Handle entries separately if provided
    entries_data = update_data.pop("entries", None)
    if entries_data is not None:
        
        # 1. Total debits MUST equal total credits.
        total_debit = sum(Decimal(str(entry['debit'])) for entry in entries_data)
        total_credit = sum(Decimal(str(entry['credit'])) for entry in entries_data)

        if abs(total_debit - total_credit) > Decimal('0.0001'):
            raise HTTPException(
                status_code=400,
                detail=f"Updated transaction unbalanced. Debits: {total_debit}, Credits: {total_credit}"
            )
        
        # 2. Delete old entries
        db.query(Entry).filter(Entry.transaction_id == db_txn.id).delete()
        
        # 3. Create new entries
        for entry_in in entries_data:
            db_entry = Entry(
                transaction_id=db_txn.id,
                account_id=entry_in['account_id'],
                debit=entry_in['debit'],
                credit=entry_in['credit'],
                description=entry_in.get('description')
            )
            
            # Handle Entry Tags
            if cascade_tags and getattr(db_txn, 'tags', None):
                db_entry.tags = db_txn.tags
            elif entry_in.get('tag_ids'):
                db_entry.tags = get_tags_by_ids(db, entry_in['tag_ids'], user_id)
                
            db.add(db_entry)

    # Update other fields
    for field, value in update_data.items():
        setattr(db_txn, field, value)
        
    db.commit()
    db.refresh(db_txn)
    return db_txn

def delete_transaction(db: Session, db_txn: Transaction) -> bool:
    # 1. Nullify reverse reference in Receipt first to avoid foreign key constraint issues
    from app.models.receipt import Receipt
    db.query(Receipt).filter(Receipt.transaction_id == db_txn.id).update({"transaction_id": None})
    
    # 2. Nullify reference in BankTransaction and reset status
    from app.models.bank_transaction import BankTransaction, MatchStatus
    db.query(BankTransaction).filter(BankTransaction.matched_transaction_id == db_txn.id).update({
        "matched_transaction_id": None,
        "status": MatchStatus.unmatched
    })
    
    db.flush()
    
    # 3. Delete the transaction (entries will cascade delete automatically)
    db.delete(db_txn)
    db.commit()
    return True
