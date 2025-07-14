# System Architecture

> **Scope:** single‑bar deployment (one local server), current implementation with FastAPI + SQLModel.

---

## 1. Current Architecture

```mermaid
flowchart LR
    subgraph Frontend Streamlit UI Temporary
        ui[Streamlit Dashboard]
        api_calls[HTTP API Calls]
    end

    subgraph Backend FastAPI Application
        fastapi[FastAPI Routes]
        sqlmodel[SQLModel ORM]
        sqlite[(SQLite Database)]
    end

    ui --> api_calls
    api_calls -- HTTP --> fastapi
    fastapi --> sqlmodel
    sqlmodel --> sqlite
```

* **Frontend (Temporary):** Streamlit-based UI for rapid prototyping and testing
* **Backend API:** FastAPI with automatic OpenAPI documentation  
* **Database:** SQLModel ORM with SQLite for development
* **No real-time features yet:** WebSocket, Redis, and background jobs planned for future

---

## 2. Current Component Responsibilities

| Component | Technology | Current Responsibilities |
| --------- | ---------- | ----------------------- |
| **Streamlit UI** | Streamlit | Client management, order creation, basic CRUD operations |
| **FastAPI Backend** | FastAPI | REST API endpoints, request validation, business logic |
| **SQLModel ORM** | SQLModel | Database models, relationships, query building |
| **SQLite Database** | SQLite | Data persistence for development |

---

## 3. Planned Architecture (Future)

```mermaid
flowchart LR
    subgraph Client [FrontEnd]
        ui["Web UI (HTML + CSS + JS)"]
        ws[WebSocket Client]
        apiReq[REST API Calls]
    end

    subgraph Backend [BackEnd]
        fastapi[FastAPI Routes]
        websocket[WebSocket Endpoints]
        sqlmodel[SQLModel ORM]
        celery[Celery Worker]
    end

    subgraph DB [DB]
        redis[(Redis Pub/Sub)]
        postgres[(PostgreSQL)]
    end

    ui --> apiReq
    apiReq --HTTPS--> fastapi
    ui <-->|bidirectional| ws
    ws --WebSocket--> websocket
    websocket --> redis[(Redis Pub/Sub)]
    fastapi --> sqlmodel
    sqlmodel --> postgres[(PostgreSQL)]
    celery --> sqlmodel
    celery <-->|Broker| redis

```

**Planned additions:**
* **Web-based UI:** Replace Streamlit with proper web interface
* **WebSocket:** Real-time order updates
* **Redis:** Message broker and caching
* **PostgreSQL:** Production database
* **Celery:** Background tasks (reports, notifications)

---

## 4. Current API Structure

### Implemented Endpoints

| Endpoint | Method | Description |
| -------- | ------ | ----------- |
| `/` | GET | Health check |
| `/api/clients/` | GET, POST | Client management |
| `/api/items/` | GET, POST | Item management |
| `/api/orders/` | GET, POST | Order management |

### API Documentation

FastAPI automatically generates OpenAPI documentation at `/docs` and `/redoc`.

---

## 5. Deployment (Current)

### Development Setup

```bash
# Backend
cd app/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py

# Frontend (separate terminal)
cd frontend/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run front.py
```

### Planned Production Setup

```mermaid
flowchart TD
    compose[Docker Compose]
    compose --> fastapi[FastAPI Container]
    compose --> redis[Redis Container]
    compose --> postgres[PostgreSQL Container]
    compose --> nginx[Nginx Container ???]
    nginx -->|80/443| browser[Browser Client]
```

---

## 6. Development Status

### ✅ Implemented

- Basic FastAPI application structure
- SQLModel database models
- CRUD operations for clients, items, orders
- Streamlit frontend for testing
- Basic API endpoints

### ❌ Not Yet Implemented

- User authentication and authorization
- WebSocket real-time updates
- Background job processing
- Stock management
- Payment processing
- Recipe components
- Audit logging
- Production deployment setup

---

**Next Steps:**
1. Implement user authentication system
2. Add stock management models
3. Create payment processing system
4. Replace Streamlit with web-based UI
5. Add WebSocket support for real-time updates
