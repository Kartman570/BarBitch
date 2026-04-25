# Development Guide

> **All commands run inside Docker containers.**
> Never run `python`, `pytest`, `alembic`, or `pip` directly on the host — the project has no local venv.

## Docker Workflow

```bash
docker compose build        # rebuild after changing requirements.txt or Dockerfile
docker compose up           # start all services (foreground)
docker compose up -d        # start in background
docker compose down         # stop all services
docker compose restart client  # restart only the frontend container (e.g. after changing VITE_CURRENCY)
```

> The `app` container runs uvicorn with `--reload` for hot-reload on file save. Remove that flag for production deployment.

## Database Migrations

Alembic config: `app/alembic.ini`. Migration files: `app/migrations/versions/`.

```bash
# After changing models, generate a new migration:
docker compose exec app alembic revision --autogenerate -m "description"

# Apply pending migrations:
docker compose exec app alembic upgrade head
```

## Database CLI

```bash
# Full init: create tables + seed roles + create admin user + seed sample menu
docker compose exec app python -m cli seed-all --admin-password <password>

# Individual steps:
docker compose exec app python -m cli init-db                                 # create tables only
docker compose exec app python -m cli seed-roles                              # insert default roles
docker compose exec app python -m cli create-user --name Admin --password <password>
docker compose exec app python -m cli seed-items --if-empty                  # add sample items if table is empty
```

## Tests

Tests use an in-memory SQLite database, isolated per test function. CI runs pytest on every push to `main` and every PR via GitHub Actions (`.github/workflows/python-app.yml`).

```bash
docker compose exec app python -m pytest tests/                    # all tests
docker compose exec app python -m pytest tests/test_v1.py         # API endpoint tests
docker compose exec app python -m pytest tests/test_auth.py       # auth, RBAC & token enforcement
docker compose exec app python -m pytest tests/test_stock.py      # stock management
docker compose exec app python -m pytest tests/test_stats.py      # daily stats
docker compose exec app python -m pytest tests/test_coverage.py   # 404 paths, filters, auth_service units, security headers
```

## Key Source Files

```
app/
  main.py                  FastAPI entry point; SecurityHeadersMiddleware, CORS, rate limiter, /api mount
  api/
    router.py              Mounts v1 sub-router under /api/v1
    routes_v1.py           All v1 endpoints; get_current_user JWT dependency; _perm() RBAC enforcement
  models/
    models.py              SQLModel table definitions (Role, User, Item, Table, Order, RefreshToken, AuditEvent, DiscountPolicy)
  schemas/
    schemas_order.py       Pydantic request/response schemas for all domains
  services/
    table_service.py       Business logic: table lifecycle, orders, stock deduction, stats aggregation
    auth_service.py        bcrypt hashing, JWT create/decode, refresh tokens, password complexity, default roles
    receipt_service.py     PDF receipt generation (fpdf2, A6, Unicode via DejaVuSans)
  core/
    database.py            SQLModel engine + get_session FastAPI dependency
    config.py              Pydantic Settings; reads SECRET_KEY (required), DEBUG, CORS_ORIGINS, etc.
    limiter.py             slowapi rate limiter instance
  fonts/
    DejaVuSans.ttf         Bundled Unicode font for PDF receipts
    DejaVuSans-Bold.ttf
  migrations/              Alembic migration files
  tests/
    conftest.py            SQLite fixtures and test client setup
    test_v1.py             API endpoint tests
    test_auth.py           Auth & RBAC tests
    test_stock.py          Stock management tests
    test_stats.py          Daily stats tests
    test_coverage.py       404 paths, filters, auth_service units, security headers

client/                    React + Vite frontend (see docs/frontend_design.md)
  src/
    i18n/                  Internationalisation layer (see docs/frontend_i18n.md)
client_legacy/             Original Streamlit stub (preserved for reference, not in use)
nginx/
  nginx.conf               Optional reverse proxy config (see docs/architecture.md — nginx section)
```

## Request Flow

```
HTTP
  → FastAPI (app/main.py)         security headers, CORS, rate limiting
  → Router (app/api/router.py)    mounts /api/v1
  → routes_v1.py                  endpoint handler
       → get_current_user()       decodes JWT Bearer token
       → _perm(name)              enforces role permission
       → TableService / AuthService
  → SQLModel session
  → PostgreSQL
```

## Auth Details

- All routes except `POST /api/v1/auth/login` require `Authorization: Bearer <token>`.
- Access tokens: HS256, 12-hour expiry. Issued by `auth_service.create_access_token()`.
- Refresh tokens: 30-day expiry, stored in `refresh_token` table, revoked on logout.
- `SECRET_KEY` must be set via environment variable — no hardcoded default. The app refuses to start without it.
- `get_current_user` dependency lives in `routes_v1.py`; it decodes the token and loads the user from the DB.

## RBAC Permission Mapping

Every route passes a permission name to `_perm()` which verifies the current user's role includes it.

| Permission   | Routes it gates |
|--------------|-----------------|
| `tables`     | `tables/*` and nested `orders/*` |
| `items`      | `items/*` (except stock) |
| `stock`      | `items/*/stock` |
| `stats`      | `stats/*` |
| `users`      | `users/*` |
| `roles`      | `roles/*` and `audit/events` |
| `discounts`  | `discounts/*` (create/update/delete/list) |

## Session Pattern

All route handlers receive `session: Session = Depends(get_session)` and pass it directly to service methods. There is no repository abstraction layer — services call SQLModel directly.
