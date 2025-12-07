# System Architecture

## Technology Stack

| Component | Technology | Status |
| --------- | ---------- | ------ |
| Backend API | FastAPI | ✅ Implemented |
| Database ORM | SQLModel | ✅ Implemented |
| Database | SQLite (dev) | ✅ Implemented |
| Frontend (temp) | Streamlit | ✅ Implemented |
| Frontend (planned) | Web-based | ❌ Planned |
| Real-time | WebSocket | ❌ Planned |
| Background jobs | Celery | ❌ Planned |
| Caching | Redis | ❌ Planned |


---

## API schema
```text
/api/v1/
    users/
        New
        Auth
        Current-user-info
    Items/
        CRUD
    Orders/
        Create-order
        Read-order
        List-orders
        Update-order
        Delete-order
```
---
## DB schema

```mermaid
users:
id PK
name str
//access str (admin, barmen, cook)
//status str (online, dayoff, break)
//shift ?

items:
id PK
is_active bool
name str
price float
uom str (unit of measurement, e.g. 3 item, 500 ml, 200 gram)
discount float (% -1:1)
available float (how much left in store)

orders:
id PK
created_at date
updated_at date
closed_at date
client str
status str (active, closed)
table str (where client sit)
order_lines backpopulate

order_line:
id PK
created_at date
order FK → orders
item FK → items
quantity float ( > 0.0)
price float (fixed price at item ordering moment)
discount_amount float (% -1:1)
final_price float
uom str (unit of measurement, e.g. 3 item, 500 ml, 200 gram)
```