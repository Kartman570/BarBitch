from fastapi import APIRouter, HTTPException, Query
from app.models.item import Item, ItemIn, ItemOut
from app.core.database import SessionDep
from sqlmodel import select
from typing import Optional

router = APIRouter()


@router.post("/items/", response_model=ItemOut)
def create_item(item_data: ItemIn, session: SessionDep) -> ItemOut:
    item = Item(**item_data.dict())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/items/", response_model=list[ItemOut])
def list_items(
    session: SessionDep,
    name: Optional[str] = Query(None, description="Search items by name"),
    min_price: Optional[float] = Query(None, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, description="Maximum price filter"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
) -> list[ItemOut]:
    query = select(Item)
    
    if name:
        query = query.where(Item.name.ilike(f"%{name}%"))
    
    if min_price is not None:
        query = query.where(Item.price >= min_price)
    
    if max_price is not None:
        query = query.where(Item.price <= max_price)
    
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    items = session.exec(query).all()
    return items

# @router.get("/items/count")
# def count_items(session: SessionDep):
#     query = select(Item)
#     items = session.exec(query).all()
#     return {"count": len(items)}

@router.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, session: SessionDep) -> ItemOut:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, item_data: ItemIn, session: SessionDep) -> ItemOut:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for field, value in item_data.dict().items():
        setattr(item, field, value)
    
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=ItemOut)
def partial_update_item(item_id: int, item_data: ItemIn, session: SessionDep) -> ItemOut:
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
