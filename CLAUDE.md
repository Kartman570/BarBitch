# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BarPOS** (codename: BarBitch) is an open-source bar management system — a web-native POS/stock system meant to replace proprietary solutions. MVP targets single-bar deployment on a local server.

Stack: FastAPI + SQLModel (SQLAlchemy + Pydantic) + PostgreSQL + Alembic migrations. Frontend is a temporary Streamlit stub (`client/`).

## Development Commands

> **All commands run inside Docker containers.**
> Never run `python`, `pytest`, `alembic`, or `pip` directly on the host — the project has no local venv.

### Run the project
```bash
docker compose build       # rebuild after requirements changes
docker compose up          # start all services
docker compose up -d       # start in background
docker compose down        # stop
```

- Backend API: `http://localhost:8000`
- Frontend (Streamlit): `http://localhost:8501`
- DB: PostgreSQL on `localhost:5432`

### Database migrations
```bash
docker compose exec app alembic revision --autogenerate -m "description"
docker compose exec app alembic upgrade head
```

### Database initialization (CLI)
```bash
docker compose exec app python -m cli seed-all          # init DB + admin user + seed items
docker compose exec app python -m cli init-db           # just create tables
docker compose exec app python -m cli seed-roles        # create default roles
docker compose exec app python -m cli create-user --name Admin
docker compose exec app python -m cli seed-items --if-empty
```

### Tests
```bash
docker compose exec app python -m pytest tests/                        # all tests
docker compose exec app python -m pytest tests/test_v1.py             # API endpoint tests
docker compose exec app python -m pytest tests/test_auth.py           # auth, RBAC & token enforcement
docker compose exec app python -m pytest tests/test_stock.py          # stock management tests
docker compose exec app python -m pytest tests/test_stats.py          # daily stats tests
```

Tests run against an in-memory SQLite database (isolated per test function).
CI runs pytest via GitHub Actions (`.github/workflows/python-app.yml`) on push to main and all PRs.

## Architecture

### Request Flow
```
HTTP → FastAPI (app/main.py) → Router (app/api/router.py) → routes_v1.py → get_current_user (JWT) → TableService/AuthService → SQLModel session → PostgreSQL
```

### Key files
- `app/main.py` — FastAPI app, mounts `/api` router
- `app/api/router.py` — includes v1 sub-router under `/v1`
- `app/api/routes_v1.py` — all v1 endpoints (auth, roles, users, items, tables, orders, stats)
- `app/services/table_service.py` — business logic for table/order/stats operations
- `app/services/auth_service.py` — password hashing (bcrypt), JWT token creation/decoding, default roles
- `app/models/models.py` — SQLModel table definitions (Role, User, Item, Table, Order)
- `app/schemas/schemas_order.py` — Pydantic request/response schemas
- `app/core/database.py` — engine setup and `get_session` FastAPI dependency
- `app/core/config.py` — settings (reads `POSTGRES_URL`, `SECRET_KEY` env vars)

### Auth
All routes except `POST /api/v1/auth/login` require `Authorization: Bearer <token>`.
JWT is issued on login (HS256, 12h expiry). `get_current_user` dependency in `routes_v1.py`.
Default admin credentials: **admin / admin** (created by `seed-all`).

### Data Model
- **Role** — named permission set (`permissions` JSON-encoded list)
- **User** — staff member with bcrypt password and role FK
- **Item** — menu item with optional `stock_qty` tracking
- **Table** — customer session (`status`: Active/Closed)
- **Order** — line item linking Table → Item, stores price snapshot at order time

### Active API routes (prefix `/api/v1`)
All routes require JWT except login.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/login` | Authenticate → JWT token |
| CRUD | `/roles/` | Role management |
| CRUD | `/users/` | User management |
| CRUD | `/items/` | Menu items; `PATCH /items/{id}/stock` for stock delta |
| CRUD | `/tables/` | Tables; `POST /tables/{id}/close` to lock bill |
| CRUD | `/tables/{id}/orders/` | Orders (deducts stock on create) |
| GET | `/stats/daily` | Daily revenue/orders summary |

### Migrations
Alembic config is in `app/alembic.ini`; migration files in `app/migrations/versions/`.

### Session pattern
All routes receive `session: Session = Depends(get_session)` and pass it to service methods. No repository abstraction layer — services call SQLModel directly.
