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


## Development Roadmap

| Phase | Focus | Status |
| ----- | ----- | ------ |
| **Phase 1** | Basic CRUD operations | ❌ Planned |
| **Phase 2** | User authentication & shifts | ❌ Planned |
| **Phase 3** | Stock management & recipes | ❌ Planned |
| **Phase 4** | Payment processing | ❌ Planned |
| **Phase 5** | Real-time features | ❌ Planned |
| **Phase 6** | Advanced features | ❌ Planned |

---
