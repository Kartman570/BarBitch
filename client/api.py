import os
import requests

_BASE = os.getenv("API_URL", "http://localhost:8000").rstrip("/") + "/api/v1"


def _req(method, path, **kwargs):
    try:
        r = requests.request(method, f"{_BASE}{path}", timeout=5, **kwargs)
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the server. Is the backend running?"
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        return None, detail
    except Exception as e:
        return None, str(e)


# ── Tables ─────────────────────────────────────────────────────────────────────

def get_tables(status=None):
    params = {"status": status} if status else None
    return _req("GET", "/tables/", params=params)

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

def create_item(name, price, category, is_available):
    return _req("POST", "/items/", json={
        "name": name, "price": price,
        "category": category or None, "is_available": is_available,
    })

def update_item(iid, **kw):
    return _req("PUT", f"/items/{iid}", json=kw)

def delete_item(iid):
    return _req("DELETE", f"/items/{iid}")

def update_stock(iid, delta):
    return _req("PATCH", f"/items/{iid}/stock", json={"delta": delta})


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_daily_stats(date_str=None):
    params = {"date": date_str} if date_str else None
    return _req("GET", "/stats/daily", params=params)


# ── Users ──────────────────────────────────────────────────────────────────────

def get_users():
    return _req("GET", "/users/")

def create_user(name, role):
    return _req("POST", "/users/", json={"name": name, "role": role})

def update_user(uid, **kw):
    return _req("PUT", f"/users/{uid}", json=kw)

def delete_user(uid):
    return _req("DELETE", f"/users/{uid}")
