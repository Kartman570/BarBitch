from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from services.auth_service import validate_password_complexity


# ==== ROLE SCHEMAS ====

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

class RoleRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: List[str]  # decoded from JSON

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


# ==== USER SCHEMAS ====

class UserCreate(BaseModel):
    name: str
    username: str
    password: str
    role_id: int

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return validate_password_complexity(v)

class UserRead(BaseModel):
    id: int
    name: str
    username: Optional[str]
    role_id: Optional[int]
    role_name: Optional[str] = None
    permissions: List[str] = []

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None  # plain text, will be hashed
    role_id: Optional[int] = None

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_password_complexity(v)


# ==== AUTH SCHEMAS ====

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    id: int
    name: str
    username: str
    role_name: str
    permissions: List[str]


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str


class AuditEventRead(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    resource_id: Optional[int]
    ip: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ==== ITEM SCHEMAS ====

class ItemCreate(BaseModel):
    name: str
    price: float = Field(gt=0)
    category: Optional[str] = None
    is_available: bool = True
    stock_qty: Optional[int] = Field(default=None, ge=0)

class ItemRead(BaseModel):
    id: int
    name: str
    price: float
    category: Optional[str]
    is_available: bool
    stock_qty: Optional[int] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = Field(default=None, gt=0)
    category: Optional[str] = None
    is_available: Optional[bool] = None

class StockAdjust(BaseModel):
    delta: int  # positive = add stock, negative = remove stock


# ==== TABLE SCHEMAS ====

class TableCreate(BaseModel):
    table_name: str

class TableRead(BaseModel):
    id: int
    table_name: str
    status: str
    total: float
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

class TableUpdate(BaseModel):
    table_name: Optional[str] = None

class TableReadDetailed(BaseModel):
    id: int
    table_name: str
    status: str
    total: float
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None
    orders: List["OrderRead"] = []
    model_config = ConfigDict(from_attributes=True)


# ==== ORDER SCHEMAS ====

class OrderCreate(BaseModel):
    item_id: int
    quantity: int = Field(default=1, gt=0)
    discount: float = Field(default=0.0, ge=0, le=100)

class OrderRead(BaseModel):
    id: int
    table_id: int
    item_id: int
    quantity: int
    price: float
    discount: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OrderUpdate(BaseModel):
    quantity: int = Field(gt=0)


TableReadDetailed.model_rebuild()


# ==== STATS SCHEMAS ====

class ItemStat(BaseModel):
    item_name: str
    quantity: int
    revenue: float

class OrderLogEntry(BaseModel):
    order_id: int
    created_at: datetime
    table_name: str
    item_name: str
    quantity: int
    price: float
    discount: float
    line_total: float

class DailyStats(BaseModel):
    date: str
    revenue_total: float
    revenue_locked: float   # from closed tables
    revenue_running: float  # from still-active tables
    orders_count: int
    tables_served: int
    items_sold: List[ItemStat]
    orders_log: List[OrderLogEntry]

class TopItemStat(BaseModel):
    item_name: str
    quantity: int
    revenue: float
    orders_count: int
