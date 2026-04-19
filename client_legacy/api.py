import os
import requests

_BASE = os.getenv("API_URL", "http://localhost:8000").rstrip("/") + "/api/v1"
_token: str | None = None
_auth_expired: bool = False


def set_token(token: str | None) -> None:
    global _token
    _token = token


def is_auth_expired() -> bool:
    return _auth_expired


def clear_auth_expired() -> None:
    global _auth_expired
    _auth_expired = False


def _req(method, path, **kwargs):
    global _auth_expired
    headers = kwargs.pop("headers", {})
    if _token:
        headers["Authorization"] = f"Bearer {_token}"
    try:
        r = requests.request(method, f"{_BASE}{path}", timeout=5, headers=headers, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the server. Is the backend running?"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401 and path != "/auth/login":
            _auth_expired = True
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


# ── Auth ───────────────────────────────────────────────────────────────────────

def login(username, password):
    return _req("POST", "/auth/login", json={"username": username, "password": password})


# ── Roles ──────────────────────────────────────────────────────────────────────

def get_roles():
    return _req("GET", "/roles/")

def create_role(name, description, permissions):
    return _req("POST", "/roles/", json={
        "name": name, "description": description or None, "permissions": permissions
    })

def update_role(rid, **kw):
    return _req("PATCH", f"/roles/{rid}", json=kw)

def delete_role(rid):
    return _req("DELETE", f"/roles/{rid}")


# ── Tables ─────────────────────────────────────────────────────────────────────

def get_tables(status=None, date=None):
    params = {}
    if status:
        params["status"] = status
    if date:
        params["date"] = date
    return _req("GET", "/tables/", params=params or None)

def create_table(name):
    return _req("POST", "/tables/", json={"table_name": name})

def get_table(tid):
    return _req("GET", f"/tables/{tid}")

def update_table(tid, name):
    return _req("PATCH", f"/tables/{tid}", json={"table_name": name})

def close_table(tid):
    return _req("POST", f"/tables/{tid}/close")

def delete_table(tid):
    return _req("DELETE", f"/tables/{tid}")


# ── Orders ─────────────────────────────────────────────────────────────────────

def add_order(tid, item_id, quantity):
    return _req("POST", f"/tables/{tid}/orders/", json={"item_id": item_id, "quantity": quantity})

def update_order(tid, oid, quantity):
    return _req("PATCH", f"/tables/{tid}/orders/{oid}", json={"quantity": quantity})

def delete_order(tid, oid):
    return _req("DELETE", f"/tables/{tid}/orders/{oid}")


# ── Items ──────────────────────────────────────────────────────────────────────

def get_items(name=None, category=None, available_only=False):
    params = {}
    if name:
        params["name"] = name
    if category:
        params["category"] = category
    if available_only:
        params["available_only"] = "true"
    return _req("GET", "/items/", params=params or None)

def get_item(iid):
    return _req("GET", f"/items/{iid}")

def create_item(name, price, category, is_available, stock_qty=None):
    body = {"name": name, "price": price, "category": category or None, "is_available": is_available}
    if stock_qty is not None:
        body["stock_qty"] = stock_qty
    return _req("POST", "/items/", json=body)

def update_item(iid, **kw):
    return _req("PUT", f"/items/{iid}", json=kw)

def delete_item(iid):
    return _req("DELETE", f"/items/{iid}")

def update_stock(iid, delta):
    return _req("PATCH", f"/items/{iid}/stock", json={"delta": delta})


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_receipt(tid) -> tuple[bytes | None, str | None]:
    headers = {}
    if _token:
        headers["Authorization"] = f"Bearer {_token}"
    try:
        r = requests.get(f"{_BASE}/tables/{tid}/receipt", timeout=10, headers=headers)
        r.raise_for_status()
        return r.content, None
    except requests.HTTPError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)


def get_daily_stats(date_str=None):
    params = {"date": date_str} if date_str else None
    return _req("GET", "/stats/daily", params=params)


# ── Users ──────────────────────────────────────────────────────────────────────

def get_users():
    return _req("GET", "/users/")

def create_user(name, username, password, role_id):
    return _req("POST", "/users/", json={
        "name": name, "username": username, "password": password, "role_id": role_id
    })

def update_user(uid, **kw):
    return _req("PUT", f"/users/{uid}", json=kw)

def delete_user(uid):
    return _req("DELETE", f"/users/{uid}")
