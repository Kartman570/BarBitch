from collections import defaultdict
from datetime import date, datetime, timedelta
from sqlmodel import select
from models.models import Item, Order, Table
from schemas.schemas_order import (
    TableCreate, TableRead, TableReadDetailed, OrderCreate, OrderRead,
    DailyStats, ItemStat, OrderLogEntry,
)


class TableService:
    def __init__(self, session):
        self.session = session

    def create_table(self, data: TableCreate) -> Table:
        table = Table(table_name=data.table_name)
        self.session.add(table)
        self.session.commit()
        self.session.refresh(table)
        return table

    def close_table(self, table: Table) -> Table:
        if table.status == "Closed":
            raise ValueError("Table is already closed")
        orders = self.session.exec(select(Order).where(Order.table_id == table.id)).all()
        table.total = sum(o.price * o.quantity for o in orders)
        table.status = "Closed"
        table.closed_at = datetime.now()
        table.updated_at = datetime.now()
        self.session.add(table)
        self.session.commit()
        self.session.refresh(table)
        return table

    def daily_stats(self, target_date: date) -> DailyStats:
        start = datetime.combine(target_date, datetime.min.time())
        end = start + timedelta(days=1)

        orders = self.session.exec(
            select(Order).where(Order.created_at >= start, Order.created_at < end)
        ).all()

        if not orders:
            return DailyStats(
                date=target_date.isoformat(),
                revenue_total=0.0, revenue_locked=0.0, revenue_running=0.0,
                orders_count=0, tables_served=0, items_sold=[], orders_log=[],
            )

        # Fetch referenced items and tables in bulk
        item_ids = list({o.item_id for o in orders})
        table_ids = list({o.table_id for o in orders})
        items = {i.id: i for i in self.session.exec(select(Item).where(Item.id.in_(item_ids))).all()}
        tables = {t.id: t for t in self.session.exec(select(Table).where(Table.id.in_(table_ids))).all()}

        # Revenue split
        revenue_total = sum(o.price * o.quantity for o in orders)
        revenue_locked = sum(
            o.price * o.quantity for o in orders
            if tables.get(o.table_id) and tables[o.table_id].status == "Closed"
        )

        # Items breakdown
        item_agg: dict = defaultdict(lambda: {"quantity": 0.0, "revenue": 0.0})
        for o in orders:
            name = items[o.item_id].name if o.item_id in items else f"Item #{o.item_id}"
            item_agg[name]["quantity"] += o.quantity
            item_agg[name]["revenue"] += o.price * o.quantity

        items_sold = [
            ItemStat(item_name=name, quantity=round(v["quantity"], 2), revenue=round(v["revenue"], 2))
            for name, v in sorted(item_agg.items(), key=lambda x: -x[1]["revenue"])
        ]

        # Orders log sorted chronologically
        orders_log = sorted([
            OrderLogEntry(
                order_id=o.id,
                created_at=o.created_at,
                table_name=tables[o.table_id].table_name if o.table_id in tables else f"Table #{o.table_id}",
                item_name=items[o.item_id].name if o.item_id in items else f"Item #{o.item_id}",
                quantity=o.quantity,
                price=o.price,
                line_total=round(o.price * o.quantity, 2),
            )
            for o in orders
        ], key=lambda e: e.created_at)

        return DailyStats(
            date=target_date.isoformat(),
            revenue_total=round(revenue_total, 2),
            revenue_locked=round(revenue_locked, 2),
            revenue_running=round(revenue_total - revenue_locked, 2),
            orders_count=len(orders),
            tables_served=len(table_ids),
            items_sold=items_sold,
            orders_log=orders_log,
        )

    def add_order(self, table: Table, data: OrderCreate) -> Order:
        if table.status == "Closed":
            raise ValueError("Cannot add orders to a closed table")
        item = self.session.get(Item, data.item_id)
        if item is None:
            raise LookupError(f"Item {data.item_id} not found")
        order = Order(
            table_id=table.id,
            item_id=data.item_id,
            quantity=data.quantity,
            price=item.price,  # price snapshot
        )
        self.session.add(order)
        table.updated_at = datetime.now()
        self.session.add(table)
        self.session.commit()
        self.session.refresh(order)
        return order
