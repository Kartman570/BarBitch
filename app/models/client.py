from typing import Annotated, List, Optional, TYPE_CHECKING

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select, Relationship
from pydantic import BaseModel

if TYPE_CHECKING:
    from .order import Order


class Client(SQLModel, table=True):
    __tablename__ = "clients"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    
    orders: list["Order"] = Relationship(back_populates="client")


class ClientBase(BaseModel):
    name: Optional[str] = None


class ClientIn(ClientBase):
    pass


class ClientOut(ClientBase):
    id: int
    
    class Config:
        from_attributes = True


# class ClientWithMenuItems(ClientBase):
#     id: int
#     menu_items: List["MenuItemOut"] = []
    
#     class Config:
#         from_attributes = True
