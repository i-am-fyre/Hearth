"""Who may read or change which users' data.

Household members can see each other's accounts, transactions and budgets. Changing
another member's data needs a write role in a household you share with them:

- Your own data is always yours to change.
- Owners and members can change data belonging to anyone in their household.
- Read-only members can view the household's data but change only their own.

Data outside your households is reported as "not found" (404), so its existence
isn't revealed; data you can see but not change is refused with 403.
"""
from collections.abc import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.household import HouseholdMember, Role
from app.services.household_service import get_household_user_ids

READ_ONLY_DETAIL = "You have read-only access to this household's data."
ACCOUNTS_NOT_FOUND_DETAIL = "One or more accounts not found or do not belong to you or your household."
WRITE_ROLES = (Role.owner, Role.member)


def readable_user_ids(db: Session, user_id: int) -> set[int]:
    """Users whose data `user_id` can see: themselves plus their households' members."""
    return set(get_household_user_ids(db, user_id))


def writable_user_ids(db: Session, user_id: int) -> set[int]:
    """Users whose data `user_id` can change: themselves plus members of households
    where they are an owner or member (not read-only)."""
    household_ids = [
        hm.household_id
        for hm in db.query(HouseholdMember).filter(
            HouseholdMember.user_id == user_id, HouseholdMember.role.in_(WRITE_ROLES)
        )
    ]
    ids = {user_id}
    if household_ids:
        ids.update(
            uid
            for (uid,) in db.query(HouseholdMember.user_id).filter(
                HouseholdMember.household_id.in_(household_ids)
            )
        )
    return ids


def ensure_can_write(db: Session, user_id: int, owner_id: int) -> None:
    """Raise 403 unless `user_id` may change data owned by `owner_id`.

    Call this only after confirming the data is readable (otherwise return 404).
    """
    if owner_id not in writable_user_ids(db, user_id):
        raise HTTPException(status_code=403, detail=READ_ONLY_DETAIL)


def readable_accounts(
    db: Session, user_id: int, account_ids: Iterable[int], not_found_status: int = 400
) -> list[Account]:
    """Load the given accounts, raising if any isn't visible to `user_id`."""
    ids = set(account_ids)
    if not ids:
        return []
    accounts = (
        db.query(Account)
        .filter(Account.id.in_(ids), Account.user_id.in_(readable_user_ids(db, user_id)))
        .all()
    )
    if len(accounts) != len(ids):
        raise HTTPException(status_code=not_found_status, detail=ACCOUNTS_NOT_FOUND_DETAIL)
    return accounts


def writable_accounts(
    db: Session, user_id: int, account_ids: Iterable[int], not_found_status: int = 400
) -> list[Account]:
    """Load the given accounts, raising unless `user_id` may post to all of them."""
    accounts = readable_accounts(db, user_id, account_ids, not_found_status)
    writable = writable_user_ids(db, user_id)
    if any(a.user_id not in writable for a in accounts):
        raise HTTPException(status_code=403, detail=READ_ONLY_DETAIL)
    return accounts


def mark_editable(items: Iterable, writable: set[int]):
    """Set `can_edit` on each item (anything with a `user_id`) for the API response."""
    items = list(items)
    for item in items:
        item.can_edit = item.user_id in writable
    return items
