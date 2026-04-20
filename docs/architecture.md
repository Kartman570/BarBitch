# System Architecture

## Technology Stack

| Component           | Technology              | Status         |
|---------------------|-------------------------|----------------|
| Backend API         | FastAPI + SQLModel      | ✅ Implemented  |
| Database ORM        | SQLModel (SQLAlchemy)   | ✅ Implemented  |
| Database            | PostgreSQL              | ✅ Implemented  |
| Migrations          | Alembic                 | ✅ Implemented  |
| Frontend            | React + Vite (SPA)      | ✅ Implemented  |
| Reverse proxy       | nginx (optional, HTTPS) | ✅ Available    |
| Real-time           | WebSocket               | ❌ Frozen       |
| Background jobs     | Celery                  | ❌ Removed      |
| Caching             | Redis                   | ❌ Removed      |

---

## Request Flow

```
HTTP → FastAPI (app/main.py)
     → Router (app/api/router.py)
     → routes_v1.py
          → get_current_user (JWT validation, HTTPBearer)
          → TableService / AuthService (app/services/)
     → SQLModel session
     → PostgreSQL
```

Optional production path with nginx:
```
Browser → nginx (TLS termination, port 443)
        → /api/* → app:8000 (FastAPI)
        → /*     → client:5173 (Vite / React)
```

---

## API Schema

All endpoints are versioned under `/api/v1/`.
Protected routes require `Authorization: Bearer <token>` header (JWT).

```
/api/v1/

  auth/                         ✅ Implemented
      POST   /login             Authenticate → access_token (12h) + refresh_token (30d)
                                  ⚠ Only unauthenticated endpoint; rate-limited 10/minute
      POST   /refresh           Exchange refresh_token → new access_token
      POST   /logout            Revoke refresh_token

  roles/                        ✅ Implemented
      POST   /                  Create role (name, description, permissions[])
      GET    /                  List roles
      GET    /{role_id}         Get role
      PATCH  /{role_id}         Update role
      DELETE /{role_id}         Delete role (blocked if users assigned or name="admin")

  users/                        ✅ Implemented
      POST   /                  Create user
      GET    /                  List users  (filter: ?name=)
      GET    /{user_id}         Get user
      PUT    /{user_id}         Update user (name, username, password, role_id)
      DELETE /{user_id}         Delete user

  items/                        ✅ Implemented
      POST   /                  Create menu item
      GET    /                  List items  (filter: ?name=, ?category=, ?available_only=; pagination: ?skip=, ?limit=)
      GET    /{item_id}         Get item
      PUT    /{item_id}         Update item
      DELETE /{item_id}         Delete item
      PATCH  /{item_id}/stock   Adjust stock delta (positive = add, negative = remove)

  tables/                       ✅ Implemented  ("table" = one customer session / tab)
      POST   /                  Open table
      GET    /                  List tables  (filter: ?status=Active|Closed; pagination: ?skip=, ?limit=)
      GET    /{table_id}        Get table + nested orders
      PATCH  /{table_id}        Rename / update table
      POST   /{table_id}/close  Close table and lock bill total (applies per-order discounts)
      GET    /{table_id}/receipt Download PDF receipt (A6, Unicode, Cyrillic-ready)
      DELETE /{table_id}        Delete table

  tables/{table_id}/orders/     ✅ Implemented
      POST   /                  Add item to table (body: item_id, quantity, discount 0–100 %)
      GET    /                  List orders for table
      GET    /{order_id}        Get order line
      PATCH  /{order_id}        Update quantity (adjusts stock delta)
      DELETE /{order_id}        Cancel order line

  stats/                        ✅ Implemented
      GET    /daily             Daily/range summary
                                  ?date=YYYY-MM-DD          — single day (default: today)
                                  ?date_from=&date_to=      — aggregate over date range
      GET    /top-items         Top selling items by revenue
                                  ?date_from=&date_to=      — date range (default: last 30 days)
                                  ?limit=10                 — number of items to return (max 100)

  audit/                        ✅ Implemented
      GET    /events            Query audit log
                                  ?action=, ?limit=, ?skip= — filter & pagination; requires roles perm
                                  Actions: login_success/failure, role_created/deleted,
                                           user_created/deleted, table_created/renamed/closed/deleted,
                                           item_created/updated/deleted, stock_adjusted,
                                           order_added/updated/deleted
```

---

## Stats Response — `GET /api/v1/stats/daily`

```json
{
  "date": "2026-04-13",
  "revenue_total": 125.50,
  "revenue_locked": 80.00,
  "revenue_running": 45.50,
  "orders_count": 12,
  "tables_served": 4,
  "items_sold": [
    { "item_name": "Beer",    "quantity": 8.0, "revenue": 40.00 },
    { "item_name": "Nachos",  "quantity": 3.0, "revenue": 36.00 }
  ],
  "orders_log": [
    {
      "order_id": 1,
      "created_at": "2026-04-13T18:30:00",
      "table_name": "Table 1",
      "item_name": "Beer",
      "quantity": 2.0,
      "price": 5.00,
      "discount": 10.0,
      "line_total": 9.00
    }
  ]
}
```

`items_sold` is sorted by `revenue` descending. `orders_log` is sorted chronologically.
Revenue figures use the discounted line total (`price × qty × (1 − discount/100)`).

For a date range (`?date_from=2026-04-01&date_to=2026-04-07`), the `date` field returns
`"2026-04-01 / 2026-04-07"` and all fields are aggregated across the range.

---

## Top Items Response — `GET /api/v1/stats/top-items`

```json
[
  { "item_name": "Beer", "quantity": 48.0, "revenue": 240.00, "orders_count": 12 },
  { "item_name": "Nachos", "quantity": 18.0, "revenue": 216.00, "orders_count": 6 }
]
```

Sorted by `revenue` descending.

---

## DB Schema

### Phase 1 + 2 + 3 — Core (current)

```mermaid
erDiagram
    ROLE {
        int     id          PK
        string  name        "admin | manager | barman | cook"
        string  description
        string  permissions "JSON-encoded list: [\"tables\",\"items\",...]"
    }

    USER {
        int     id            PK
        string  name
        string  username      "login identifier (unique)"
        string  password_hash "bcrypt"
        int     role_id       FK
    }

    ITEM {
        int     id          PK
        string  name
        float   price       "current list price"
        string  category    "beer | cocktail | food | ..."
        bool    is_available
        float   stock_qty   "null = not tracked"
        datetime created_at
        datetime updated_at
    }

    TABLE {
        int     id          PK
        string  table_name  "human label: Table 3, Bar Tab..."
        string  status      "Active | Closed"
        float   total       "locked bill total (set on close, discount applied)"
        datetime created_at
        datetime updated_at
        datetime closed_at  "null while active"
    }

    ORDER {
        int     id          PK
        int     table_id    FK
        int     item_id     FK
        float   quantity
        float   price       "snapshot of price at order time"
        float   discount    "percentage 0–100 applied to this line"
        datetime created_at
    }

    REFRESH_TOKEN {
        int      id           PK
        string   token        "urlsafe random 32-byte string (unique)"
        int      user_id      FK
        datetime expires_at   "now + 30 days"
        datetime revoked_at   "null until logout"
        datetime created_at
    }

    AUDIT_EVENT {
        int      id           PK
        int      user_id      "null for unauthenticated actions"
        string   username
        string   action       "login_success | table_created | order_added | ..."
        int      resource_id  "null for non-resource actions"
        string   ip           "client IP (max 45 chars for IPv6)"
        datetime created_at
    }

    ROLE  ||--o{ USER          : "assigned to"
    TABLE ||--o{ ORDER         : "contains"
    ITEM  ||--o{ ORDER         : "referenced by"
    USER  ||--o{ REFRESH_TOKEN : "owns"
```

> `ORDER.price` locks the price at the moment of ordering so later price
> changes do not affect open or past bills.
> `ORDER.discount` is a percentage (0–100) reducing the line total.

**Available permissions:** `tables`, `items`, `stock`, `stats`, `users`, `roles`

---

## nginx — HTTPS Setup

The `nginx` Docker Compose service is opt-in (profile `nginx`).

```bash
# 1. Generate a self-signed cert (dev/LAN use)
mkdir -p nginx/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/key.pem -out nginx/certs/cert.pem \
  -subj "/CN=localhost"

# 2. Start with nginx
docker compose --profile nginx up
```

For production use Let's Encrypt / Certbot and replace the self-signed cert.
Update `CORS_ORIGINS` in `.env` accordingly (e.g., `https://your-domain.com`).

---

## Backlog

See `docs/roadmap.md` for the prioritised task list.
