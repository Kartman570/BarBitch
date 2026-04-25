# BarPOS — Open-Source Bar Management System

An open-source web-native POS and stock system for bars, designed to replace proprietary solutions. Deploys on a single local server; no internet connection required during operation.

## Features

- **Tables & Orders** — open tabs, add items, track running totals, close bills
- **Menu Management** — item catalog with categories, availability toggles, and optional stock tracking
- **Staff & RBAC** — role-based access control with four built-in roles (admin, manager, barman, cook)
- **Daily Statistics** — revenue breakdown (locked vs. running), items sold, orders log
- **Discount Policies** — time-bounded, per-item or global discount rules with audit trail
- **PDF Receipts** — A6 Unicode-ready receipts with optional QR code
- **Audit Log** — tracks all money- and stock-affecting actions
- **Multilanguage UI** — English, Russian, Georgian (KA) via built-in i18n layer

## Quick Start

### One-command setup (recommended)

```bash
./start.sh
```

The script creates `.env`, generates a `SECRET_KEY`, builds images, runs migrations, seeds default roles and a sample menu, and runs the test suite. You will be prompted for the admin password.

Non-interactive:
```bash
./start.sh --admin-password=yourpassword
```

### Manual setup

```bash
cp .env.example .env          # set SECRET_KEY and POSTGRES_PASSWORD
docker compose build
docker compose up -d
docker compose exec app alembic upgrade head
docker compose exec app python -m cli seed-all --admin-password <password>
```

### Service URLs

| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173      |
| API      | http://localhost:8000      |
| API docs | http://localhost:8000/docs |
| Database | localhost:5432             |

### Default credentials

After seeding: `username=admin` / `password=admin` — **change before production use.**

## Configuration

All settings live in `.env` (copy from `.env.example`).

| Variable            | Required | Default | Description |
|---------------------|----------|---------|-------------|
| `SECRET_KEY`        | ✅       | —       | JWT signing key. Generate: `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | ✅       | `postgres` | PostgreSQL password |
| `DEBUG`             |          | `true`  | Set `false` in production to hide `/docs` |
| `RECEIPT_QR`        |          | `""`    | URL encoded as QR code on printed receipts |
| `RECEIPT_QR_TITLE`  |          | `""`    | Caption text below the QR code |
| `VITE_CURRENCY`     |          | `USD`   | Currency symbol shown in the UI (`USD` → `$`, `EUR` → `€`, `GEL` → `₾`, `RUB` → `₽`) |

> **Changing currency:** update `VITE_CURRENCY` in `.env`, then `docker compose restart client`. No rebuild needed.

## Documentation

| Document | Contents |
|----------|----------|
| [docs/architecture.md](docs/architecture.md) | Tech stack, request flow, full API schema, DB schema, nginx HTTPS setup |
| [docs/development.md](docs/development.md) | Docker commands, migrations, CLI, tests, key source files |
| [docs/user_management.md](docs/user_management.md) | RBAC roles, permissions, authentication flow |
| [docs/frontend_design.md](docs/frontend_design.md) | UI screens, components, user flows |
| [docs/frontend_i18n.md](docs/frontend_i18n.md) | Internationalisation layer (EN/RU/KA) |
