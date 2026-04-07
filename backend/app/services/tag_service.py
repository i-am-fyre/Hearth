from sqlalchemy.orm import Session
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate
from sqlalchemy.orm import joinedload

def get_tag(db: Session, tag_id: int, user_id: int) -> Tag | None:
    return db.query(Tag).filter(Tag.id == tag_id, Tag.user_id == user_id).first()

def get_tags(db: Session, user_id: int) -> list[Tag]:
    return db.query(Tag).filter(Tag.user_id == user_id).all()

def get_tags_by_ids(db: Session, tag_ids: list[int], user_id: int) -> list[Tag]:
    if not tag_ids:
        return []
    return db.query(Tag).filter(Tag.id.in_(tag_ids), Tag.user_id == user_id).all()

def create_tag(db: Session, obj_in: TagCreate, user_id: int) -> Tag:
    db_obj = Tag(
        name=obj_in.name,
        color_hex=obj_in.color_hex,
        user_id=user_id
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_tag(db: Session, db_obj: Tag, obj_in: TagUpdate) -> Tag:
    if obj_in.name is not None:
        db_obj.name = obj_in.name
    if obj_in.color_hex is not None:
        db_obj.color_hex = obj_in.color_hex
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_tag(db: Session, db_obj: Tag):
    db.delete(db_obj)
    db.commit()
