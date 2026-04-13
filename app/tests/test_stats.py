from datetime import date

BASE = "/api/v1"
TODAY = date.today().isoformat()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _item(client, name="Beer", price=5.0, category="drink"):
    return client.post(f"{BASE}/items/", json={"name": name, "price": price, "category": category}).json()["id"]

def _table(client, name="T1"):
    return client.post(f"{BASE}/tables/", json={"table_name": name}).json()["id"]

def _order(client, table_id, item_id, qty=1.0):
    return client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": qty}).json()


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestDailyStatsEmpty:
    def test_empty_day_returns_zeros(self, client):
        r = client.get(f"{BASE}/stats/daily")
        assert r.status_code == 200
        d = r.json()
        assert d["date"] == TODAY
        assert d["revenue_total"] == 0.0
        assert d["revenue_locked"] == 0.0
        assert d["revenue_running"] == 0.0
        assert d["orders_count"] == 0
        assert d["tables_served"] == 0
        assert d["items_sold"] == []
        assert d["orders_log"] == []

    def test_past_date_with_no_data_returns_zeros(self, client):
        r = client.get(f"{BASE}/stats/daily?date=2000-01-01")
        assert r.status_code == 200
        d = r.json()
        assert d["date"] == "2000-01-01"
        assert d["revenue_total"] == 0.0
        assert d["orders_count"] == 0

    def test_invalid_date_returns_400(self, client):
        r = client.get(f"{BASE}/stats/daily?date=not-a-date")
        assert r.status_code == 400


class TestDailyStatsRevenue:
    def test_single_order_revenue(self, client):
        iid = _item(client, "Beer", 5.0)
        tid = _table(client)
        _order(client, tid, iid, qty=2.0)

        d = client.get(f"{BASE}/stats/daily").json()
        assert d["revenue_total"] == 10.0
        assert d["orders_count"] == 1
        assert d["tables_served"] == 1

    def test_multiple_orders_same_table(self, client):
        iid = _item(client, "Beer", 5.0)
        tid = _table(client)
        _order(client, tid, iid, qty=2.0)
        _order(client, tid, iid, qty=3.0)

        d = client.get(f"{BASE}/stats/daily").json()
        assert d["revenue_total"] == 25.0
        assert d["orders_count"] == 2
        assert d["tables_served"] == 1  # still one table

    def test_orders_across_multiple_tables(self, client):
        iid = _item(client, "Beer", 10.0)
        t1 = _table(client, "T1")
        t2 = _table(client, "T2")
        _order(client, t1, iid, qty=1.0)
        _order(client, t2, iid, qty=1.0)

        d = client.get(f"{BASE}/stats/daily").json()
        assert d["revenue_total"] == 20.0
        assert d["tables_served"] == 2

    def test_revenue_locked_vs_running(self, client):
        iid = _item(client, "Wine", 8.0)

        t1 = _table(client, "Closed Table")
        _order(client, t1, iid, qty=2.0)           # 16.0
        client.post(f"{BASE}/tables/{t1}/close")

        t2 = _table(client, "Active Table")
        _order(client, t2, iid, qty=1.0)           # 8.0

        d = client.get(f"{BASE}/stats/daily").json()
        assert d["revenue_total"] == 24.0
        assert d["revenue_locked"] == 16.0
        assert d["revenue_running"] == 8.0

    def test_revenue_all_locked_when_all_tables_closed(self, client):
        iid = _item(client, "Beer", 5.0)
        tid = _table(client)
        _order(client, tid, iid, qty=3.0)
        client.post(f"{BASE}/tables/{tid}/close")

        d = client.get(f"{BASE}/stats/daily").json()
        assert d["revenue_locked"] == 15.0
        assert d["revenue_running"] == 0.0


class TestDailyStatsItemBreakdown:
    def test_single_item_aggregated(self, client):
        iid = _item(client, "Beer", 5.0)
        tid = _table(client)
        _order(client, tid, iid, qty=2.0)
        _order(client, tid, iid, qty=1.0)

        d = client.get(f"{BASE}/stats/daily").json()
        assert len(d["items_sold"]) == 1
        row = d["items_sold"][0]
        assert row["item_name"] == "Beer"
        assert row["quantity"] == 3.0
        assert row["revenue"] == 15.0

    def test_multiple_items_sorted_by_revenue_desc(self, client):
        beer = _item(client, "Beer", 5.0)
        wine = _item(client, "Wine", 10.0)
        tid = _table(client)
        _order(client, tid, beer, qty=1.0)   # 5.0
        _order(client, tid, wine, qty=3.0)   # 30.0

        d = client.get(f"{BASE}/stats/daily").json()
        assert len(d["items_sold"]) == 2
        assert d["items_sold"][0]["item_name"] == "Wine"   # higher revenue first
        assert d["items_sold"][1]["item_name"] == "Beer"

    def test_item_qty_aggregated_across_tables(self, client):
        iid = _item(client, "Beer", 5.0)
        t1 = _table(client, "T1")
        t2 = _table(client, "T2")
        _order(client, t1, iid, qty=2.0)
        _order(client, t2, iid, qty=3.0)

        d = client.get(f"{BASE}/stats/daily").json()
        assert len(d["items_sold"]) == 1
        assert d["items_sold"][0]["quantity"] == 5.0
        assert d["items_sold"][0]["revenue"] == 25.0


class TestDailyStatsOrdersLog:
    def test_log_contains_correct_fields(self, client):
        iid = _item(client, "Nachos", 6.0)
        tid = _table(client, "Bar Tab")
        _order(client, tid, iid, qty=2.0)

        d = client.get(f"{BASE}/stats/daily").json()
        assert len(d["orders_log"]) == 1
        entry = d["orders_log"][0]
        assert entry["item_name"] == "Nachos"
        assert entry["table_name"] == "Bar Tab"
        assert entry["quantity"] == 2.0
        assert entry["price"] == 6.0
        assert entry["line_total"] == 12.0
        assert "created_at" in entry
        assert "order_id" in entry

    def test_log_sorted_by_time(self, client):
        iid = _item(client, "Beer", 5.0)
        tid = _table(client)
        o1 = _order(client, tid, iid, qty=1.0)
        o2 = _order(client, tid, iid, qty=2.0)

        d = client.get(f"{BASE}/stats/daily").json()
        log = d["orders_log"]
        assert len(log) == 2
        # Chronological order — first order's id should appear before second
        ids = [e["order_id"] for e in log]
        assert ids.index(o1["id"]) < ids.index(o2["id"])

    def test_log_count_matches_orders_count(self, client):
        iid = _item(client, "Beer", 5.0)
        tid = _table(client)
        for qty in [1.0, 2.0, 1.5]:
            _order(client, tid, iid, qty=qty)

        d = client.get(f"{BASE}/stats/daily").json()
        assert d["orders_count"] == len(d["orders_log"]) == 3
