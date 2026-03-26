from sqlalchemy.orm import Session
from app.models.household import Household, HouseholdMember, Role, HouseholdInvitation
from app.models.user import User
from app.schemas.household import HouseholdCreate, HouseholdMemberCreate
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

def invite_member(db: Session, household_id: int, invite_in: HouseholdMemberCreate):
    # Find user by email
    user = db.query(User).filter(User.email == invite_in.email).first()
    if not user:
        raise Exception("User not found")
        
    hm = db.query(HouseholdMember).filter(HouseholdMember.household_id == household_id, HouseholdMember.user_id == user.id).first()
    if hm:
        # Already member, update role
        hm.role = invite_in.role
        db.commit()
        db.refresh(hm)
        return hm

    hm = HouseholdMember(
        household_id=household_id,
        user_id=user.id,
        role=invite_in.role
    )
    db.add(hm)
    db.commit()
    db.refresh(hm)
    return hm

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

def process_pending_invitations(db: Session, user: User):
    invs = db.query(HouseholdInvitation).filter(HouseholdInvitation.email == user.email).all()
    for inv in invs:
        # Check if already member
        hm = db.query(HouseholdMember).filter(HouseholdMember.household_id == inv.household_id, HouseholdMember.user_id == user.id).first()
        if not hm:
            hm = HouseholdMember(household_id=inv.household_id, user_id=user.id, role=inv.role)
            db.add(hm)
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
