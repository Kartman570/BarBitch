from typing import Annotated, List, TYPE_CHECKING
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import BaseModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default="New user name", max_length=20)


class Item(SQLModel, table=True):
    __tablename__ = "items"
    id: int | None = Field(default=None, primary_key=True)
    is_active: bool = Field(default=None)
    name: str = Field(default="New item name", max_length=40)
    price: float = Field()
    uom: str = Field(default="item")
    discount: float = Field(default=0.0)
    available: float = Field(default=0.0)

    order_lines: List["OrderLine"] = Relationship(back_populates="item")


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    closed_at: datetime | None = Field(default=None)
    client: str = Field(default="New client")
    status: str = Field(default="Active")
    table: str = Field(default="Table_1")

    # order_line: list["OrderLine"] = Relationship(back_populates="order")
    order_lines: List["OrderLine"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class OrderLine(SQLModel, table=True):
    __tablename__ = "order_lines"
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    order_id: int = Field(foreign_key="orders.id", index=True)
    order: Order = Relationship(back_populates="order_lines")
    item_id: int = Field(foreign_key="items.id", index=True)
    item: Item = Relationship(back_populates="order_lines")

    quantity: float = Field(default=1.0)
    uom: str = Field(default="item")
    price: float = Field(default=1.0)  # (fixed price at item ordering moment)

    discount_amount: float = Field(default=0.0)
    final_price: float = Field(default=1.0)
