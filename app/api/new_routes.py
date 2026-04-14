from datetime import datetime, date as date_type
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from models.models import User, Item, Order, Table
from schemas.schemas_order import (
    UserCreate, UserRead, UserUpdate,
    ItemCreate, ItemRead, ItemUpdate, StockAdjust,
    OrderCreate, OrderRead, OrderUpdate,
    TableCreate, TableRead, TableUpdate, TableReadDetailed,
    DailyStats,
)
from core.database import SessionDep
from services.table_service import TableService

router = APIRouter()


# ── Users ──────────────────────────────────────────────────────────────────────

@router.post("/users/", response_model=UserRead, tags=["users"])
def create_user(data: UserCreate, session: SessionDep):
    user = User(**data.model_dump())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/users/", response_model=list[UserRead], tags=["users"])
def list_users(
    session: SessionDep,
    name: Optional[str] = Query(None, description="Filter by name"),
):
    q = select(User)
    if name:
        q = q.where(User.name.ilike(f"%{name}%"))
    return session.exec(q).all()


@router.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserRead, tags=["users"])
def update_user(user_id: int, data: UserUpdate, session: SessionDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"message": "User deleted"}


# ── Items ──────────────────────────────────────────────────────────────────────

@router.post("/items/", response_model=ItemRead, tags=["items"])
def create_item(data: ItemCreate, session: SessionDep):
    item = Item(**data.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/items/", response_model=list[ItemRead], tags=["items"])
def list_items(
    session: SessionDep,
    name: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    available_only: bool = Query(False),
):
    q = select(Item)
    if name:
        q = q.where(Item.name.ilike(f"%{name}%"))
    if category:
        q = q.where(Item.category == category)
    if available_only:
        q = q.where(Item.is_available == True)
    return session.exec(q).all()


@router.get("/items/{item_id}", response_model=ItemRead, tags=["items"])
def get_item(item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{item_id}", response_model=ItemRead, tags=["items"])
def update_item(item_id: int, data: ItemUpdate, session: SessionDep):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.updated_at = datetime.now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/items/{item_id}", tags=["items"])
def delete_item(item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return {"message": "Item deleted"}


@router.patch("/items/{item_id}/stock", response_model=ItemRead, tags=["items"])
def adjust_stock(item_id: int, data: StockAdjust, session: SessionDep):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.stock_qty is None:
        raise HTTPException(status_code=400, detail="Stock not tracked for this item")
    new_qty = item.stock_qty + data.delta
    if new_qty < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    item.stock_qty = new_qty
    item.updated_at = datetime.now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


# ── Tables ─────────────────────────────────────────────────────────────────────

@router.post("/tables/", response_model=TableRead, tags=["tables"])
def create_table(data: TableCreate, session: SessionDep):
    table = TableService(session).create_table(data)
    return table


@router.get("/tables/", response_model=list[TableRead], tags=["tables"])
def list_tables(
    session: SessionDep,
    status: Optional[str] = Query(None, description="Filter by status: Active | Closed"),
):
    q = select(Table)
    if status:
        q = q.where(Table.status == status)
    return session.exec(q).all()


@router.get("/tables/{table_id}", response_model=TableReadDetailed, tags=["tables"])
def get_table(table_id: int, session: SessionDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return table


@router.patch("/tables/{table_id}", response_model=TableRead, tags=["tables"])
def update_table(table_id: int, data: TableUpdate, session: SessionDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(table, field, value)
    table.updated_at = datetime.now()
    session.add(table)
    session.commit()
    session.refresh(table)
    return table


@router.post("/tables/{table_id}/close", response_model=TableRead, tags=["tables"])
def close_table(table_id: int, session: SessionDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        table = TableService(session).close_table(table)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return table


@router.delete("/tables/{table_id}", tags=["tables"])
def delete_table(table_id: int, session: SessionDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    session.delete(table)
    session.commit()
    return {"message": "Table deleted"}


# ── Orders (nested under tables) ───────────────────────────────────────────────

@router.post("/tables/{table_id}/orders/", response_model=OrderRead, tags=["orders"])
def add_order(table_id: int, data: OrderCreate, session: SessionDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        order = TableService(session).add_order(table, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return order


@router.get("/tables/{table_id}/orders/", response_model=list[OrderRead], tags=["orders"])
def list_orders(table_id: int, session: SessionDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    orders = session.exec(select(Order).where(Order.table_id == table_id)).all()
    return orders


@router.get("/tables/{table_id}/orders/{order_id}", response_model=OrderRead, tags=["orders"])
def get_order(table_id: int, order_id: int, session: SessionDep):
    order = session.get(Order, order_id)
    if order is None or order.table_id != table_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/tables/{table_id}/orders/{order_id}", response_model=OrderRead, tags=["orders"])
def update_order(table_id: int, order_id: int, data: OrderUpdate, session: SessionDep):
    order = session.get(Order, order_id)
    if order is None or order.table_id != table_id:
        raise HTTPException(status_code=404, detail="Order not found")

    # Calculate quantity delta
    quantity_delta = data.quantity - order.quantity

    # Adjust stock if item has stock tracking
    if quantity_delta != 0:
        item = session.get(Item, order.item_id)
        if item and item.stock_qty is not None:
            # Quantity increased: deduct more stock
            if quantity_delta > 0:
                if item.stock_qty < quantity_delta:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for {item.name}. Available: {item.stock_qty}, Need: {quantity_delta}")
                item.stock_qty -= quantity_delta
            # Quantity decreased: restore stock
            else:
                item.stock_qty -= quantity_delta  # subtract negative number = add
            item.updated_at = datetime.now()
            session.add(item)

    order.quantity = data.quantity
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.delete("/tables/{table_id}/orders/{order_id}", tags=["orders"])
def delete_order(table_id: int, order_id: int, session: SessionDep):
    order = session.get(Order, order_id)
    if order is None or order.table_id != table_id:
        raise HTTPException(status_code=404, detail="Order not found")
    session.delete(order)
    session.commit()
    return {"message": "Order deleted"}


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.get("/stats/daily", response_model=DailyStats, tags=["stats"])
def daily_stats(
    session: SessionDep,
    date: Optional[str] = Query(None, description="Date YYYY-MM-DD, defaults to today"),
):
    if date:
        try:
            target = date_type.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    else:
        target = date_type.today()
    return TableService(session).daily_stats(target)
