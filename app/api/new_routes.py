from fastapi import APIRouter, HTTPException, Query
from models.models import (
    User,
    Item,
    Order,
    OrderLine
)
from schemas.schemas_order import (
    UserCreate, UserRead,
    ItemCreate, ItemRead, ItemUpdate,
    OrderCreate, OrderRead,
    OrderLineCreate, OrderLineRead
)

from core.database import SessionDep
from sqlmodel import select
from typing import Optional

router = APIRouter()


@router.post("/users/", response_model=UserRead)
def create_user(user_data: UserCreate, session: SessionDep) -> UserRead:
    user = User(**user_data.dict())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/users/", response_model=list[UserRead])
def list_users(
        session: SessionDep,
        name: Optional[str] = Query(None, description="Search user by name")
) -> list[UserRead]:
    query = select(User)
    if name:
        query = query.where(User.name.ilike(f"%{name}%"))
    users = session.exec(query).all()
    return users



@router.post("/items/", response_model=ItemRead)
def create_item(item_data: ItemCreate, session: SessionDep) -> ItemRead:
    item = Item(**item_data.dict())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/items/", response_model=list[ItemRead])
def list_items(
        session: SessionDep,
        name: Optional[str] = Query(None, description="Search items by name"),
) -> list[ItemRead]:
    query = select(Item)

    if name:
        query = query.where(Item.name.ilike(f"%{name}%"))
    items = session.exec(query).all()
    return items


@router.get("/items/{item_id}", response_model=ItemRead)
def get_item(item_id: int, session: SessionDep) -> ItemRead:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


# NO NEED ?
# @router.put("/items/{item_id}", response_model=ItemRead)
# def update_item(item_id: int, item_data: ItemCreate, session: SessionDep) -> ItemRead:
#     item = session.get(Item, item_id)
#     if item is None:
#         raise HTTPException(status_code=404, detail="Item not found")
#
#     for field, value in item_data.dict().items():
#         setattr(item, field, value)
#
#     session.add(item)
#     session.commit()
#     session.refresh(item)
#     return item


@router.patch("/items/{item_id}", response_model=ItemRead)
def partial_update_item(item_id: int, item_data: ItemUpdate, session: SessionDep) -> ItemRead:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/items/{item_id}")
def delete_item(item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    session.delete(item)
    session.commit()
    return {"message": "Item deleted successfully"}
