from fastapi import APIRouter, HTTPException, Query, Depends
from app.models.order import Order, OrderIn, OrderOut
from app.models.order_item import OrderItem, OrderItemIn, OrderItemOut
from app.models.client import Client
from app.models.item import Item
from app.core.database import SessionDep
from sqlmodel import select
from typing import Optional, List
from pydantic import BaseModel
from app.services.order_service import OrderService
from app.api.schemas import OrderDetailOut, ClientWithOrdersOut, AddItemsToOrderIn, UpdateOrderItemIn

router = APIRouter()


class OrderItemForCreation(BaseModel):
    item_id: int
    quantity: int


class OrderWithItemsIn(BaseModel):
    client_id: int
    items: List[OrderItemForCreation]


class OrderWithItemsOut(BaseModel):
    id: int
    client_id: int
    total_price: float
    items: List[OrderItemOut]
    
    class Config:
        from_attributes = True


def get_order_service(session: SessionDep) -> OrderService:
    return OrderService(session)


@router.post("/orders/", response_model=OrderOut)
def create_order(order_data: OrderIn, session: SessionDep) -> OrderOut:
    client = session.get(Client, order_data.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    order = Order(**order_data.dict())
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.post("/orders/with-items/", response_model=OrderWithItemsOut)
def create_order_with_items(order_data: OrderWithItemsIn, session: SessionDep) -> OrderWithItemsOut:
    client = session.get(Client, order_data.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    total_price = 0
    for item_data in order_data.items:
        item = session.get(Item, item_data.item_id)
        if item is None:
            raise HTTPException(status_code=404, detail=f"Item {item_data.item_id} not found")
        total_price += item.price * item_data.quantity
    
    order = Order(client_id=order_data.client_id, total_price=total_price)
    session.add(order)
    session.commit()
    session.refresh(order)
    
    order_items = []
    for item_data in order_data.items:
        order_item = OrderItem(
            order_id=order.id,
            item_id=item_data.item_id,
            quantity=item_data.quantity
        )
        session.add(order_item)
        order_items.append(order_item)
    
    session.commit()
    
    for order_item in order_items:
        session.refresh(order_item)
    
    return OrderWithItemsOut(
        id=order.id,
        client_id=order.client_id,
        total_price=order.total_price,
        items=order_items
    )


@router.get("/orders/", response_model=list[OrderOut])
def list_orders(
    session: SessionDep,
    client_id: Optional[int] = Query(None, description="Filter orders by client"),
    min_price: Optional[float] = Query(None, description="Minimum total price"),
    max_price: Optional[float] = Query(None, description="Maximum total price"),
    limit: Optional[int] = Query(None, description="Limit number of results"),
    offset: Optional[int] = Query(0, description="Offset for pagination")
) -> list[OrderOut]:
    query = select(Order)
    
    if client_id:
        query = query.where(Order.client_id == client_id)
    
    if min_price is not None:
        query = query.where(Order.total_price >= min_price)
    
    if max_price is not None:
        query = query.where(Order.total_price <= max_price)
    
    if offset:
        query = query.offset(offset)
    
    if limit:
        query = query.limit(limit)
    
    orders = session.exec(query).all()
    return orders


@router.get("/orders/count")
def count_orders(session: SessionDep):
    query = select(Order)
    orders = session.exec(query).all()
    return {"count": len(orders)}


@router.get("/orders/{order_id}", response_model=OrderOut)
def get_order(order_id: int, session: SessionDep) -> OrderOut:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/orders/{order_id}/items", response_model=list[OrderItemOut])
def get_order_items(order_id: int, session: SessionDep) -> list[OrderItemOut]:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_items = session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all()
    return order_items


@router.put("/orders/{order_id}", response_model=OrderOut)
def update_order(order_id: int, order_data: OrderIn, session: SessionDep) -> OrderOut:
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    client = session.get(Client, order_data.client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    for field, value in order_data.dict().items():
        setattr(order, field, value)
    
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.delete("/orders/{order_id}")
def delete_order(order_id: int, session: SessionDep):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    
    session.exec(select(OrderItem).where(OrderItem.order_id == order_id))
    for order_item in session.exec(select(OrderItem).where(OrderItem.order_id == order_id)).all():
        session.delete(order_item)
    
    session.delete(order)
    session.commit()
    return {"message": "Order deleted successfully"}


@router.get("/clients/{client_id}/orders", response_model=list[OrderOut])
def get_client_orders(client_id: int, session: SessionDep) -> list[OrderOut]:
    client = session.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    orders = session.exec(select(Order).where(Order.client_id == client_id)).all()
    return orders


# NEW HUMAN-READABLE ENDPOINTS

@router.get("/orders/{order_id}/detail", response_model=OrderDetailOut)
def get_order_detail(order_id: int, order_service: OrderService = Depends(get_order_service)) -> OrderDetailOut:
    return order_service.get_order_detail(order_id)


@router.post("/orders/{order_id}/add-items", response_model=OrderDetailOut)
def add_items_to_order(
    order_id: int, 
    items_data: AddItemsToOrderIn, 
    order_service: OrderService = Depends(get_order_service)
) -> OrderDetailOut:
    return order_service.add_items_to_order(order_id, items_data.items)


@router.delete("/orders/{order_id}/items/{item_id}", response_model=OrderDetailOut)
def remove_item_from_order(
    order_id: int, 
    item_id: int, 
    order_service: OrderService = Depends(get_order_service)
) -> OrderDetailOut:
    return order_service.remove_item_from_order(order_id, item_id)


@router.put("/orders/{order_id}/items/{item_id}", response_model=OrderDetailOut)
def update_order_item_quantity(
    order_id: int, 
    item_id: int, 
    quantity_data: UpdateOrderItemIn, 
    order_service: OrderService = Depends(get_order_service)
) -> OrderDetailOut:
    return order_service.update_order_item_quantity(order_id, item_id, quantity_data.quantity)


@router.get("/clients/{client_id}/profile", response_model=ClientWithOrdersOut)
def get_client_profile(
    client_id: int, 
    order_service: OrderService = Depends(get_order_service)
) -> ClientWithOrdersOut:
    return order_service.get_client_with_orders(client_id) 