from decimal import Decimal
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.account import Account, AccountType
from app.models.transaction import Entry
from app.schemas.account import AccountCreate, AccountUpdate
from app.services.household_service import get_household_user_ids

def create_account(db: Session, account_in: AccountCreate, user_id: int) -> Account:
    db_account = Account(
        **account_in.model_dump(),
        user_id=user_id
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def get_accounts(db: Session, user_id: int) -> list[Account]:
    user_ids = get_household_user_ids(db, user_id)
    accounts = db.query(Account).filter(Account.user_id.in_(user_ids)).all()
    # In-place sorting to put current user's accounts first? 
    # Let's just keep it simple for now and just return shared accounts.

    
    for account in accounts:
        # Calculate debits and credits
        sums = db.query(
            func.sum(Entry.debit).label("debits"),
            func.sum(Entry.credit).label("credits")
        ).filter(Entry.account_id == account.id).first()
        
        debits = sums.debits or Decimal("0.00")
        credits = sums.credits or Decimal("0.00")
        
        # Balance = Debits - Credits for Assets and Expenses
        if account.type in [AccountType.asset, AccountType.expense]:
            account.balance = debits - credits
        else:
            # Balance = Credits - Debits for Liabilities, Income, and Equity
            account.balance = credits - debits
            
    return accounts

def update_account(db: Session, account_id: int, account_in: AccountUpdate, user_id: int) -> Account:
    user_ids = get_household_user_ids(db, user_id)
    db_account = db.query(Account).filter(Account.id == account_id, Account.user_id.in_(user_ids)).first()
    if not db_account:
        return None
    
    update_data = account_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_account, field, value)
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def delete_account(db: Session, account_id: int, user_id: int) -> bool:
    user_ids = get_household_user_ids(db, user_id)
    db_account = db.query(Account).filter(Account.id == account_id, Account.user_id.in_(user_ids)).first()
    if not db_account:
        return False
    
    # Check if there are entries associated with this account
    has_entries = db.query(Entry).filter(Entry.account_id == account_id).first() is not None
    if has_entries:
        raise ValueError("Cannot delete account with existing transactions.")
    
    db.delete(db_account)
    db.commit()
    return True
