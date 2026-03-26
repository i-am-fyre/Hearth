from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

from app.services.crypto_service import generate_encryption_key

def get_user(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    encryption_key = generate_encryption_key()
    db_user = User(
        email=user_in.email, 
        password_hash=hashed_password,
        encryption_key=encryption_key
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
