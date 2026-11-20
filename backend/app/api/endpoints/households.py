from fastapi import APIRouter, HTTPException
from app.api.deps import CurrentUser, SessionDep
from app.models.household import HouseholdInvitation, Role
from app.schemas.household import HouseholdResponse, HouseholdMemberCreate
from app.services.household_service import (
    get_user_household,
    create_initial_household,
    invite_to_household,
    remove_member,
    get_household_members_details,
    get_membership,
    owner_count,
    get_invitations_for_email,
    accept_invitation,
)
from app.services.email_service import send_invite_email

router = APIRouter()


def _household_or_create(db, user):
    h = get_user_household(db, user.id)
    return h or create_initial_household(db, user.id)


def _require_owner(db, household_id: int, user) -> None:
    hm = get_membership(db, household_id, user.id)
    if not hm or hm.role != Role.owner:
        raise HTTPException(status_code=403, detail="Only the household owner can manage members.")


@router.get("/", response_model=HouseholdResponse)
def read_household(
    db: SessionDep,
    current_user: CurrentUser,
):
    h = _household_or_create(db, current_user)
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
    h = _household_or_create(db, current_user)
    _require_owner(db, h.id, current_user)
    if invite_in.email == current_user.email:
        raise HTTPException(status_code=400, detail="You are already in this household.")

    result = invite_to_household(db, h.id, invite_in.email, invite_in.role)
    if result == "role_updated":
        return {"status": "role_updated", "email": invite_in.email}

    await send_invite_email(invite_in.email, h.name, current_user.email)
    return {"status": "invite_sent", "email": invite_in.email}


@router.delete("/member/{user_id}")
def delete_member(
    user_id: int,
    db: SessionDep,
    current_user: CurrentUser,
):
    h = get_user_household(db, current_user.id)
    if not h:
        raise HTTPException(status_code=404, detail="No household found")

    target = get_membership(db, h.id, user_id)
    if not target:
        raise HTTPException(status_code=404, detail="That person is not in your household.")

    # Anyone may leave; only owners may remove other people.
    if user_id != current_user.id:
        _require_owner(db, h.id, current_user)

    if target.role == Role.owner and owner_count(db, h.id) <= 1:
        raise HTTPException(
            status_code=400,
            detail="A household needs at least one owner. Make someone else an owner first.",
        )

    remove_member(db, h.id, user_id)
    return {"status": "ok"}


@router.get("/invitations")
def list_my_invitations(db: SessionDep, current_user: CurrentUser):
    """Invitations other households have sent to the signed-in user."""
    return get_invitations_for_email(db, current_user.email)


def _get_invitation(db, invitation_id: int) -> HouseholdInvitation:
    inv = db.get(HouseholdInvitation, invitation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    return inv


@router.post("/invitations/{invitation_id}/accept")
def accept_household_invitation(invitation_id: int, db: SessionDep, current_user: CurrentUser):
    inv = _get_invitation(db, invitation_id)
    if inv.email != current_user.email:
        raise HTTPException(status_code=404, detail="Invitation not found.")
    accept_invitation(db, inv, current_user)
    return {"status": "ok"}


@router.delete("/invitations/{invitation_id}")
def decline_or_cancel_invitation(invitation_id: int, db: SessionDep, current_user: CurrentUser):
    """The invitee can decline; the household's owner can cancel."""
    inv = _get_invitation(db, invitation_id)
    if inv.email != current_user.email:
        hm = get_membership(db, inv.household_id, current_user.id)
        if not hm or hm.role != Role.owner:
            raise HTTPException(status_code=404, detail="Invitation not found.")
    db.delete(inv)
    db.commit()
    return {"status": "ok"}
