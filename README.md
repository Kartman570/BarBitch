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

| Phase         | Focus               | Status        |
|---------------|---------------------|---------------|
| **Phase 1**   | DB Models           | ✅ Implemented |
| **Phase 1**   | Backend API         | ✅ Implemented |
|               |                     |               |
| **Phase 1**   | Basic Frontend      | In progress   |
|               |                     |               |
| **Phase 2**   | Stock Management    | ❌ Planned     |
| **Phase 2**   | Recipe Components   | ❌ Planned     |
| **Phase 3**   | User Authentication | ❌ Planned     |
| **Phase 3**   | Shifts Management   | ❌ Planned     |
| **Phase 4**   | WebSocket Real-time | ❌ Planned     |
| **Phase 5**   | Audit Logging       | ❌ Planned     |
| **Phase 6**   | Payment Processing  | ❌ Planned     |





## Development Setup
### Build
```bash
docker compose build
docker compose up
```

### Migrations:

After changing something in `app/models` run (in container):
```bash
alembic revision --autogenerate -m "Summary of changes"
```

To migrate database:
```bash
alembic upgrade head
```