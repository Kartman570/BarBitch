v_0.1.0
# BarPOS — Open‑Source Bar Management System
**MVP Scope** - Single bar deployment (one local server). FastAPI + SQLModel.


## Purpose

BarPOS is an open‑source, (**licensename_TODO**)‑licensed application that replaces proprietary bar POS/stock systems.
It aims to be easy to deploy on a single local server (one bar → one instance) while remaining extensible for multi‑location setups later.

## Core Principles

| Principle                | Explanation                                                                                                          |
|--------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Freedom (OpenSource)** | Anyone can use, fork, or build SaaS offerings without copyleft restrictions.                                         |
| **Web‑native**           | Front end runs entirely in the browser - easy access from any device (pc, smartphone, etc.). No platform lock‑in.    |
| **Offline‑capable**      | Architecture allows to deploy local instance within WiFi network. No need in external server or even internet access |
| **Transparent**          | Audit log planned for money‑ and stock‑affecting actions.                                                            |



## Current Implementation Status

| Phase         | Focus                          | Status         |
|---------------|--------------------------------|----------------|
| **Phase 1**   | DB Models                      | ✅ Done         |
| **Phase 1**   | Backend REST API               | ✅ Done         |
| **Phase 1**   | Daily Stats endpoint           | ✅ Done         |
| **Phase 1**   | Backend tests                  | ✅ Done         |
| **Phase 1**   | Streamlit frontend             | ✅ Done (stub)  |
| **Phase 2**   | Stock Management               | ✅ Done         |
| **Phase 2**   | Low-stock alerts               | ❌ Planned      |
| **Phase 2**   | Recipe Components              | ❌ Planned      |
| **Phase 3**   | User Authentication + RBAC     | ✅ Done         |
| **Phase 3**   | JWT enforcement on all routes  | ✅ Done         |
| **Phase 3**   | Token expiry → redirect login  | ✅ Done         |
| **Phase 3**   | Refresh token + revocation     | ✅ Done         |
| **Phase 3**   | Password complexity policy     | ✅ Done         |
| **Phase 3**   | Rate limiting (login)          | ✅ Done         |
| **Phase 3**   | Security headers + CORS        | ✅ Done         |
| **Phase 3**   | Multilanguage support (EN/RU/KA) | ✅ Done       |
| **Phase 3**   | Pagination on list endpoints   | ❌ Planned      |
| **Phase 3**   | Shifts Management              | ❌ Planned      |
| **Phase 4**   | Bill / receipt export (PDF)    | ✅ Done         |
| **Phase 4**   | WebSocket Real-time            | ❌ Planned      |
| **Phase 5**   | Audit Logging                  | ✅ Done         |
| **Phase 5**   | Discount Policy System         | ✅ Done         |
| **Phase 6**   | Payment Processing             | ❌ Planned      |


## Quick Start

```bash
docker compose build
docker compose up
```

| Service   | URL                      |
|-----------|--------------------------|
| Frontend  | http://localhost:8501    |
| API       | http://localhost:8000    |
| API docs  | http://localhost:8000/docs |
| DB        | localhost:5432           |

Default credentials: **admin / admin** (created by `seed-all`).

> **Note:** Existing accounts created before the password complexity policy (≥8 chars + digit/special) are not affected retroactively.

### Seed initial data (first run)

```bash
docker compose exec app python -m cli seed-all
```

This creates the DB schema, an Admin user, and a sample menu.


## Configuration

All settings live in `.env` (copy from `.env.example`).

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | ✅ | — | JWT signing key. Generate: `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | ✅ | `postgres` | PostgreSQL password |
| `DEBUG` | — | `true` | Set `false` in production to hide `/docs` |
| `RECEIPT_QR` | — | `""` | URL encoded as QR code on printed receipts |
| `RECEIPT_QR_TITLE` | — | `""` | Caption text below the QR code |
| `VITE_CURRENCY` | — | `RUB` | Currency symbol in the UI: `RUB` (₽), `USD` ($), `EUR` (€), `GEL` (₾) |

> **Changing currency:** set `VITE_CURRENCY=GEL` (or `USD`/`EUR`) in `.env`, then restart the client container:
> ```bash
> docker compose restart client
> ```
> No rebuild needed. The backend is not affected — it stores only numeric values.

## Development Setup

### Database migrations (run inside `app/` container)

```bash
# After changing models:
docker compose exec app alembic revision --autogenerate -m "description"
docker compose exec app alembic upgrade head
```

### Database initialization (CLI)

```bash
docker compose exec app python -m cli seed-all       # init DB + admin user + seed items
docker compose exec app python -m cli init-db        # just create tables
docker compose exec app python -m cli create-user --name Admin
docker compose exec app python -m cli seed-items --if-empty
```

### Tests

```bash
docker compose exec app pytest                          # all tests
docker compose exec app pytest app/tests/test_v1.py    # API endpoint tests
docker compose exec app pytest app/tests/test_auth.py  # auth & RBAC tests
docker compose exec app pytest app/tests/test_stock.py # stock management tests
docker compose exec app pytest app/tests/test_stats.py # daily stats tests
```

Tests run against an in-memory SQLite database (isolated per test function).
CI runs pytest on every push to `main` and every PR via GitHub Actions.


## Project Structure

```
app/
  main.py                  FastAPI entry point
  api/
    router.py              mounts sub-routers under /api
    routes_v1.py           active v1 endpoints (auth, roles, users, items, tables, orders, stats, discounts)
  models/
    models.py              SQLModel table definitions (Role, User, Item, Table, Order, DiscountPolicy)
  schemas/
    schemas_order.py       Pydantic request/response schemas
  services/
    table_service.py       business logic (table lifecycle, orders, stock, stats)
    auth_service.py        password hashing (bcrypt), JWT, refresh tokens, default roles
    receipt_service.py     PDF receipt generation (fpdf2, A6, Unicode)
  fonts/
    DejaVuSans.ttf         bundled Unicode font for PDF receipts
    DejaVuSans-Bold.ttf
  core/
    database.py            engine + get_session dependency
    config.py              reads POSTGRES_URL, SECRET_KEY env vars
  migrations/              Alembic migration files
  tests/
    conftest.py            SQLite test fixtures
    test_v1.py             API endpoint tests
    test_auth.py           auth & RBAC tests
    test_stock.py          stock management tests
    test_stats.py          daily stats tests
  cli.py                   management CLI (seed-all, init-db, seed-roles, create-user, seed-items)

client/
  app.py                   Streamlit frontend (permission-aware UI)
  api.py                   HTTP client wrapper for the backend API
  requirements.txt
  Dockerfile

docs/
  architecture.md          system architecture and API/DB schema
  frontend_design.md       UI screen specifications
  manual_testing.md        QA test scripts
  user_management.md       role & permission system details

docker-compose.yml
pyproject.toml             pytest config
```


## API Overview

All endpoints are versioned under `/api/v1/`. All routes except login require `Authorization: Bearer <token>`. Full schema in `docs/architecture.md`.

| Resource       | Endpoints |
|----------------|-----------|
| Auth           | `POST /auth/login` → access + refresh token; `POST /auth/refresh`; `POST /auth/logout` |
| Roles          | CRUD `/api/v1/roles/` |
| Users          | CRUD `/api/v1/users/` + `?name=` filter |
| Items (menu)   | CRUD `/api/v1/items/` with `?name=`, `?category=`, `?available_only=` filters; `PATCH /items/{id}/stock` (delta adjustment) |
| Tables         | CRUD `/api/v1/tables/` + `POST /tables/{id}/close` |
| Receipt        | `GET /api/v1/tables/{id}/receipt` → PDF download (A6, Unicode) |
| Orders         | CRUD `/api/v1/tables/{id}/orders/` (nested; deducts stock on create) |
| Daily stats    | `GET /api/v1/stats/daily?date=YYYY-MM-DD` |
| Discounts      | CRUD `/api/v1/discounts/` (requires `discounts` permission); `GET /discounts/for-item/{id}` returns active policy for barmen |
| Audit log      | `GET /api/v1/audit/events` (requires `roles` permission) |

Interactive API docs: http://localhost:8000/docs
