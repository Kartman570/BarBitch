# BarPOS Security Audit

**Date:** 2026-04-19  
**Scope:** Backend API (`app/`) — FastAPI + SQLModel + PostgreSQL  
**Method:** Black-box curl simulation + source-code review  
**Tester:** Internal (Claude Code)

---

## Executive Summary

Аудит выявил **3 критические**, **7 высоких** и **7 средних** уязвимостей.  
Система в текущем виде не готова к деплою даже во внутреннюю сеть: JWT-секрет известен публично, RBAC не работает от слова совсем, база данных открыта без пароля. Любой сотрудник с токеном может стать администратором за один запрос.

**Статус исправлений:**

| Sprint | Статус | Дата |
|--------|--------|------|
| Sprint 1 — Critical (SECRET_KEY, RBAC, default creds, PG auth) | ✅ Исправлено и проверено | 2026-04-19 |
| Sprint 2 — High (input validation, rate limit, mass assignment) | ✅ Исправлено и проверено | 2026-04-19 |
| Sprint 3 — Medium (security headers, CORS, OpenAPI, dep pins) | ✅ Исправлено и проверено | 2026-04-19 |
| Sprint 4 — Additional (audit log, self-delete, refresh tokens, password policy) | ✅ Исправлено и проверено | 2026-04-19 |

---

## Attack Surface — карта эндпоинтов

| Метод | Путь | Auth | Риски |
|-------|------|------|-------|
| POST | `/api/v1/auth/login` | ❌ | Брутфорс, нет rate limit |
| GET/POST | `/api/v1/roles/` | JWT | RBAC не проверяется |
| GET/PATCH/DELETE | `/api/v1/roles/{id}` | JWT | RBAC не проверяется |
| POST/GET | `/api/v1/users/` | JWT | RBAC, IDOR, priv. escalation |
| GET/PUT/DELETE | `/api/v1/users/{id}` | JWT | IDOR — любой удаляет любого |
| POST/GET | `/api/v1/items/` | JWT | Negative prices, mass assign |
| GET/PUT/DELETE | `/api/v1/items/{id}` | JWT | Mass assignment stock_qty |
| PATCH | `/api/v1/items/{id}/stock` | JWT | RBAC не проверяется |
| POST/GET | `/api/v1/tables/` | JWT | Negative qty orders |
| GET/PATCH/DELETE | `/api/v1/tables/{id}` | JWT | — |
| POST | `/api/v1/tables/{id}/close` | JWT | Revenue manipulation |
| POST/GET | `/api/v1/tables/{id}/orders/` | JWT | Negative qty, revenue hack |
| GET/PATCH/DELETE | `/api/v1/tables/{id}/orders/{id}` | JWT | — |
| GET | `/api/v1/stats/daily` | JWT | RBAC не проверяется |
| GET | `/openapi.json` | ❌ | Полная карта API без auth |
| GET | `/docs` | ❌ | Swagger UI без auth |

---

## Уязвимости

### 🔴 CRITICAL-01 — Hardcoded JWT Secret Key
**OWASP:** A02 Cryptographic Failures  
**Файл:** `app/core/config.py:11`

```python
secret_key: str = "change-me-in-production"
```

**Доказательство эксплуатации:**
```bash
# Брутфорс секрета за < 1мс — секрет совпал с дефолтом
python3 -c "
import hmac, hashlib, base64
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
sig = base64.urlsafe_b64decode(token.split('.')[2] + '==')
secret = 'change-me-in-production'
computed = hmac.new(secret.encode(), ..., hashlib.sha256).digest()
# => MATCH
"

# Подделка токена для ЛЮБОГО user_id без знания пароля
from jose import jwt
token = jwt.encode({'sub': '1', 'exp': ...}, 'change-me-in-production', algorithm='HS256')
# Токен принят API — получаем полный доступ от имени любого пользователя
```

**Воздействие:** Полный захват системы. Атакующий генерирует валидный токен для любого user_id без знания пароля.

**Исправление:**
```bash
# .env
SECRET_KEY=<сгенерировать: openssl rand -hex 32>
```
```python
# config.py
secret_key: str  # убрать default, требовать из ENV
```

---

### 🔴 CRITICAL-02 — RBAC не реализован (полное отсутствие)
**OWASP:** A01 Broken Access Control  
**Файл:** `app/api/routes_v1.py` — все роуты

`CurrentUserDep` проверяет только валидность JWT. Поля `permissions` у пользователя никогда не проверяются ни на одном роуте.

**Доказательство эксплуатации:**
```bash
# Alice — barman, permission: ["tables"] only
# Ожидаемо: нет доступа к /users/, /roles/, /items/, /stats/

# Реальность:
curl -X GET  /api/v1/users/      -H "Authorization: Bearer $BARMAN_TOKEN"
# => 200, список всех пользователей

curl -X DELETE /api/v1/users/5   -H "Authorization: Bearer $BARMAN_TOKEN"
# => {"message": "User deleted"}   ← удалил admin-аккаунт

curl -X POST /api/v1/roles/ -d '{"name":"hacker","permissions":["roles","users","items","stock","stats","tables"]}'
# => {"id": 6, "name": "hacker", ...}  ← создал роль с полными правами

curl -X PUT /api/v1/users/1 -d '{"role_id": 4}'   # 4 = admin role
# => {"role_name": "admin", ...}   ← повысил себя до admin
```

**Воздействие:** Бармен, повар — любой сотрудник с токеном имеет полные административные права. Система ролей декоративная.

**Исправление:** Добавить dependency для проверки прав на каждый роут:
```python
def require_permission(perm: str):
    def checker(user: CurrentUserDep, session: SessionDep):
        role = session.get(Role, user.role_id)
        perms = decode_permissions(role.permissions) if role else []
        if perm not in perms:
            raise HTTPException(403, f"Permission '{perm}' required")
        return user
    return Depends(checker)

# Применение:
@router.get("/users/")
def list_users(..., _: Annotated[User, require_permission("users")]):
    ...
```

---

### 🔴 CRITICAL-03 — Default Credentials
**OWASP:** A07 Identification and Authentication Failures  
**Файл:** `app/cli.py` (команда `seed-all`)

```bash
curl -X POST /api/v1/auth/login -d '{"username":"admin","password":"admin"}'
# => {"access_token": "eyJ...", "role_name": "admin", "permissions": [...all...]}
```

Дефолтные credentials `admin/admin` жёстко зашиты в CLI и документированы в CLAUDE.md. При деплое на любой сервер учётная запись немедленно компрометируема.

**Исправление:** `seed-all` должен принимать пароль как аргумент и требовать его явного указания (без default). Добавить предупреждение при старте если пароль admin не сменён.

---

### 🟠 HIGH-01 — No Rate Limiting on Login
**OWASP:** A07 Identification and Authentication Failures

```bash
# 20 запросов за ~200мс — все обработаны, никакого throttling
401 401 401 401 401 401 401 401 401 401 401 401 401 401 401 401 401 401 401 401
```

При стандартном словарном атаке (rockyou.txt, ~14M паролей) — несколько часов до подбора слабого пароля. Нет блокировки аккаунта, нет CAPTCHA, нет задержки.

**Исправление:**
```python
# Вариант: slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/login")
@limiter.limit("5/minute")
def login(request: Request, data: LoginRequest, session: SessionDep):
    ...
```

---

### 🟠 HIGH-02 — Business Logic: Negative Prices & Quantities
**OWASP:** A04 Insecure Design

Pydantic-схемы не валидируют диапазоны числовых полей.

```bash
# Товар с отрицательной ценой — принят без ошибки
curl -X POST /api/v1/items/ -d '{"name":"FreeItem","price":-100.0}'
# => {"id":6, "price":-100.0}

# Заказ с отрицательным количеством — принят
curl -X POST /api/v1/tables/10/orders/ -d '{"item_id":8,"quantity":-3}'
# => {"id":19, "quantity":-3.0}

# Начальный stock отрицательный — принят
curl -X POST /api/v1/items/ -d '{"name":"Ghost","price":5.0,"stock_qty":-50}'
# => {"stock_qty":-50.0}
```

**Исправление:**
```python
from pydantic import field_validator, Field

class ItemCreate(BaseModel):
    price: float = Field(gt=0)          # строго больше нуля
    stock_qty: Optional[float] = Field(default=None, ge=0)

class OrderCreate(BaseModel):
    quantity: float = Field(default=1.0, gt=0)

class StockAdjust(BaseModel):
    delta: float  # delta может быть отрицательной — это ок, проверяется в route
```

---

### 🟠 HIGH-03 — Revenue Manipulation via Negative Orders
**OWASP:** A04 Insecure Design

Следствие HIGH-02. Атака позволяет занизить итог стола.

```bash
# Пиво стоит 100₽. Честных заказов на 500₽.
# Добавляем отрицательный "возврат" -4 пива:
curl -X POST /api/v1/tables/11/orders/ -d '{"item_id":X,"quantity":-4}'

# Закрываем стол:
curl -X POST /api/v1/tables/11/close
# => {"total": 100.0}   ← вместо 500₽
```

Бармен может занизить выручку стола в 5 раз перед закрытием. Финансовый ущерб прямой.

---

### 🟠 HIGH-04 — Mass Assignment: stock_qty через PUT /items/
**OWASP:** A04 Insecure Design

`PUT /items/{id}` принимает `ItemUpdate` который включает `stock_qty`. Это позволяет:
1. Установить любое значение stock_qty в обход PATCH /stock
2. Включить stock-tracking для товара, у которого его не было
3. Обнулить stock у конкурентного товара

```bash
# Товар создан без отслеживания остатков (stock_qty=None)
curl -X PUT /api/v1/items/13 -d '{"stock_qty": 999999}'
# => {"stock_qty": 999999.0}  ← bypass stock audit trail
```

---

### 🟠 HIGH-05 — PostgreSQL TRUST Authentication
**Файл:** `docker-compose.yml:28`

```yaml
POSTGRES_HOST_AUTH_METHOD: trust
```

База данных принимает любое подключение из контейнерной сети без пароля.

```bash
# Прямой доступ к данным без каких-либо credentials:
docker compose exec db psql -U postgres -c "SELECT username, password_hash FROM users;"
#  username |                        password_hash
# ----------+--------------------------------------------------------------
#  admin    | $2b$12$...
#  Alice    | $2b$12$...
```

Любой процесс в docker-сети читает/пишет в БД напрямую.

**Исправление:**
```yaml
# docker-compose.yml
POSTGRES_PASSWORD: <strong_password>
POSTGRES_HOST_AUTH_METHOD: scram-sha-256  # или убрать и добавить password
```

---

### 🟠 HIGH-06 — IDOR: любой пользователь удаляет любого
**OWASP:** A01 Broken Access Control

Нет проверки "кто удаляет кого". Бармен удаляет admin-аккаунт:

```bash
curl -X DELETE /api/v1/users/5 -H "Authorization: Bearer $BARMAN_TOKEN"
# => {"message": "User deleted"}

curl -X GET /api/v1/users/5 -H "Authorization: Bearer $BARMAN_TOKEN"
# => {"detail": "User not found"}
```

Полный захват: удаляем всех кроме себя → единственный пользователь системы.

---

### 🟠 HIGH-07 — Privilege Escalation
**OWASP:** A01 Broken Access Control

Прямое следствие CRITICAL-02. Любой пользователь меняет свою роль на admin:

```bash
# Barman (Alice, id=1) узнаёт ID admin-роли через GET /roles/
# Присваивает себе:
curl -X PUT /api/v1/users/1 -d '{"role_id": 4}' -H "Authorization: Bearer $BARMAN_TOKEN"
# => {"role_name": "admin", "permissions": ["items","roles","stats","stock","tables","users"]}
```

---

### 🟡 MEDIUM-01 — Нет Security Headers
**OWASP:** A05 Security Misconfiguration

```bash
curl -I http://localhost:8000/
# server: uvicorn
# (никаких security headers)
```

Отсутствуют: `X-Frame-Options`, `X-Content-Type-Options`, `Strict-Transport-Security`, `Content-Security-Policy`, `Referrer-Policy`, `Permissions-Policy`.

**Исправление:**
```python
# main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)
```

---

### 🟡 MEDIUM-02 — CORS полностью открыт (или отсутствует)
**OWASP:** A05 Security Misconfiguration

FastAPI без `CORSMiddleware` не добавляет `Access-Control-Allow-Origin` — браузер блокирует запросы, но это не защита для curl/Postman/скриптов. При добавлении CORS нужно явно указать `allow_origins`.

**Исправление:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # только Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 🟡 MEDIUM-03 — Pydantic validation errors раскрывают внутреннюю структуру
**OWASP:** A09 Security Logging and Monitoring Failures

```bash
curl -X POST /api/v1/auth/login -d '{"username":{"$ne":""},"password":"x"}'
# {
#   "detail": [{
#     "type": "string_type",
#     "loc": ["body", "username"],    ← имена полей схемы
#     "msg": "Input should be a valid string",
#     "input": {"$ne": ""}           ← отражает входные данные
#   }]
# }
```

Раскрывает внутренние имена полей Pydantic-схем и отражает пользовательский ввод — потенциальный вектор для XSS/log injection если ответ рендерится во frontend.

**Исправление:** Перехватить `RequestValidationError` и возвращать обобщённое сообщение:
```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": "Invalid request data"})
```

---

### 🟡 MEDIUM-04 — Server header раскрывает стек
```
server: uvicorn
```
Раскрывает тип сервера. В связке с OpenAPI — атакующий знает точный стек.

**Исправление:** Убрать через middleware или `--header-size` конфиг uvicorn. Либо кастомный middleware переписывает `server` header.

---

### 🟡 MEDIUM-05 — OpenAPI/Swagger открыт без аутентификации
Полная схема API доступна без токена:

```bash
curl http://localhost:8000/openapi.json   # 200 OK, полная схема
curl http://localhost:8000/docs           # 200 OK, Swagger UI
```

**Исправление:**
```python
# main.py — отключить в продакшне через env
app = FastAPI(
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)
```

---

### 🟡 MEDIUM-06 — Uvicorn `--reload` в docker-compose
**Файл:** `docker-compose.yml:16`

```yaml
command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

`--reload` — режим разработки. Воздействие: повышенное потребление ресурсов, файловый watcher может быть использован для hot-code-injection если volume смонтирован из ненадёжного источника.

---

### 🟡 MEDIUM-07 — Unpinned Dependencies
**Файл:** `requirements.txt`

```
fastapi
uvicorn
sqlmodel
bcrypt
python-jose[cryptography]
# ... все без версий
```

Без пинов `pip install` при следующем билде может поставить версию с регрессией безопасности.

**Известные CVE в используемых библиотеках:**

| Библиотека | Версия | CVE | Описание |
|---|---|---|---|
| python-jose | 3.5.0 | CVE-2024-33664 | Memory exhaustion via malformed JWE compact objects |
| python-jose | 3.5.0 | CVE-2024-33663 | Algorithm confusion с ECDSA ключами (не применимо для HS256) |

**Исправление:** Сгенерировать `requirements.txt` с пинами:
```bash
pip freeze > requirements.txt
```
Рассмотреть переход с `python-jose` (unmaintained) на `PyJWT`:
```bash
pip install PyJWT>=2.8.0
```

---

## Отсутствующие механизмы защиты

| Механизм | Статус | Приоритет |
|---|---|---|
| RBAC enforcement | ✅ Реализовано (Sprint 1) | P0 |
| Rate limiting (login) | ✅ Реализовано 10/min (Sprint 2) | P1 |
| Input validation (числа) | ✅ Реализовано (Sprint 2) | P1 |
| Account lockout | ❌ Отсутствует | P1 |
| Token revocation / blacklist | ❌ Отсутствует | P2 |
| Audit log (кто что сделал) | ❌ Отсутствует | P2 |
| Security headers | ❌ Отсутствует | P2 |
| CORS policy | ❌ Отсутствует | P2 |
| HTTPS enforcement | ❌ Отсутствует | P2 |
| Pinned dependencies | ❌ Отсутствует | P2 |
| Защита от самоудаления | ❌ Отсутствует | P3 |
| Password complexity policy | ❌ Отсутствует | P3 |

---

## OWASP Top 10 — сводка

| # | Категория | Статус |
|---|---|---|
| A01 | Broken Access Control | 🟡 Частично (RBAC исправлен ✅, IDOR остаётся) |
| A02 | Cryptographic Failures | ✅ Исправлено (SECRET_KEY из ENV) |
| A03 | Injection | 🟢 Защищено (ORM параметризация) |
| A04 | Insecure Design | ✅ Исправлено (валидация + mass assign fix) |
| A05 | Security Misconfiguration | ✅ Исправлено (headers ✅, CORS ✅, OpenAPI gate ✅, --reload задокументирован) |
| A06 | Vulnerable Components | ✅ Исправлено (PyJWT 2.9.0 вместо python-jose, deps pinned) |
| A07 | Auth Failures | 🟡 Частично (default creds исправлены ✅, rate limit ✅, account lockout нет) |
| A08 | Software Integrity | 🟡 Средний (unpinned deps) |
| A09 | Logging & Monitoring | 🟠 Высокий (нет аудит-лога) |
| A10 | SSRF | 🟢 Н/П |

---

## Что устояло

- **SQL Injection** — SQLAlchemy ORM с bind-параметрами блокирует все попытки инъекций в `ilike`-фильтрах
- **JWT alg=none** — `python-jose` правильно отклоняет токены с `alg:none`
- **Password hash** — bcrypt, не возвращается в API-ответах
- **Float precision** — проверка `stock < requested` корректна для float (10.0000000001 > 10.0 отклонён)
- **Token deleted user** — после удаления пользователя его токен немедленно даёт 401

---

## Roadmap исправлений

### ✅ Sprint 1 — Критично (выполнено 2026-04-19)

1. ✅ `SECRET_KEY` из ENV, без дефолта — `app/core/config.py`
2. ✅ RBAC: `_perm(perm)` dependency на всех 27 защищённых роутах — `app/api/routes_v1.py`
3. ✅ Убрать дефолтный пароль из `seed-all`, требовать `--admin-password` — `app/cli.py`
4. ✅ PostgreSQL TRUST убран, добавлен `POSTGRES_PASSWORD` — `docker-compose.yml`

**Ручная проверка Sprint 1** (curl против live backend):

```bash
# CRITICAL-01 исправлено: SECRET_KEY больше не hardcoded
# config.py отклоняет запуск без SECRET_KEY в ENV

# CRITICAL-02 исправлено: RBAC проверяется на каждом роуте
curl -X GET /api/v1/users/ -H "Authorization: Bearer $BARMAN_TOKEN"
# => 403 {"detail": "Permission 'users' required"}

curl -X POST /api/v1/roles/ -d '{"name":"hacker","permissions":["roles"]}' \
  -H "Authorization: Bearer $BARMAN_TOKEN"
# => 403 {"detail": "Permission 'roles' required"}

# CRITICAL-03 исправлено: admin/admin больше не работает
curl -X POST /api/v1/auth/login -d '{"username":"admin","password":"admin"}'
# => 401 {"detail": "Invalid credentials"}

# HIGH-05 исправлено: TRUST убран
docker compose exec db psql -U postgres -c "SELECT 1;"
# => psql: error: connection to server failed: FATAL: password authentication required
```

---

### ✅ Sprint 2 — Высокий приоритет (выполнено 2026-04-19)

5. ✅ Валидация числовых полей: `price: Field(gt=0)`, `stock_qty: Field(ge=0)`, `quantity: Field(gt=0)` — `app/schemas/schemas_order.py`
6. ✅ Rate limiting 10/minute на `/auth/login` (slowapi) — `app/api/routes_v1.py`, `app/core/limiter.py`
7. ✅ `stock_qty` удалён из `ItemUpdate` — `app/schemas/schemas_order.py`

**Ручная проверка Sprint 2** (curl против live backend, 2026-04-19):

```
# ── Валидация ItemCreate ──────────────────────────────────────────────────────
POST /api/v1/items/  {"name":"Beer","price":0}        → 422  ✅ (price=0 отклонён)
POST /api/v1/items/  {"name":"Beer","price":-5}        → 422  ✅ (price<0 отклонён)
POST /api/v1/items/  {"name":"Beer","price":5,"stock_qty":-1} → 422  ✅ (stock_qty<0)
POST /api/v1/items/  {"name":"Beer","price":5,"stock_qty":0}  → 200  ✅ (stock_qty=0 допустим)

# ── Масс-приswignment stock_qty через PUT ─────────────────────────────────────
# Товар создан с stock_qty=10. PUT отправляет stock_qty=999:
PUT /api/v1/items/5  {"name":"Updated","stock_qty":999}
→ 200, stock_qty=10.0  ✅ (поле проигнорировано — не в схеме ItemUpdate)

PUT /api/v1/items/5  {"price":0}  → 422  ✅ (price=0 в UPDATE тоже отклонён)

# ── Валидация OrderCreate ──────────────────────────────────────────────────────
POST /api/v1/tables/1/orders/  {"item_id":6,"quantity":0}   → 422  ✅
POST /api/v1/tables/1/orders/  {"item_id":6,"quantity":-1}  → 422  ✅
POST /api/v1/tables/1/orders/  {"item_id":6,"quantity":3}   → 200  ✅ (id=1)

# ── Валидация OrderUpdate ──────────────────────────────────────────────────────
PATCH /api/v1/tables/1/orders/1  {"quantity":0}   → 422  ✅
PATCH /api/v1/tables/1/orders/1  {"quantity":-2}  → 422  ✅

# ── Rate limiting (10/minute) ──────────────────────────────────────────────────
# 11 последовательных POST /auth/login с неверными credentials:
запрос 1-10: 401  ✅ (неверный пароль, но обработан)
запрос 11:   429  ✅ (Too Many Requests — rate limit сработал)
```

---

### ✅ Sprint 3 — Средний приоритет (выполнено 2026-04-19)

8. ✅ Security headers middleware — `app/main.py` (`SecurityHeadersMiddleware`)
9. ✅ CORS restrictive policy — разрешён только `http://localhost:8501` (Streamlit)
10. ✅ `/docs` и `/openapi.json` скрыты при `DEBUG=false` — `app/main.py`, `app/core/config.py`
11. ✅ Пиннинг зависимостей + миграция с `python-jose` на `PyJWT==2.9.0` — `requirements.txt`
12. ⚠️ `--reload` оставлен намеренно для удобства разработки. Удалить перед production-деплоем (`docker-compose.yml:16`, задокументировано в `CLAUDE.md`).

**Ручная проверка Sprint 3** (curl против live backend, 2026-04-19):

```
# ── Security headers ──────────────────────────────────────────────────────────
GET /  → заголовки в ответе:
  x-frame-options: DENY                              ✅
  x-content-type-options: nosniff                   ✅
  x-xss-protection: 1; mode=block                   ✅
  referrer-policy: strict-origin-when-cross-origin  ✅
  permissions-policy: geolocation=(), camera=(), microphone=()  ✅

# ── CORS ──────────────────────────────────────────────────────────────────────
OPTIONS /api/v1/auth/login  Origin: http://localhost:8501  (разрешённый фронтенд)
→ access-control-allow-origin: http://localhost:8501   ✅

OPTIONS /api/v1/auth/login  Origin: http://evil.com
→ access-control-allow-origin: (заголовок отсутствует)  ✅  браузер заблокирует запрос

# ── OpenAPI в dev-режиме (DEBUG=true, default) ──────────────────────────────
GET /docs        → 200  ✅
GET /openapi.json → 200  ✅

# ── OpenAPI в prod-режиме (DEBUG=false) ─────────────────────────────────────
python -c "os.environ['DEBUG']='false'; from main import app; print(app.docs_url)"
→ docs_url = None, openapi_url = None  ✅

# ── PyJWT вместо python-jose ─────────────────────────────────────────────────
pip show PyJWT     → Version: 2.9.0   ✅
pip show python-jose → WARNING: Package(s) not found  ✅  (удалён)
```

### ✅ Sprint 4 — Дополнительно (выполнено 2026-04-19)

13. ✅ Audit log — таблица `audit_events`, эндпоинт `GET /audit/events` — `app/models/models.py`, `app/api/routes_v1.py`
14. ✅ Защита от самоудаления — `DELETE /users/{id}` возвращает 400 если `user_id == current_user.id`
15. ✅ Refresh tokens + revocation — таблица `refresh_tokens`, эндпоинты `POST /auth/refresh` и `POST /auth/logout`
16. ✅ Password complexity — минимум 8 символов + хотя бы одна цифра или спецсимвол (Pydantic validator в `UserCreate` и `UserUpdate`)

**Ручная проверка Sprint 4** (curl против live backend, 2026-04-19):

```
# ── Password complexity ───────────────────────────────────────────────────────
POST /users/  {"password": "abc"}         → 422  ✅ (меньше 8 символов)
POST /users/  {"password": "abcdefgh"}    → 422  ✅ (нет цифры/спецсимвола)
POST /users/  {"password": "abcdefg1"}   → 200  ✅ (≥8 символов + цифра)

# ── Self-delete protection ────────────────────────────────────────────────────
DELETE /users/1  (от имени admin, id=1)
→ 400 {"detail": "Cannot delete your own account"}  ✅

# ── Refresh tokens ────────────────────────────────────────────────────────────
POST /auth/login  → возвращает access_token + refresh_token  ✅

POST /auth/refresh  {"refresh_token": "<valid>"}
→ 200 {"access_token": "eyJ..."}  ✅

POST /auth/logout  {"refresh_token": "<valid>"}  → 200  ✅

POST /auth/refresh  {"refresh_token": "<revoked>"}  → 401  ✅ (отозван)

POST /auth/refresh  {"refresh_token": "notarealtoken"}  → 401  ✅ (не существует)

# ── Audit log ────────────────────────────────────────────────────────────────
GET /audit/events?action=login_success  → [{username: "admin", ip: "192.168.65.1", ...}]  ✅
GET /audit/events?action=login_failure  → записи о неудачных попытках  ✅
GET /audit/events?limit=2              → ровно 2 записи  ✅
GET /audit/events  (barman)            → 403  ✅ (требует "roles" permission)
```
