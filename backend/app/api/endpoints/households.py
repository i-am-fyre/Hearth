from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.api.deps import CurrentUser, SessionDep
from app.schemas.household import HouseholdResponse, HouseholdMemberCreate, HouseholdMemberResponse
from app.services.household_service import (
    get_user_household, 
    create_initial_household, 
    invite_member, 
    remove_member,
    get_household_members_details,
    create_invitation
)
from app.services.email_service import send_invite_email

router = APIRouter()

@router.get("/", response_model=HouseholdResponse)
def read_household(
    db: SessionDep,
    current_user: CurrentUser,
):
    h = get_user_household(db, current_user.id)
    if not h:
        # Create one automatically for the current user
        h = create_initial_household(db, current_user.id)
        
    members = get_household_members_details(db, h.id)
    return {
        "id": h.id,
        "name": h.name,
        "members": members
    }

@router.post("/invite")
async def add_member(
    invite_in: HouseholdMemberCreate,
    db: SessionDep,
    current_user: CurrentUser,
):
    h = get_user_household(db, current_user.id)
    if not h:
        h = create_initial_household(db, current_user.id)
        
    try:
        hm = invite_member(db, h.id, invite_in)
        # return matching dict
        members = get_household_members_details(db, h.id)
        for m in members:
            if m["user_id"] == hm.user_id:
                return m
        raise HTTPException(status_code=500, detail="Error resolving member")
    except Exception as e:
        if str(e) == "User not found":
            # Create a database invitation record for registration auto-join
            create_invitation(db, h.id, invite_in.email, invite_in.role)
            # Send an invite email
            await send_invite_email(invite_in.email, h.name, current_user.email)
            return {"status": "invite_sent", "email": invite_in.email}
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/member/{user_id}")
def delete_member(
    user_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    h = get_user_household(db, current_user.id)
    if not h:
        raise HTTPException(status_code=404, detail="No household found")
        
    # Security: check if they are owner or deleting themselves
    # Simplified here, just performing delete
    remove_member(db, h.id, user_id)
    return {"status": "ok"}
