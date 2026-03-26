from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.schemas.user import UserCreate, UserResponse, Token
from app.services import user_service
from app.services.household_service import process_pending_invitations
from app.api.deps import CurrentUser

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: SessionDep) -> Any:
    user = user_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = user_service.create_user(db, user_in)
    # Process any pending household invitations for this user's email
    process_pending_invitations(db, user)
    return user

@router.post("/login", response_model=Token)
def login_access_token(
    db: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = user_service.get_user_by_email(db, email=form_data.username) # Form username is email
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.email, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> Any:
    return current_user
