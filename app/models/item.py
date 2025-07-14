from typing import Annotated, List, Optional, TYPE_CHECKING

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import BaseModel

if TYPE_CHECKING:
    from .order_item import OrderItem


class Item(SQLModel, table=True):
    __tablename__ = "items"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price: float = Field(index=True)
    
    order_items: list["OrderItem"] = Relationship(back_populates="item")


class ItemBase(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class ItemIn(ItemBase):
    pass


class ItemOut(ItemBase):
    id: int

    class Config:
        from_attributes = True