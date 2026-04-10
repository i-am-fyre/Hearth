from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.schemas.user import UserCreate, UserResponse, Token, UserForgotPassword, UserResetPassword
from app.services import user_service
from app.services.household_service import process_pending_invitations
from app.api.deps import CurrentUser
from app.services.email_service import send_password_reset_email
from datetime import datetime, timezone
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate, db: SessionDep) -> Any:
    try:
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
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Registration Error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error during registration")

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

@router.post("/forgot-password")
async def forgot_password(user_in: UserForgotPassword, db: SessionDep) -> Any:
    user = user_service.get_user_by_email(db, email=user_in.email)
    
    # Always return success to prevent timing/enumeration attacks
    if not user:
        return {"message": "If that email address exists in our system, we've sent a password reset link."}
        
    # Generate token
    token = secrets.token_urlsafe(32)
    user.reset_token = security.get_password_hash(token) # Reuse hash function for secure storage
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()
    
    # Send email
    await send_password_reset_email(email_to=user.email, token=token)
    
    # Fallback log for local development without SMTP
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"--- FALLBACK PASSWORD RESET LINK ---")
        logger.warning(f"{settings.FRONTEND_URL}/login/reset?token={token}")
        logger.warning(f"------------------------------------")
        
    return {"message": "If that email address exists in our system, we've sent a password reset link."}

@router.post("/reset-password")
def reset_password(user_in: UserResetPassword, db: SessionDep) -> Any:
    
    # Find any user whose reset token matches and isn't expired
    # To do this safely, we must iterate over active resets (or hash it first if we weren't dynamically salting)
    # Wait, bcrypt (get_password_hash) generates a unique salt every time, so we CANNOT query by hash!
    # Let's fetch all users with an active token and test them. It's safe given password resets are rare.
    users_with_token = db.query(user_service.User).filter(
        user_service.User.reset_token != None,
        user_service.User.reset_token_expires > datetime.now(timezone.utc)
    ).all()
    
    target_user = None
    for u in users_with_token:
        if security.verify_password(user_in.token, u.reset_token):
            target_user = u
            break
            
    if not target_user:
        raise HTTPException(status_code=400, detail="Invalid or expired password reset token.")
        
    # Valid token found! Reset password.
    target_user.password_hash = security.get_password_hash(user_in.new_password)
    target_user.reset_token = None
    target_user.reset_token_expires = None
    db.commit()
    
    return {"message": "Password has been successfully reset."}
