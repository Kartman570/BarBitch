# WORK IN PROGRESS
# BarPOS — Open‑Source Bar Management System

## Purpose

BarPOS is an open‑source, MIT‑licensed application that replaces proprietary bar POS/stock systems. It aims to be easy to deploy on a single local server (one bar → one instance) while remaining extensible for multi‑location setups later.

## Core Principles

| Principle           | Explanation                                                                      |
| ------------------- | -------------------------------------------------------------------------------- |
| **Freedom (MIT)**   | Anyone can use, fork, or build SaaS offerings without copyleft restrictions.     |
| **Web‑native**      | Runs entirely in the browser; no platform lock‑in.                               |
| **Real‑time**       | Planned WebSocket‑driven updates (orders, stock) - not yet implemented.         |
| **Offline‑capable** | Planned Service‑worker cache + outbox queue - not yet implemented.               |
| **Modular**         | Clean FastAPI structure with separate models, services, and API endpoints.       |
| **Transparent**     | Audit log planned for money‑ and stock‑affecting actions.                       |
| **Tested**          | Test coverage planned with pytest and httpx.                                    |

## High‑Level Architecture

```
Streamlit UI (temporary)
          ▲
          │ HTTP API calls
          ▼
      FastAPI + SQLModel
               │
               └─ SQLite (development)
```

**Note:** Current implementation uses Streamlit for rapid prototyping. Production UI will be web-based.

## Current Implementation Status

| Module                     | Status                                       |
| -------------------------- | -------------------------------------------- |
| Basic Models               | ✅ Client, Order, OrderItem, Item            |
| FastAPI Backend            | ✅ Basic CRUD endpoints                      |
| Streamlit Frontend         | ✅ Client and order management               |
| SQLModel Database          | ✅ SQLite for development                    |
| **Not Yet Implemented:**   |                                              |
| Product Categories         | ❌ Planned                                   |
| Stock Management           | ❌ Planned                                   |
| User Authentication        | ❌ Planned                                   |
| Shifts Management          | ❌ Planned                                   |
| Payment Processing         | ❌ Planned                                   |
| WebSocket Real-time        | ❌ Planned                                   |
| Recipe Components          | ❌ Planned                                   |
| Audit Logging              | ❌ Planned                                   |

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

## Development Roadmap

| Phase | Focus | Status |
| ----- | ----- | ------ |
| **Phase 1** | Basic CRUD operations | ✅ In Progress |
| **Phase 2** | User authentication & shifts | ❌ Planned |
| **Phase 3** | Stock management & recipes | ❌ Planned |
| **Phase 4** | Payment processing | ❌ Planned |
| **Phase 5** | Real-time features | ❌ Planned |
| **Phase 6** | Advanced features | ❌ Planned |

---
