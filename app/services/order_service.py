# from typing import List, Optional
# from sqlmodel import Session, select
# from models.order import Order
# from models.order_item import OrderItem
# from models.client import Client
# from models.item import Item
# from schemas.schemas_order import OrderCreate, OrderRead, OrderItemCreate, OrderItemRead
# from fastapi import HTTPException
#
#
# class OrderService:
#     def __init__(self, session: Session):
#         self.session = session
#
#     def create_order(self, order_data: OrderCreate) -> OrderRead:
#         order = Order(**order_data.dict())
#         self.session.add(order)
#         self.session.commit()
#         self.session.refresh(order)
#         return order
#
#     # def get_order_detail(self, order_id: int) -> OrderDetailOut:
#     #     order = self.session.get(Order, order_id)
#     #     if not order:
#     #         raise HTTPException(status_code=404, detail="Order not found")
#
#     #     client = self.session.get(Client, order.client_id)
#     #     if not client:
#     #         raise HTTPException(status_code=404, detail="Client not found")
#
#     #     order_items = self.session.exec(
#     #         select(OrderItem, Item)
#     #         .where(OrderItem.order_id == order_id)
#     #         .join(Item, OrderItem.item_id == Item.id)
#     #     ).all()
#
#     #     items_detail = []
#     #     for order_item, item in order_items:
#     #         items_detail.append(OrderItemDetailOut(
#     #             id=order_item.id,
#     #             item_id=item.id,
#     #             item_name=item.name,
#     #             item_price=item.price,
#     #             quantity=order_item.quantity,
#     #             total_price=item.price * order_item.quantity
#     #         ))
#
#     #     return OrderDetailOut(
#     #         id=order.id,
#     #         client_id=order.client_id,
#     #         client_name=client.name,
#     #         total_price=order.total_price,
#     #         items=items_detail,
#     #         items_count=len(items_detail)
#     #     )
#
#     # def add_items_to_order(self, order_id: int, items_data: List[OrderItemForAdd]) -> OrderDetailOut:
#     #     order = self.session.get(Order, order_id)
#     #     if not order:
#     #         raise HTTPException(status_code=404, detail="Order not found")
#
#     #     added_price = 0
#     #     for item_data in items_data:
#     #         item = self.session.get(Item, item_data.item_id)
#     #         if not item:
#     #             raise HTTPException(status_code=404, detail=f"Item {item_data.item_id} not found")
#
#     #         # Check if item already exists in order
#     #         existing_order_item = self.session.exec(
#     #             select(OrderItem)
#     #             .where(OrderItem.order_id == order_id)
#     #             .where(OrderItem.item_id == item_data.item_id)
#     #         ).first()
#
#     #         if existing_order_item:
#     #             # Update quantity
#     #             existing_order_item.quantity += item_data.quantity
#     #             added_price += item.price * item_data.quantity
#     #         else:
#     #             # Create new order item
#     #             order_item = OrderItem(
#     #                 order_id=order_id,
#     #                 item_id=item_data.item_id,
#     #                 quantity=item_data.quantity
#     #             )
#     #             self.session.add(order_item)
#     #             added_price += item.price * item_data.quantity
#
#     #     # Update order total price
#     #     order.total_price += added_price
#     #     self.session.commit()
#
#     #     return self.get_order_detail(order_id)
#
#     # def remove_item_from_order(self, order_id: int, item_id: int) -> OrderDetailOut:
#     #     order = self.session.get(Order, order_id)
#     #     if not order:
#     #         raise HTTPException(status_code=404, detail="Order not found")
#
#     #     order_item = self.session.exec(
#     #         select(OrderItem)
#     #         .where(OrderItem.order_id == order_id)
#     #         .where(OrderItem.item_id == item_id)
#     #     ).first()
#
#     #     if not order_item:
#     #         raise HTTPException(status_code=404, detail="Item not found in order")
#
#     #     item = self.session.get(Item, item_id)
#     #     if item:
#     #         # Subtract from total price
#     #         order.total_price -= item.price * order_item.quantity
#
#     #     self.session.delete(order_item)
#     #     self.session.commit()
#
#     #     return self.get_order_detail(order_id)
#
#     # def update_order_item_quantity(self, order_id: int, item_id: int, new_quantity: int) -> OrderDetailOut:
#     #     order = self.session.get(Order, order_id)
#     #     if not order:
#     #         raise HTTPException(status_code=404, detail="Order not found")
#
#     #     order_item = self.session.exec(
#     #         select(OrderItem)
#     #         .where(OrderItem.order_id == order_id)
#     #         .where(OrderItem.item_id == item_id)
#     #     ).first()
#
#     #     if not order_item:
#     #         raise HTTPException(status_code=404, detail="Item not found in order")
#
#     #     item = self.session.get(Item, item_id)
#     #     if item:
#     #         # Update total price
#     #         old_total = item.price * order_item.quantity
#     #         new_total = item.price * new_quantity
#     #         order.total_price = order.total_price - old_total + new_total
#
#     #     if new_quantity <= 0:
#     #         self.session.delete(order_item)
#     #     else:
#     #         order_item.quantity = new_quantity
#
#     #     self.session.commit()
#
#     #     return self.get_order_detail(order_id)
#
#     # def get_client_with_orders(self, client_id: int) -> ClientWithOrdersOut:
#     #     client = self.session.get(Client, client_id)
#     #     if not client:
#     #         raise HTTPException(status_code=404, detail="Client not found")
#
#     #     orders = self.session.exec(select(Order).where(Order.client_id == client_id)).all()
#
#     #     orders_detail = []
#     #     total_spent = 0
#
#     #     for order in orders:
#     #         order_detail = self.get_order_detail(order.id)
#     #         orders_detail.append(order_detail)
#     #         total_spent += order.total_price
#
#     #     return ClientWithOrdersOut(
#     #         id=client.id,
#     #         name=client.name,
#     #         orders=orders_detail,
#     #         total_orders=len(orders_detail),
#     #         total_spent=total_spent
#     #     )