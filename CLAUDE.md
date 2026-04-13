# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**BarPOS** (codename: BarBitch) is an open-source bar management system — a web-native POS/stock system meant to replace proprietary solutions. MVP targets single-bar deployment on a local server.

Stack: FastAPI + SQLModel (SQLAlchemy + Pydantic) + PostgreSQL + Alembic migrations. Frontend is a temporary Streamlit stub (`client/`).

## Development Commands

### Run the project
```bash
docker compose build
docker compose up
```
- Backend API: `http://localhost:8000`
- Frontend (Streamlit): `http://localhost:8501`
- DB: PostgreSQL on `localhost:5432`

### Database migrations (run inside `app/` container or directory)
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Database initialization (CLI, run inside `app/`)
```bash
python -m cli seed-all       # init DB + create admin user + seed items
python -m cli init-db        # just create tables
python -m cli create-user --name Admin
python -m cli seed-items --if-empty
```

### Tests
```bash
pytest                        # from repo root (configured in pyproject.toml)
pytest app/tests/test_item.py # single file
```

CI runs pytest via GitHub Actions (`.github/workflows/python-app.yml`) on push to main and all PRs.

## Architecture

### Request Flow
```
HTTP → FastAPI (app/main.py) → Router (app/api/router.py) → new_routes.py → TableService → SQLModel session → PostgreSQL
```

### Key files
- `app/main.py` — FastAPI app, mounts `/api` router
- `app/api/router.py` — includes sub-routers
- `app/api/new_routes.py` — **active** endpoints for users, items, tables
- `app/services/table_service.py` — business logic for table/order operations
- `app/models/models.py` — SQLModel table definitions
- `app/schemas/schemas_order.py` — Pydantic request/response schemas
- `app/core/database.py` — engine setup and `get_session` FastAPI dependency
- `app/core/config.py` — settings (reads `POSTGRES_URL` env var)

### Data Model
- **Table** — represents a physical bar table / customer session (`status`: Active/Closed, cascade deletes its Orders)
- **Order** — a line item on a table's bill (links Table → Item, stores price at time of order)
- **Item** — menu item with price
- **User** — staff user (minimal, no auth yet)

### Active API routes (prefix `/api/new_router`)
| Method | Path | Description |
|--------|------|-------------|
| POST | `/users/` | Create user |
| GET | `/users/` | List users |
| POST | `/items/` | Create item |
| GET | `/items/` | List items |
| GET | `/items/{item_id}` | Get item |
| DELETE | `/items/{item_id}` | Delete item |
| POST | `/tables/` | Create table |

Order CRUD endpoints exist in the codebase but are commented out.

### Migrations
Alembic config is in `app/alembic.ini`; migration files in `app/migrations/versions/`. The env.py imports all SQLModel metadata so autogenerate detects model changes automatically.

### Session pattern
All routes receive `session: Session = Depends(get_session)` and pass it to service methods. No repository abstraction layer — services call SQLModel directly.
