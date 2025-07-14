from typing import Annotated, List, TYPE_CHECKING

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import BaseModel

if TYPE_CHECKING:
    from .order import Order
    from .item import Item


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"
    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.id")
    item_id: int = Field(foreign_key="items.id")
    quantity: int = Field(index=True)
    
    order: "Order" = Relationship(back_populates="order_items")
    item: "Item" = Relationship(back_populates="order_items")


class OrderItemBase(BaseModel):
    order_id: int
    item_id: int
    quantity: int


class OrderItemIn(OrderItemBase):
    pass


class OrderItemOut(OrderItemBase):
    id: int

    class Config:
        from_attributes = True