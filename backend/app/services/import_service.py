import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.bank_transaction import BankTransaction, MatchStatus
from app.models.transaction import Transaction, Entry
from app.models.user import User
from app.models.account import Account
from app.schemas.import_config import MappingConfig
from app.services import rule_engine

# A simple string similarity implementation since we cannot use heavy external ML libraries here safely.
def similarity(s1: str, s2: str) -> float:
    s1, s2 = s1.lower(), s2.lower()
    # Very basic jaccard-like similarity using character bigrams as a simple proxy
    def get_bigrams(s):
        return set(s[i:i+2] for i in range(len(s)-1)) if len(s) > 1 else set(s)
    
    set1 = get_bigrams(s1)
    set2 = get_bigrams(s2)
    
    if not set1 or not set2:
        return 0.0
        
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


    return intersection / union if union > 0 else 0.0

def get_csv_preview(file_content: bytes, limit: int = 5) -> List[List[str]]:
    text = file_content.decode('utf-8', errors='ignore')
    f = io.StringIO(text)
    reader = csv.reader(f)
    preview = []
    for i, row in enumerate(reader):
        if i >= limit:
            break
        preview.append(row)
    return preview

def parse_date(date_str: str) -> datetime.date:
    # Try various common formats
    formats = [
        "%Y-%m-%d", 
        "%m/%d/%Y", 
        "%d/%m/%Y", 
        "%b %d, %Y", # Mar 09, 2026
        "%Y/%m/%d"
    ]
    date_str = date_str.strip()
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Could not parse date: {date_str}")

def parse_amount(amount_str: str) -> Decimal:
    if not amount_str:
        return Decimal("0.00")
    # Remove symbols like $, commas
    clean = amount_str.replace('$', '').replace(',', '').strip()
    # Handle "(123.45)" style negatives
    if clean.startswith('(') and clean.endswith(')'):
        clean = '-' + clean[1:-1]
    return Decimal(clean)

def process_csv_import(db: Session, user: User, file_content: bytes, config: MappingConfig) -> List[BankTransaction]:
    """
    Parses a CSV file using provided MappingConfig.
    """
    text = file_content.decode('utf-8', errors='ignore')
    f = io.StringIO(text)
    reader = csv.reader(f)
    
    rows = list(reader)
    if not rows:
        return []
        
    data_rows = rows[1:] if config.has_header else rows
    imported_txns = []
    
    for row in data_rows:
        if not any(row): continue # Skip empty rows
        
        try:
            # Extract Date
            txn_date = parse_date(row[config.date_col])
            
            # Extract Description
            desc = row[config.desc_col].strip()
            
            # Extract Amount
            if config.amount_col is not None:
                amount = parse_amount(row[config.amount_col])
            elif config.debit_col is not None and config.credit_col is not None:
                debit = parse_amount(row[config.debit_col])
                credit = parse_amount(row[config.credit_col])
                # Logic: If it's a credit card, 'debit' column usually means spending (positive) 
                # and 'credit' means payment (negative toward balance).
                # Consistent with BankTransaction: positive = inflow?, no, 
                # actually transactions are signed. 
                # Usually: Spending is POSITIVE in bank transaction lists? 
                # Let's look at the samples. 
                # Credit Union: Withdrawal is "-$200.57".
                # CIBC: Spending is "32.47" in col 2, Payments are "2267.73" in col 3.
                # So if debit has value, it's negative. If credit has value, it's positive.
                if abs(debit) > 0:
                    amount = -abs(debit)
                else:
                    amount = abs(credit)
            else:
                amount = Decimal("0.00")
            
            bank_txn = BankTransaction(
                user_id=user.id,
                date=txn_date,
                description=desc,
                amount=amount
            )
            db.add(bank_txn)
            imported_txns.append(bank_txn)
        except Exception as e:
            print(f"Skipping row {row} due to error {e}")
            continue
            
    db.flush() # Get IDs for the newly inserted bank transactions
    
    # Now run the matching algorithm
    # Match if: 
    #   Absolute amount matches (Bank amount vs Transaction Entries amounts)
    #   Date within ±2 days
    #   String similarity > 0.7
    
    for bank_txn in imported_txns:
        # Optimization: Fetch candidate transactions matching criteria within the window
        start_date = bank_txn.date - timedelta(days=2)
        end_date = bank_txn.date + timedelta(days=2)
        
        candidates = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        ).all()
        
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            # Check absolute amount match
            # For a double entry transaction, the absolute value of debits (or credits) is the total transacted value
            candidate_amount = sum(e.debit for e in candidate.entries)
            
            if abs(candidate_amount) == abs(bank_txn.amount):
                sim_score = similarity(bank_txn.description, candidate.description)
                
                if sim_score > 0.7 and sim_score > best_score:
                    best_match = candidate
                    best_score = sim_score
                    
        if best_match:
            bank_txn.matched_transaction_id = best_match.id
            bank_txn.status = MatchStatus.matched
        else:
            # Let's flag it if we found the date and amount but string sim failed
            # or if it's completely unmatched
            amount_matches = any(abs(sum(e.debit for e in c.entries)) == abs(bank_txn.amount) for c in candidates)
            if amount_matches:
                bank_txn.status = MatchStatus.flagged
            else:
                bank_txn.status = MatchStatus.unmatched
            
            # RULE ENGINE SUGGESTION
            rule_result = rule_engine.apply_rules(db, user, {
                "merchant": bank_txn.description,
                "amount": abs(bank_txn.amount)
            })
            rule_actions = rule_result.get("actions", {})
            auto_post = rule_result.get("auto_post", False)

            if "assign_account_id" in rule_actions:
                acc_id = rule_actions["assign_account_id"]
                bank_txn.suggested_account_id = acc_id
                acc = db.query(Account).filter(Account.id == acc_id).first()
                if acc:
                    bank_txn.suggested_account_name = acc.name
                
                # Check for Auto-Post
                if auto_post and config.source_account_id:
                    try:
                        # Perform auto-reconciliation
                        # We use the existing function but need to be careful with session management
                        reconcile_transaction(
                            db, 
                            user, 
                            bank_txn.id, 
                            config.source_account_id, 
                            acc_id
                        )
                    except Exception as e:
                        print(f"Auto-post failed for {bank_txn.description}: {e}")
                
    db.commit()
    return imported_txns

def get_unmatched_transactions(db: Session, user_id: int) -> List[BankTransaction]:
    return db.query(BankTransaction).filter(
        BankTransaction.user_id == user_id,
        BankTransaction.status != MatchStatus.matched
    ).all()

def reconcile_transaction(
    db: Session, 
    user: User, 
    bank_txn_id: int, 
    source_acc_id: int, 
    target_acc_id: int
) -> Transaction:
    bank_txn = db.query(BankTransaction).filter(
        BankTransaction.id == bank_txn_id,
        BankTransaction.user_id == user.id
    ).first()
    
    if not bank_txn:
        raise ValueError("Bank transaction not found")
        
    # Create the regular Transaction
    new_txn = Transaction(
        user_id=user.id,
        date=bank_txn.date,
        description=bank_txn.description,
        receipt_id=None
    )
    db.add(new_txn)
    db.flush()
    
    # Create entries
    # bank_txn.amount is net. 
    # If negative (expense): source is credited (bank goes down), target is debited (expense goes up)
    # If positive (income): source is debited (bank goes up), target is credited (income goes up)
    
    abs_amount = abs(bank_txn.amount)
    if bank_txn.amount < 0:
        # Credit source, Debit target
        db.add(Entry(transaction_id=new_txn.id, account_id=source_acc_id, debit=0, credit=abs_amount))
        db.add(Entry(transaction_id=new_txn.id, account_id=target_acc_id, debit=abs_amount, credit=0))
    else:
        # Debit source, Credit target
        db.add(Entry(transaction_id=new_txn.id, account_id=source_acc_id, debit=abs_amount, credit=0))
        db.add(Entry(transaction_id=new_txn.id, account_id=target_acc_id, debit=0, credit=abs_amount))
        
    bank_txn.status = MatchStatus.matched
    bank_txn.matched_transaction_id = new_txn.id
    
    db.commit()
    db.refresh(new_txn)
    return new_txn
