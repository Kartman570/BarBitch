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

| Phase         | Focus                  | Status         |
|---------------|------------------------|----------------|
| **Phase 1**   | DB Models              | ✅ Done         |
| **Phase 1**   | Backend REST API       | ✅ Done         |
| **Phase 1**   | Daily Stats endpoint   | ✅ Done         |
| **Phase 1**   | Backend tests (37)     | ✅ Done         |
| **Phase 1**   | Streamlit frontend     | ✅ Done (stub)  |
| **Phase 2**   | Stock Management       | ❌ Planned      |
| **Phase 2**   | Recipe Components      | ❌ Planned      |
| **Phase 3**   | User Authentication    | ❌ Planned      |
| **Phase 3**   | Shifts Management      | ❌ Planned      |
| **Phase 4**   | WebSocket Real-time    | ❌ Planned      |
| **Phase 5**   | Audit Logging          | ❌ Planned      |
| **Phase 6**   | Payment Processing     | ❌ Planned      |


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

Default credentials: no auth in Phase 1.

### Seed initial data (first run)

```bash
docker compose exec app python -m cli seed-all
```

This creates the DB schema, an Admin user, and a sample menu.


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
docker compose exec app pytest           # all tests
docker compose exec app pytest app/tests/test_v1.py    # API tests only
docker compose exec app pytest app/tests/test_stats.py # stats tests only
```

Tests run against an in-memory SQLite database (isolated per test function).
CI runs pytest on every push to `main` and every PR via GitHub Actions.


## Project Structure

```
app/
  main.py                  FastAPI entry point
  api/
    router.py              mounts sub-routers under /api
    new_routes.py          active v1 endpoints
  models/
    models.py              SQLModel table definitions
  schemas/
    schemas_order.py       Pydantic request/response schemas
  services/
    table_service.py       business logic (table lifecycle, stats)
  core/
    database.py            engine + get_session dependency
    config.py              reads POSTGRES_URL env var
  migrations/              Alembic migration files
  tests/
    conftest.py            SQLite test fixtures
    test_v1.py             API endpoint tests (22 tests)
    test_stats.py          stats endpoint tests (14 tests + 1 smoke)
  cli.py                   management CLI (seed-all, init-db, etc.)

client/
  app.py                   Streamlit frontend
  api.py                   HTTP client wrapper for the backend API
  requirements.txt
  Dockerfile

docs/
  architecture.md          system architecture and API/DB schema
  frontend_design.md       UI screen specifications
  manual_testing.md        QA test scripts

docker-compose.yml
pyproject.toml             pytest config
```


## API Overview

All endpoints are versioned under `/api/v1/`. Full schema in `docs/architecture.md`.

| Resource       | Endpoints |
|----------------|-----------|
| Users          | CRUD `/api/v1/users/` |
| Items (menu)   | CRUD `/api/v1/items/` with `?available_only=true`, `?category=` filters |
| Tables         | CRUD `/api/v1/tables/` + `POST /tables/{id}/close` |
| Orders         | CRUD `/api/v1/tables/{id}/orders/` (nested) |
| Daily stats    | `GET /api/v1/stats/daily?date=YYYY-MM-DD` |

Interactive API docs: http://localhost:8000/docs
