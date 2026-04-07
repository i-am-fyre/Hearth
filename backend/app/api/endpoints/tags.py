from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import SessionDep, CurrentUser
from app.schemas.tag import TagCreate, TagUpdate, TagResponse
from app.services import tag_service

router = APIRouter()

@router.get("/", response_model=list[TagResponse])
def read_tags(db: SessionDep, current_user: CurrentUser) -> Any:
    return tag_service.get_tags(db, user_id=current_user.id)

@router.post("/", response_model=TagResponse)
def create_tag(db: SessionDep, current_user: CurrentUser, tag_in: TagCreate) -> Any:
    return tag_service.create_tag(db, obj_in=tag_in, user_id=current_user.id)

@router.put("/{tag_id}", response_model=TagResponse)
def update_tag(db: SessionDep, current_user: CurrentUser, tag_id: int, tag_in: TagUpdate) -> Any:
    tag = tag_service.get_tag(db, tag_id=tag_id, user_id=current_user.id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag_service.update_tag(db, db_obj=tag, obj_in=tag_in)

@router.delete("/{tag_id}")
def delete_tag(db: SessionDep, current_user: CurrentUser, tag_id: int) -> dict:
    tag = tag_service.get_tag(db, tag_id=tag_id, user_id=current_user.id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    tag_service.delete_tag(db, db_obj=tag)
    return {"ok": True}
