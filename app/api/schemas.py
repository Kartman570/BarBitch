from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ItemDetailOut(BaseModel):
    id: int
    name: str
    price: float
    
    class Config:
        from_attributes = True


class OrderItemDetailOut(BaseModel):
    id: int
    item_id: int
    item_name: str
    item_price: float
    quantity: int
    total_price: float  # item_price * quantity
    
    class Config:
        from_attributes = True


class OrderDetailOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    total_price: float
    items: List[OrderItemDetailOut]
    items_count: int
    
    class Config:
        from_attributes = True


class ClientWithOrdersOut(BaseModel):
    id: int
    name: str
    orders: List[OrderDetailOut]
    total_orders: int
    total_spent: float
    
    class Config:
        from_attributes = True


class OrderItemForAdd(BaseModel):
    item_id: int
    quantity: int


class AddItemsToOrderIn(BaseModel):
    items: List[OrderItemForAdd]


class UpdateOrderItemIn(BaseModel):
    quantity: int 