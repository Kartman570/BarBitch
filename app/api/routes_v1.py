from datetime import datetime, date as date_type
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlmodel import select

from models.models import User, Item, Order, Table, Role
from schemas.schemas_order import (
    RoleCreate, RoleRead, RoleUpdate,
    UserCreate, UserRead, UserUpdate,
    LoginRequest, LoginResponse,
    ItemCreate, ItemRead, ItemUpdate, StockAdjust,
    OrderCreate, OrderRead, OrderUpdate,
    TableCreate, TableRead, TableUpdate, TableReadDetailed,
    DailyStats,
)
from core.database import SessionDep
from core.config import settings
from services.table_service import TableService
from services.auth_service import (
    hash_password, verify_password,
    encode_permissions, decode_permissions,
    create_access_token, decode_access_token,
    ALL_PERMISSIONS,
)

router = APIRouter()
_bearer = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
    session: SessionDep,
) -> User:
    try:
        user_id = decode_access_token(credentials.credentials, settings.secret_key)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# ── Auth ───────────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=LoginResponse, tags=["auth"])
def login(data: LoginRequest, session: SessionDep):
    user = session.exec(select(User).where(User.username == data.username)).first()
    if user is None or user.password_hash is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role = session.get(Role, user.role_id) if user.role_id else None
    permissions = decode_permissions(role.permissions) if role else []
    return LoginResponse(
        access_token=create_access_token(user.id, settings.secret_key),
        id=user.id,
        name=user.name,
        username=user.username,
        role_name=role.name if role else "",
        permissions=permissions,
    )


# ── Roles ──────────────────────────────────────────────────────────────────────

def _role_to_read(role: Role) -> RoleRead:
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=decode_permissions(role.permissions),
    )


@router.post("/roles/", response_model=RoleRead, tags=["roles"])
def create_role(data: RoleCreate, session: SessionDep, _: CurrentUserDep):
    invalid = set(data.permissions) - ALL_PERMISSIONS
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown permissions: {sorted(invalid)}")
    existing = session.exec(select(Role).where(Role.name == data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Role '{data.name}' already exists")
    role = Role(
        name=data.name,
        description=data.description,
        permissions=encode_permissions(data.permissions),
    )
    session.add(role)
    session.commit()
    session.refresh(role)
    return _role_to_read(role)


@router.get("/roles/", response_model=list[RoleRead], tags=["roles"])
def list_roles(session: SessionDep, _: CurrentUserDep):
    roles = session.exec(select(Role)).all()
    return [_role_to_read(r) for r in roles]


@router.get("/roles/{role_id}", response_model=RoleRead, tags=["roles"])
def get_role(role_id: int, session: SessionDep, _: CurrentUserDep):
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return _role_to_read(role)


@router.patch("/roles/{role_id}", response_model=RoleRead, tags=["roles"])
def update_role(role_id: int, data: RoleUpdate, session: SessionDep, _: CurrentUserDep):
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    if data.name is not None:
        role.name = data.name
    if data.description is not None:
        role.description = data.description
    if data.permissions is not None:
        invalid = set(data.permissions) - ALL_PERMISSIONS
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unknown permissions: {sorted(invalid)}")
        role.permissions = encode_permissions(data.permissions)
    session.add(role)
    session.commit()
    session.refresh(role)
    return _role_to_read(role)


@router.delete("/roles/{role_id}", tags=["roles"])
def delete_role(role_id: int, session: SessionDep, _: CurrentUserDep):
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.name == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete the built-in admin role")
    assigned = session.exec(select(User).where(User.role_id == role_id)).first()
    if assigned:
        raise HTTPException(status_code=400, detail="Cannot delete role with assigned users")
    session.delete(role)
    session.commit()
    return {"message": "Role deleted"}


# ── Users ──────────────────────────────────────────────────────────────────────

def _user_to_read(user: User, session) -> UserRead:
    role = session.get(Role, user.role_id) if user.role_id else None
    return UserRead(
        id=user.id,
        name=user.name,
        username=user.username,
        role_id=user.role_id,
        role_name=role.name if role else None,
        permissions=decode_permissions(role.permissions) if role else [],
    )


@router.post("/users/", response_model=UserRead, tags=["users"])
def create_user(data: UserCreate, session: SessionDep, _: CurrentUserDep):
    if session.exec(select(User).where(User.username == data.username)).first():
        raise HTTPException(status_code=400, detail=f"Username '{data.username}' already taken")
    if session.get(Role, data.role_id) is None:
        raise HTTPException(status_code=404, detail="Role not found")
    user = User(
        name=data.name,
        username=data.username,
        password_hash=hash_password(data.password),
        role_id=data.role_id,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_to_read(user, session)


@router.get("/users/", response_model=list[UserRead], tags=["users"])
def list_users(
    session: SessionDep,
    _: CurrentUserDep,
    name: Optional[str] = Query(None, description="Filter by name"),
):
    q = select(User)
    if name:
        q = q.where(User.name.ilike(f"%{name}%"))
    users = session.exec(q).all()
    return [_user_to_read(u, session) for u in users]


@router.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: int, session: SessionDep, _: CurrentUserDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_read(user, session)


@router.put("/users/{user_id}", response_model=UserRead, tags=["users"])
def update_user(user_id: int, data: UserUpdate, session: SessionDep, _: CurrentUserDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if data.name is not None:
        user.name = data.name
    if data.username is not None:
        existing = session.exec(select(User).where(User.username == data.username)).first()
        if existing and existing.id != user_id:
            raise HTTPException(status_code=400, detail=f"Username '{data.username}' already taken")
        user.username = data.username
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.role_id is not None:
        if session.get(Role, data.role_id) is None:
            raise HTTPException(status_code=404, detail="Role not found")
        user.role_id = data.role_id
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_to_read(user, session)


@router.delete("/users/{user_id}", tags=["users"])
def delete_user(user_id: int, session: SessionDep, _: CurrentUserDep):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"message": "User deleted"}


# ── Items ──────────────────────────────────────────────────────────────────────

@router.post("/items/", response_model=ItemRead, tags=["items"])
def create_item(data: ItemCreate, session: SessionDep, _: CurrentUserDep):
    item = Item(**data.model_dump())
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/items/", response_model=list[ItemRead], tags=["items"])
def list_items(
    session: SessionDep,
    _: CurrentUserDep,
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
def get_item(item_id: int, session: SessionDep, _: CurrentUserDep):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{item_id}", response_model=ItemRead, tags=["items"])
def update_item(item_id: int, data: ItemUpdate, session: SessionDep, _: CurrentUserDep):
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
def delete_item(item_id: int, session: SessionDep, _: CurrentUserDep):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return {"message": "Item deleted"}


@router.patch("/items/{item_id}/stock", response_model=ItemRead, tags=["items"])
def adjust_stock(item_id: int, data: StockAdjust, session: SessionDep, _: CurrentUserDep):
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
def create_table(data: TableCreate, session: SessionDep, _: CurrentUserDep):
    table = TableService(session).create_table(data)
    return table


@router.get("/tables/", response_model=list[TableRead], tags=["tables"])
def list_tables(
    session: SessionDep,
    _: CurrentUserDep,
    status: Optional[str] = Query(None, description="Filter by status: Active | Closed"),
    date: Optional[str] = Query(None, description="Filter closed tables by date YYYY-MM-DD"),
):
    from datetime import timedelta as _td
    q = select(Table)
    if status:
        q = q.where(Table.status == status)
    if date and status == "Closed":
        try:
            day = date_type.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
        day_start = datetime.combine(day, datetime.min.time())
        day_end = day_start + _td(days=1)
        q = q.where(Table.closed_at >= day_start).where(Table.closed_at < day_end)
    q = q.order_by(Table.created_at.desc())
    return session.exec(q).all()


@router.get("/tables/{table_id}", response_model=TableReadDetailed, tags=["tables"])
def get_table(table_id: int, session: SessionDep, _: CurrentUserDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return table


@router.patch("/tables/{table_id}", response_model=TableRead, tags=["tables"])
def update_table(table_id: int, data: TableUpdate, session: SessionDep, _: CurrentUserDep):
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
def close_table(table_id: int, session: SessionDep, _: CurrentUserDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        table = TableService(session).close_table(table)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return table


@router.delete("/tables/{table_id}", tags=["tables"])
def delete_table(table_id: int, session: SessionDep, _: CurrentUserDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    session.delete(table)
    session.commit()
    return {"message": "Table deleted"}


# ── Orders (nested under tables) ───────────────────────────────────────────────

@router.post("/tables/{table_id}/orders/", response_model=OrderRead, tags=["orders"])
def add_order(table_id: int, data: OrderCreate, session: SessionDep, _: CurrentUserDep):
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
def list_orders(table_id: int, session: SessionDep, _: CurrentUserDep):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    orders = session.exec(select(Order).where(Order.table_id == table_id)).all()
    return orders


@router.get("/tables/{table_id}/orders/{order_id}", response_model=OrderRead, tags=["orders"])
def get_order(table_id: int, order_id: int, session: SessionDep, _: CurrentUserDep):
    order = session.get(Order, order_id)
    if order is None or order.table_id != table_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/tables/{table_id}/orders/{order_id}", response_model=OrderRead, tags=["orders"])
def update_order(table_id: int, order_id: int, data: OrderUpdate, session: SessionDep, _: CurrentUserDep):
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
def delete_order(table_id: int, order_id: int, session: SessionDep, _: CurrentUserDep):
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
    _: CurrentUserDep,
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
