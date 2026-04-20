from typing import List
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"
    id: int | None = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    expires_at: datetime = Field()
    revoked_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


class AuditEvent(SQLModel, table=True):
    __tablename__ = "audit_events"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None)
    username: str | None = Field(default=None, max_length=50)
    action: str = Field(max_length=50)
    resource_id: int | None = Field(default=None)
    ip: str | None = Field(default=None, max_length=45)
    created_at: datetime = Field(default_factory=datetime.now)


class Role(SQLModel, table=True):
    __tablename__ = "roles"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, max_length=50)
    description: str | None = Field(default=None)
    # JSON-encoded list of permission strings, e.g. '["tables","stock"]'
    permissions: str = Field(default="[]")

    users: List["User"] = Relationship(back_populates="role")


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    username: str | None = Field(default=None, unique=True, max_length=50)
    password_hash: str | None = Field(default=None)
    role_id: int | None = Field(default=None, foreign_key="roles.id")

    role: Role | None = Relationship(back_populates="users")


class Item(SQLModel, table=True):
    __tablename__ = "items"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    price: float
    category: str | None = Field(default=None)
    is_available: bool = Field(default=True)
    stock_qty: int | None = Field(default=None)  # None = not tracked, >= 0 = current stock
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    orders: List["Order"] = Relationship(back_populates="item")


class Table(SQLModel, table=True):
    __tablename__ = "tables"
    id: int | None = Field(default=None, primary_key=True)
    table_name: str = Field(max_length=100)
    status: str = Field(default="Active")  # Active | Closed
    total: float = Field(default=0.0)      # computed at close
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    closed_at: datetime | None = Field(default=None)

    orders: List["Order"] = Relationship(
        back_populates="table",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: int | None = Field(default=None, primary_key=True)
    table_id: int = Field(foreign_key="tables.id", index=True)
    item_id: int = Field(foreign_key="items.id", index=True)
    quantity: int = Field(default=1)
    price: float  # snapshot of item.price at order time
    discount: float = Field(default=0.0)  # percentage 0–100 applied to this line
    created_at: datetime = Field(default_factory=datetime.now)

    table: Table = Relationship(back_populates="orders")
    item: Item = Relationship(back_populates="orders")
