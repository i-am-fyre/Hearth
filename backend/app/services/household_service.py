from sqlalchemy.orm import Session
from app.models.household import Household, HouseholdMember, Role, HouseholdInvitation
from app.models.user import User
from typing import List

def get_user_household(db: Session, user_id: int):
    # Find all households the user is a part of
    memberships = db.query(HouseholdMember).filter(HouseholdMember.user_id == user_id).all()
    if not memberships:
        return None
        
    # If in multiple, prioritize the one that has other members
    for hm in memberships:
        count = db.query(HouseholdMember).filter(HouseholdMember.household_id == hm.household_id).count()
        if count > 1:
            return db.query(Household).filter(Household.id == hm.household_id).first()
            
    # Fallback to the first one
    return db.query(Household).filter(Household.id == memberships[0].household_id).first()

def create_initial_household(db: Session, user_id: int, name: str = "My Household"):
    h = Household(name=name)
    db.add(h)
    db.commit()
    db.refresh(h)
    
    hm = HouseholdMember(
        household_id=h.id,
        user_id=user_id,
        role=Role.owner
    )
    db.add(hm)
    db.commit()
    db.refresh(hm)
    return h

def get_membership(db: Session, household_id: int, user_id: int) -> HouseholdMember | None:
    return db.query(HouseholdMember).filter(
        HouseholdMember.household_id == household_id, HouseholdMember.user_id == user_id
    ).first()


def owner_count(db: Session, household_id: int) -> int:
    return db.query(HouseholdMember).filter(
        HouseholdMember.household_id == household_id, HouseholdMember.role == Role.owner
    ).count()


def invite_to_household(db: Session, household_id: int, email: str, role: Role) -> str:
    """Invite someone by email. Nobody joins a household without accepting.

    Household members see each other's accounts and transactions, so an existing
    user is never added directly. Returns "role_updated" if they are already a
    member (their role is changed), otherwise "invited".
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        hm = get_membership(db, household_id, user.id)
        if hm:
            hm.role = role
            db.commit()
            return "role_updated"
    create_invitation(db, household_id, email, role)
    return "invited"


def remove_member(db: Session, household_id: int, user_id: int):
    hm = db.query(HouseholdMember).filter(HouseholdMember.household_id == household_id, HouseholdMember.user_id == user_id).first()
    if hm:
        db.delete(hm)
        db.commit()

def get_household_members_details(db: Session, household_id: int):
    members = db.query(HouseholdMember, User.email).join(User, HouseholdMember.user_id == User.id).filter(HouseholdMember.household_id == household_id).all()
    out = []
    for m, email in members:
        out.append({
            "id": m.id,
            "user_id": m.user_id,
            "role": m.role,
            "household_id": m.household_id,
            "email": email,
            "status": "active"
        })
    
    # Also include pending invitations
    invs = db.query(HouseholdInvitation).filter(HouseholdInvitation.household_id == household_id).all()
    for inv in invs:
        out.append({
            "id": inv.id,
            "user_id": None,
            "role": inv.role,
            "household_id": inv.household_id,
            "email": inv.email,
            "status": "pending"
        })
    return out

def create_invitation(db: Session, household_id: int, email: str, role: Role):
    # Check if invitation already exists
    inv = db.query(HouseholdInvitation).filter(HouseholdInvitation.household_id == household_id, HouseholdInvitation.email == email).first()
    if inv:
        inv.role = role
    else:
        inv = HouseholdInvitation(household_id=household_id, email=email, role=role)
        db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv

def get_invitations_for_email(db: Session, email: str) -> list[dict]:
    """Pending invitations addressed to this email, with the household's name."""
    rows = (
        db.query(HouseholdInvitation, Household.name)
        .join(Household, Household.id == HouseholdInvitation.household_id)
        .filter(HouseholdInvitation.email == email)
        .all()
    )
    # Every household starts out named "My Household", so also say whose it is.
    # Only owners can invite, so an owner is who the invitation came from.
    def owner_email(household_id: int) -> str | None:
        row = (
            db.query(User.email)
            .join(HouseholdMember, HouseholdMember.user_id == User.id)
            .filter(HouseholdMember.household_id == household_id, HouseholdMember.role == Role.owner)
            .order_by(HouseholdMember.id)
            .first()
        )
        return row[0] if row else None

    return [
        {
            "id": inv.id,
            "household_id": inv.household_id,
            "household_name": name,
            "owner_email": owner_email(inv.household_id),
            "role": inv.role,
        }
        for inv, name in rows
    ]


def accept_invitation(db: Session, inv: HouseholdInvitation, user: User) -> None:
    if not get_membership(db, inv.household_id, user.id):
        db.add(HouseholdMember(household_id=inv.household_id, user_id=user.id, role=inv.role))
    db.delete(inv)
    db.commit()


def get_household_user_ids(db: Session, user_id: int) -> list[int]:
    # Find all households the user is part of
    hms = db.query(HouseholdMember).filter(HouseholdMember.user_id == user_id).all()
    if not hms:
        return [user_id]
        
    household_ids = [hm.household_id for hm in hms]
    
    # Find all members of all those households
    all_members = db.query(HouseholdMember).filter(HouseholdMember.household_id.in_(household_ids)).all()
    
    # Return unique set of user IDs
    user_ids = {m.user_id for m in all_members}
    return list(user_ids)
