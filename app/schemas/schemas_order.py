from sqlmodel import SQLModel
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# ==== USER SCHEMAS ====
class UserCreate(BaseModel):
    name: str

class UserRead(BaseModel):
    id: int
    name: str


# ==== ITEM SCHEMAS ====
class ItemCreate(BaseModel):
    quantity: Optional[float] = 0.0
    name: str
    is_active: bool = True
    price: float
    uom: str  # (unit of measurement, e.g. 3 item, 500 ml, 200 gram)
    discount: Optional[float] = 0.0  # (% -1:1)


class ItemRead(BaseModel):
    id: int
    quantity: Optional[float] = 0.0
    name: str
    is_active: bool
    price: float
    uom: str  # (unit of measurement, e.g. 3 item, 500 ml, 200 gram)
    discount: Optional[float] = 0.0  # (% -1:1)


class ItemUpdate(BaseModel):
    quantity: Optional[float] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    price: Optional[float] = None
    uom: Optional[str] = None  # (unit of measurement, e.g. 3 item, 500 ml, 200 gram)
    discount: Optional[float] = None  # (% -1:1)


# ==== ORDER SCHEMAS ====
class OrderCreate(BaseModel):
    client: str
    table: str  # (where client sit)


class OrderRead(BaseModel):
    id: int
    created_at: datetime
    updated_at: datetime
    closed_at: datetime
    status: str
    client: str
    table: str  # (where client sit)


# ==== ORDER LINE SCHEMAS ====
class OrderLineCreate(BaseModel):
    order: int
    item: int
    quantity: float
    discount_amount: float


class OrderLineRead(BaseModel):
    id: int
    created_at: datetime
    order: int
    item: int
    quantity: float
    uom: str  # (unit of measurement, e.g. 3 item, 500 ml, 200 gram)
    price: float  # (fixed price at item ordering moment)
    discount_amount: float  # (% -1:1)
    final_price: float
