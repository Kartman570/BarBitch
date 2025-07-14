from typing import Annotated, List, TYPE_CHECKING

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import BaseModel

if TYPE_CHECKING:
    from .order_item import OrderItem
    from .client import Client


class Order(SQLModel, table=True):
    __tablename__ = "orders"
    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="clients.id")
    total_price: float = Field(index=True)
    
    order_items: list["OrderItem"] = Relationship(back_populates="order")
    client: "Client" = Relationship(back_populates="orders")


class OrderBase(BaseModel):
    client_id: int
    total_price: float


class OrderIn(OrderBase):
    pass


class OrderOut(OrderBase):
    id: int

    class Config:
        from_attributes = True