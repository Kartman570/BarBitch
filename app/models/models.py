from typing import List
from datetime import datetime

from sqlmodel import Field, SQLModel, Relationship


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    role: str = Field(default="barman")  # admin | barman | cook


class Item(SQLModel, table=True):
    __tablename__ = "items"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    price: float
    category: str | None = Field(default=None)
    is_available: bool = Field(default=True)
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
    quantity: float = Field(default=1.0)
    price: float  # snapshot of item.price at order time
    created_at: datetime = Field(default_factory=datetime.now)

    table: Table = Relationship(back_populates="orders")
    item: Item = Relationship(back_populates="orders")
