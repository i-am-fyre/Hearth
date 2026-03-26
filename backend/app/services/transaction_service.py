from sqlalchemy.orm import Session
from decimal import Decimal
from fastapi import HTTPException
from app.models.transaction import Transaction, Entry
from app.models.account import Account
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.household_service import get_household_user_ids

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

    # 2. Verify all accounts belong to the user's household
    account_ids = {entry.account_id for entry in transaction_in.entries}
    user_ids = get_household_user_ids(db, user_id)
    accounts = db.query(Account).filter(Account.id.in_(account_ids), Account.user_id.in_(user_ids)).all()
    if len(accounts) != len(account_ids):
        raise HTTPException(status_code=400, detail="One or more accounts not found or do not belong to you or your household.")

    # 3. Create Transaction
    db_transaction = Transaction(
        user_id=user_id,
        date=transaction_in.date,
        description=transaction_in.description,
        receipt_id=transaction_in.receipt_id
    )
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
        db.add(db_entry)

    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions(db: Session, user_id: int) -> list[Transaction]:
    user_ids = get_household_user_ids(db, user_id)
    return db.query(Transaction).filter(Transaction.user_id.in_(user_ids)).all()

def update_transaction(db: Session, db_txn: Transaction, transaction_in: TransactionUpdate) -> Transaction:
    update_data = transaction_in.model_dump(exclude_unset=True)
    
    # Handle entries separately if provided
    if "entries" in update_data:
        entries_data = update_data.pop("entries")
        
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
