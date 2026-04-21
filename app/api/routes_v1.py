from datetime import datetime, date as date_type, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError as JWTError
from sqlmodel import select

from models.models import User, Item, Order, Table, Role, RefreshToken, AuditEvent, DiscountPolicy
from schemas.schemas_order import (
    RoleCreate, RoleRead, RoleUpdate,
    UserCreate, UserRead, UserUpdate,
    LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    ItemCreate, ItemRead, ItemUpdate, StockAdjust,
    OrderCreate, OrderRead, OrderUpdate,
    TableCreate, TableRead, TableUpdate, TableReadDetailed,
    DailyStats, AuditEventRead, TopItemStat,
    DiscountPolicyCreate, DiscountPolicyUpdate, DiscountPolicyRead, ActiveDiscountRead,
)
import json as _json
from core.database import SessionDep
from core.config import settings
from core.limiter import limiter
from services.table_service import TableService
from services.auth_service import (
    hash_password, verify_password,
    encode_permissions, decode_permissions,
    create_access_token, decode_access_token,
    create_refresh_token_string, REFRESH_TOKEN_EXPIRE_DAYS,
    ALL_PERMISSIONS,
)

router = APIRouter()
_bearer = HTTPBearer()


def _get_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def _audit(session, action: str, user: User | None = None, resource_id: int | None = None, ip: str | None = None):
    session.add(AuditEvent(
        user_id=user.id if user else None,
        username=user.username if user else None,
        action=action,
        resource_id=resource_id,
        ip=ip,
    ))


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


def _perm(perm: str):
    """Returns a Depends that enforces a named permission from the user's role."""
    def checker(user: CurrentUserDep, session: SessionDep) -> User:
        role = session.get(Role, user.role_id) if user.role_id else None
        if role is None:
            raise HTTPException(status_code=403, detail="No role assigned to this account")
        if perm not in decode_permissions(role.permissions):
            raise HTTPException(status_code=403, detail=f"Permission '{perm}' required")
        return user
    return Depends(checker)


# ── Auth ───────────────────────────────────────────────────────────────────────

@router.post("/auth/login", response_model=LoginResponse, tags=["auth"])
@limiter.limit("10/minute")
def login(request: Request, data: LoginRequest, session: SessionDep):
    ip = _get_ip(request)
    user = session.exec(select(User).where(User.username == data.username)).first()
    if user is None or user.password_hash is None or not verify_password(data.password, user.password_hash):
        _audit(session, "login_failure", ip=ip)
        session.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    role = session.get(Role, user.role_id) if user.role_id else None
    permissions = decode_permissions(role.permissions) if role else []
    token_str = create_refresh_token_string()
    session.add(RefreshToken(
        token=token_str,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    _audit(session, "login_success", user=user, ip=ip)
    session.commit()
    return LoginResponse(
        access_token=create_access_token(user.id, settings.secret_key),
        refresh_token=token_str,
        id=user.id,
        name=user.name,
        username=user.username,
        role_name=role.name if role else "",
        permissions=permissions,
    )


@router.post("/auth/refresh", response_model=RefreshResponse, tags=["auth"])
def refresh_token(data: RefreshRequest, session: SessionDep):
    rt = session.exec(select(RefreshToken).where(RefreshToken.token == data.refresh_token)).first()
    if rt is None or rt.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")
    if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")
    user = session.get(User, rt.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return RefreshResponse(access_token=create_access_token(user.id, settings.secret_key))


@router.post("/auth/logout", tags=["auth"])
def logout(data: RefreshRequest, session: SessionDep):
    rt = session.exec(select(RefreshToken).where(RefreshToken.token == data.refresh_token)).first()
    if rt and rt.revoked_at is None:
        rt.revoked_at = datetime.now(timezone.utc)
        session.add(rt)
        session.commit()
    return {"message": "Logged out"}


# ── Roles ──────────────────────────────────────────────────────────────────────

def _role_to_read(role: Role) -> RoleRead:
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=decode_permissions(role.permissions),
    )


@router.post("/roles/", response_model=RoleRead, tags=["roles"])
def create_role(data: RoleCreate, session: SessionDep, actor: Annotated[User, _perm("roles")]):
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
    session.flush()
    _audit(session, "role_created", user=actor, resource_id=role.id)
    session.commit()
    session.refresh(role)
    return _role_to_read(role)


@router.get("/roles/", response_model=list[RoleRead], tags=["roles"])
def list_roles(session: SessionDep, _: Annotated[User, _perm("roles")]):
    roles = session.exec(select(Role)).all()
    return [_role_to_read(r) for r in roles]


@router.get("/roles/{role_id}", response_model=RoleRead, tags=["roles"])
def get_role(role_id: int, session: SessionDep, _: Annotated[User, _perm("roles")]):
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return _role_to_read(role)


@router.patch("/roles/{role_id}", response_model=RoleRead, tags=["roles"])
def update_role(role_id: int, data: RoleUpdate, session: SessionDep, _: Annotated[User, _perm("roles")]):
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
def delete_role(role_id: int, session: SessionDep, actor: Annotated[User, _perm("roles")]):
    role = session.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.name == "admin":
        raise HTTPException(status_code=400, detail="Cannot delete the built-in admin role")
    assigned = session.exec(select(User).where(User.role_id == role_id)).first()
    if assigned:
        raise HTTPException(status_code=400, detail="Cannot delete role with assigned users")
    _audit(session, "role_deleted", user=actor, resource_id=role_id)
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
def create_user(data: UserCreate, session: SessionDep, actor: Annotated[User, _perm("users")]):
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
    session.flush()
    _audit(session, "user_created", user=actor, resource_id=user.id)
    session.commit()
    session.refresh(user)
    return _user_to_read(user, session)


@router.get("/users/", response_model=list[UserRead], tags=["users"])
def list_users(
    session: SessionDep,
    _: Annotated[User, _perm("users")],
    name: Optional[str] = Query(None, description="Filter by name"),
):
    q = select(User)
    if name:
        q = q.where(User.name.ilike(f"%{name}%"))
    users = session.exec(q).all()
    return [_user_to_read(u, session) for u in users]


@router.get("/users/{user_id}", response_model=UserRead, tags=["users"])
def get_user(user_id: int, session: SessionDep, _: Annotated[User, _perm("users")]):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_read(user, session)


@router.put("/users/{user_id}", response_model=UserRead, tags=["users"])
def update_user(user_id: int, data: UserUpdate, session: SessionDep, _: Annotated[User, _perm("users")]):
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
def delete_user(user_id: int, session: SessionDep, actor: Annotated[User, _perm("users")]):
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user_id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    _audit(session, "user_deleted", user=actor, resource_id=user_id)
    session.delete(user)
    session.commit()
    return {"message": "User deleted"}


# ── Items ──────────────────────────────────────────────────────────────────────

@router.post("/items/", response_model=ItemRead, tags=["items"])
def create_item(data: ItemCreate, session: SessionDep, actor: Annotated[User, _perm("items")]):
    item = Item(**data.model_dump())
    session.add(item)
    session.flush()
    _audit(session, "item_created", user=actor, resource_id=item.id)
    session.commit()
    session.refresh(item)
    return item


@router.get("/items/", response_model=list[ItemRead], tags=["items"])
def list_items(
    session: SessionDep,
    _: Annotated[User, _perm("items")],
    name: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    available_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
):
    q = select(Item)
    if name:
        q = q.where(Item.name.ilike(f"%{name}%"))
    if category:
        q = q.where(Item.category == category)
    if available_only:
        q = q.where(Item.is_available == True)
    return session.exec(q.offset(skip).limit(limit)).all()


@router.get("/items/{item_id}", response_model=ItemRead, tags=["items"])
def get_item(item_id: int, session: SessionDep, _: Annotated[User, _perm("items")]):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/items/{item_id}", response_model=ItemRead, tags=["items"])
def update_item(item_id: int, data: ItemUpdate, session: SessionDep, actor: Annotated[User, _perm("items")]):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.updated_at = datetime.now()
    session.add(item)
    _audit(session, "item_updated", user=actor, resource_id=item_id)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/items/{item_id}", tags=["items"])
def delete_item(item_id: int, session: SessionDep, actor: Annotated[User, _perm("items")]):
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    _audit(session, "item_deleted", user=actor, resource_id=item_id)
    session.delete(item)
    session.commit()
    return {"message": "Item deleted"}


@router.patch("/items/{item_id}/stock", response_model=ItemRead, tags=["items"])
def adjust_stock(item_id: int, data: StockAdjust, session: SessionDep, actor: Annotated[User, _perm("stock")]):
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
    _audit(session, "stock_adjusted", user=actor, resource_id=item_id)
    session.commit()
    session.refresh(item)
    return item


# ── Tables ─────────────────────────────────────────────────────────────────────

@router.post("/tables/", response_model=TableRead, tags=["tables"])
def create_table(data: TableCreate, session: SessionDep, actor: Annotated[User, _perm("tables")]):
    table = TableService(session).create_table(data)
    _audit(session, "table_created", user=actor, resource_id=table.id)
    session.commit()
    return table


@router.get("/tables/", response_model=list[TableRead], tags=["tables"])
def list_tables(
    session: SessionDep,
    _: Annotated[User, _perm("tables")],
    status: Optional[str] = Query(None, description="Filter by status: Active | Closed"),
    date: Optional[str] = Query(None, description="Filter closed tables by date YYYY-MM-DD"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
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
    return session.exec(q.offset(skip).limit(limit)).all()


@router.get("/tables/{table_id}", response_model=TableReadDetailed, tags=["tables"])
def get_table(table_id: int, session: SessionDep, _: Annotated[User, _perm("tables")]):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    return table


@router.patch("/tables/{table_id}", response_model=TableRead, tags=["tables"])
def update_table(table_id: int, data: TableUpdate, session: SessionDep, actor: Annotated[User, _perm("tables")]):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(table, field, value)
    table.updated_at = datetime.now()
    session.add(table)
    _audit(session, "table_renamed", user=actor, resource_id=table_id)
    session.commit()
    session.refresh(table)
    return table


@router.post("/tables/{table_id}/close", response_model=TableRead, tags=["tables"])
def close_table(table_id: int, session: SessionDep, actor: Annotated[User, _perm("tables")]):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        table = TableService(session).close_table(table)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    _audit(session, "table_closed", user=actor, resource_id=table_id)
    session.commit()
    return table


@router.get("/tables/{table_id}/receipt", tags=["tables"])
def get_receipt(table_id: int, session: SessionDep, _: Annotated[User, _perm("tables")]):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    orders = session.exec(select(Order).where(Order.table_id == table_id)).all()
    item_ids = {o.item_id for o in orders}
    items = {i.id: i for i in session.exec(select(Item).where(Item.id.in_(item_ids))).all()} if item_ids else {}
    from services.receipt_service import build_receipt
    pdf = build_receipt(table, list(orders), items)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=receipt_{table_id}.pdf"},
    )


@router.delete("/tables/{table_id}", tags=["tables"])
def delete_table(table_id: int, session: SessionDep, actor: Annotated[User, _perm("tables")]):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    _audit(session, "table_deleted", user=actor, resource_id=table_id)
    session.delete(table)
    session.commit()
    return {"message": "Table deleted"}


# ── Orders (nested under tables) ───────────────────────────────────────────────

@router.post("/tables/{table_id}/orders/", response_model=OrderRead, tags=["orders"])
def add_order(table_id: int, data: OrderCreate, session: SessionDep, actor: Annotated[User, _perm("tables")]):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    try:
        order = TableService(session).add_order(table, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    _audit(session, "order_added", user=actor, resource_id=order.id)
    # Log override if sent discount deviates from active policy
    active_policy = _get_active_discount_for_item(data.item_id, session)
    if active_policy is not None and data.discount != active_policy.percent:
        _audit(session, "discount_override", user=actor, resource_id=order.id)
    session.commit()
    return order


@router.get("/tables/{table_id}/orders/", response_model=list[OrderRead], tags=["orders"])
def list_orders(table_id: int, session: SessionDep, _: Annotated[User, _perm("tables")]):
    table = session.get(Table, table_id)
    if table is None:
        raise HTTPException(status_code=404, detail="Table not found")
    orders = session.exec(select(Order).where(Order.table_id == table_id)).all()
    return orders


@router.get("/tables/{table_id}/orders/{order_id}", response_model=OrderRead, tags=["orders"])
def get_order(table_id: int, order_id: int, session: SessionDep, _: Annotated[User, _perm("tables")]):
    order = session.get(Order, order_id)
    if order is None or order.table_id != table_id:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/tables/{table_id}/orders/{order_id}", response_model=OrderRead, tags=["orders"])
def update_order(table_id: int, order_id: int, data: OrderUpdate, session: SessionDep, actor: Annotated[User, _perm("tables")]):
    order = session.get(Order, order_id)
    if order is None or order.table_id != table_id:
        raise HTTPException(status_code=404, detail="Order not found")

    quantity_delta = data.quantity - order.quantity

    if quantity_delta != 0:
        item = session.get(Item, order.item_id)
        if item and item.stock_qty is not None:
            if quantity_delta > 0:
                if item.stock_qty < quantity_delta:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for {item.name}. Available: {item.stock_qty}, Need: {quantity_delta}")
                item.stock_qty -= quantity_delta
            else:
                item.stock_qty -= quantity_delta
            item.updated_at = datetime.now()
            session.add(item)

    order.quantity = data.quantity
    session.add(order)
    _audit(session, "order_updated", user=actor, resource_id=order_id)
    session.commit()
    session.refresh(order)
    return order


@router.delete("/tables/{table_id}/orders/{order_id}", tags=["orders"])
def delete_order(table_id: int, order_id: int, session: SessionDep, actor: Annotated[User, _perm("tables")]):
    order = session.get(Order, order_id)
    if order is None or order.table_id != table_id:
        raise HTTPException(status_code=404, detail="Order not found")
    _audit(session, "order_deleted", user=actor, resource_id=order_id)
    session.delete(order)
    session.commit()
    return {"message": "Order deleted"}


# ── Stats ──────────────────────────────────────────────────────────────────────

def _parse_date(s: str) -> date_type:
    try:
        return date_type.fromisoformat(s)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")


@router.get("/stats/daily", response_model=DailyStats, tags=["stats"])
def daily_stats(
    session: SessionDep,
    _: Annotated[User, _perm("stats")],
    date: Optional[str] = Query(None, description="Single date YYYY-MM-DD (defaults to today)"),
    date_from: Optional[str] = Query(None, description="Range start YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="Range end YYYY-MM-DD"),
):
    if date_from:
        from_date = _parse_date(date_from)
        to_date = _parse_date(date_to) if date_to else from_date
    elif date:
        from_date = to_date = _parse_date(date)
    else:
        from_date = to_date = date_type.today()
    return TableService(session).daily_stats(from_date, to_date)


@router.get("/stats/top-items", response_model=list[TopItemStat], tags=["stats"])
def top_items(
    session: SessionDep,
    _: Annotated[User, _perm("stats")],
    date_from: Optional[str] = Query(None, description="Range start YYYY-MM-DD (default: 30 days ago)"),
    date_to: Optional[str] = Query(None, description="Range end YYYY-MM-DD (default: today)"),
    limit: int = Query(10, ge=1, le=100),
):
    to_date = _parse_date(date_to) if date_to else date_type.today()
    from_date = _parse_date(date_from) if date_from else to_date - timedelta(days=30)
    return TableService(session).top_items(from_date, to_date, limit)


# ── Discounts ──────────────────────────────────────────────────────────────────

def _policy_currently_active(policy: DiscountPolicy) -> bool:
    if not policy.is_active:
        return False
    now = datetime.now()
    if policy.valid_from > now:
        return False
    if policy.valid_until is not None and policy.valid_until < now:
        return False
    return True


def _policy_to_read(p: DiscountPolicy) -> DiscountPolicyRead:
    return DiscountPolicyRead(
        id=p.id,
        name=p.name,
        percent=p.percent,
        item_ids=_json.loads(p.item_ids),
        valid_from=p.valid_from,
        valid_until=p.valid_until,
        is_active=p.is_active,
        created_by_id=p.created_by_id,
        created_at=p.created_at,
        is_currently_active=_policy_currently_active(p),
    )


def _get_active_discount_for_item(item_id: int, session) -> DiscountPolicy | None:
    """Return the highest-percent currently-active policy that covers item_id."""
    now = datetime.now()
    policies = session.exec(
        select(DiscountPolicy)
        .where(DiscountPolicy.is_active == True)
        .where(DiscountPolicy.valid_from <= now)
        .where(
            (DiscountPolicy.valid_until == None) | (DiscountPolicy.valid_until >= now)
        )
    ).all()
    candidates = [
        p for p in policies
        if not _json.loads(p.item_ids) or item_id in _json.loads(p.item_ids)
    ]
    return max(candidates, key=lambda p: p.percent) if candidates else None


@router.get("/discounts/for-item/{item_id}", response_model=ActiveDiscountRead | None, tags=["discounts"])
def get_active_discount(item_id: int, session: SessionDep, _: Annotated[User, _perm("tables")]):
    policy = _get_active_discount_for_item(item_id, session)
    if policy is None:
        return None
    return ActiveDiscountRead(policy_id=policy.id, policy_name=policy.name, percent=policy.percent)


@router.get("/discounts/", response_model=list[DiscountPolicyRead], tags=["discounts"])
def list_discounts(session: SessionDep, _: Annotated[User, _perm("discounts")]):
    policies = session.exec(select(DiscountPolicy).order_by(DiscountPolicy.created_at.desc())).all()
    return [_policy_to_read(p) for p in policies]


@router.post("/discounts/", response_model=DiscountPolicyRead, tags=["discounts"])
def create_discount(data: DiscountPolicyCreate, session: SessionDep, actor: Annotated[User, _perm("discounts")]):
    policy = DiscountPolicy(
        name=data.name,
        percent=data.percent,
        item_ids=_json.dumps(data.item_ids),
        valid_from=data.valid_from or datetime.now(),
        valid_until=data.valid_until,
        created_by_id=actor.id,
    )
    session.add(policy)
    session.flush()
    _audit(session, "discount_created", user=actor, resource_id=policy.id)
    session.commit()
    session.refresh(policy)
    return _policy_to_read(policy)


@router.patch("/discounts/{policy_id}", response_model=DiscountPolicyRead, tags=["discounts"])
def update_discount(policy_id: int, data: DiscountPolicyUpdate, session: SessionDep, actor: Annotated[User, _perm("discounts")]):
    policy = session.get(DiscountPolicy, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Discount policy not found")
    if data.name is not None:
        policy.name = data.name
    if data.percent is not None:
        policy.percent = data.percent
    if data.item_ids is not None:
        policy.item_ids = _json.dumps(data.item_ids)
    if data.valid_from is not None:
        policy.valid_from = data.valid_from
    if "valid_until" in data.model_fields_set:
        policy.valid_until = data.valid_until
    if data.is_active is not None:
        policy.is_active = data.is_active
    session.add(policy)
    _audit(session, "discount_updated", user=actor, resource_id=policy_id)
    session.commit()
    session.refresh(policy)
    return _policy_to_read(policy)


@router.delete("/discounts/{policy_id}", tags=["discounts"])
def delete_discount(policy_id: int, session: SessionDep, actor: Annotated[User, _perm("discounts")]):
    policy = session.get(DiscountPolicy, policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="Discount policy not found")
    _audit(session, "discount_deleted", user=actor, resource_id=policy_id)
    session.delete(policy)
    session.commit()
    return {"message": "Discount policy deleted"}


# ── Audit log ──────────────────────────────────────────────────────────────────

@router.get("/audit/events", response_model=list[AuditEventRead], tags=["audit"])
def list_audit_events(
    session: SessionDep,
    _: Annotated[User, _perm("roles")],
    action: Optional[str] = Query(None, description="Filter by action"),
    limit: int = Query(100, le=500),
    skip: int = Query(0, ge=0),
):
    q = select(AuditEvent).order_by(AuditEvent.created_at.desc())
    if action:
        q = q.where(AuditEvent.action == action)
    return session.exec(q.offset(skip).limit(limit)).all()
