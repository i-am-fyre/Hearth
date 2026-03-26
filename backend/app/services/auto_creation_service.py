from sqlalchemy.orm import Session
from datetime import datetime, date
from decimal import Decimal
from fastapi import HTTPException
from app.models.receipt import Receipt
from app.models.user import User
from app.models.account import Account, AccountType
from app.schemas.transaction import TransactionCreate, EntryCreate
from app.services.transaction_service import create_transaction
import json

def auto_create_transaction_from_receipt(db: Session, receipt: Receipt, user: User) -> Receipt | None:
    if not receipt.parsed_json or receipt.confidence_score is None:
        return None

    try:
        parsed_data = json.loads(receipt.parsed_json)
    except json.JSONDecodeError:
        return None

    # Get Default Accounts
    # We will try to find a generic Expense account and a generic Asset account for defaults
    expense_account = db.query(Account).filter(Account.user_id == user.id, Account.type == AccountType.expense).first()
    asset_account = db.query(Account).filter(Account.user_id == user.id, Account.type == AccountType.asset).first()

    # Phase 6: Rule Engine Integration
    from app.services.rule_engine import apply_rules
    rule_data = {
        "merchant": parsed_data.get("merchant", ""),
        "amount": parsed_data.get("total", "0.00")
    }
    rule_actions = apply_rules(db, user, rule_data)
    
    # If a rule defines a specific account, override the default expense account
    assigned_account_id = rule_actions.get("assign_account_id")
    if assigned_account_id:
        rule_account = db.query(Account).filter(Account.id == assigned_account_id, Account.user_id == user.id).first()
        if rule_account:
            expense_account = rule_account

    if not expense_account or not asset_account:
        # Cannot auto-create without valid accounts to balance
        return None

    # Try mapping date safely
    txn_date = date.today()
    if parsed_data.get("date"):
        try:
            # Simplistic mm/dd/yyyy parser attempt for the demo
            # In a real app, `dateutil.parser` is much better here
            parts = parsed_data["date"].replace("-", "/").replace(".", "/").split("/")
            if len(parts) >= 3:
                # Assuming mm/dd/yy or mm/dd/yyyy
                year = int(parts[2])
                if year < 100:
                    year += 2000
                txn_date = date(year, int(parts[0]), int(parts[1]))
        except Exception:
            pass
            
    total_amount = Decimal(parsed_data.get("total", "0.00"))
    if total_amount == Decimal('0.00'):
        # Don't auto-create zero-dollar transactions
        return None

    is_draft = receipt.confidence_score < 0.6
    description_prefix = "[DRAFT REVIEW] " if is_draft else "[AUTO] "
    description = f"{description_prefix}Receipt: {parsed_data.get('merchant', 'Unknown')}"

    # Build the double entry
    entries = []
    
    # 1. Debit Expense
    entries.append(
        EntryCreate(
            account_id=expense_account.id,
            debit=total_amount,
            credit=Decimal('0.00')
        )
    )
    
    # 2. Credit Asset (assuming we paid from our primary asset)
    entries.append(
        EntryCreate(
            account_id=asset_account.id,
            debit=Decimal('0.00'),
            credit=total_amount
        )
    )

    transaction_in = TransactionCreate(
        date=txn_date,
        description=description,
        receipt_id=receipt.id,
        entries=entries
    )

    # 3. Create the actual transaction
    transaction = create_transaction(db=db, transaction_in=transaction_in, user_id=user.id)
    
    # 4. Attach receipt to transaction
    receipt.transaction_id = transaction.id
    db.commit()
    db.refresh(receipt)
    
    return receipt
