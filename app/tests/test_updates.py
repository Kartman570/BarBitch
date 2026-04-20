"""Tests covering the 11 roadmap tasks implemented in the updates branch."""
import pytest

BASE = "/api/v1"


# ── Task 3: Expanded audit log ─────────────────────────────────────────────────

class TestAuditExpanded:
    def _audit_actions(self, client):
        return [e["action"] for e in client.get(f"{BASE}/audit/events?limit=500").json()]

    def test_table_created_audit(self, client):
        client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        assert "table_created" in self._audit_actions(client)

    def test_table_renamed_audit(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        tid = r.json()["id"]
        client.patch(f"{BASE}/tables/{tid}", json={"table_name": "T1-renamed"})
        assert "table_renamed" in self._audit_actions(client)

    def test_table_closed_audit(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T2"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        iid = r.json()["id"]
        client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 1})
        client.post(f"{BASE}/tables/{tid}/close")
        assert "table_closed" in self._audit_actions(client)

    def test_table_deleted_audit(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T3"})
        tid = r.json()["id"]
        client.delete(f"{BASE}/tables/{tid}")
        assert "table_deleted" in self._audit_actions(client)

    def test_item_created_audit(self, client):
        client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        assert "item_created" in self._audit_actions(client)

    def test_item_updated_audit(self, client):
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        iid = r.json()["id"]
        client.put(f"{BASE}/items/{iid}", json={"price": 6.0})
        assert "item_updated" in self._audit_actions(client)

    def test_item_deleted_audit(self, client):
        r = client.post(f"{BASE}/items/", json={"name": "Wine", "price": 8.0})
        iid = r.json()["id"]
        client.delete(f"{BASE}/items/{iid}")
        assert "item_deleted" in self._audit_actions(client)

    def test_stock_adjusted_audit(self, client):
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0, "stock_qty": 10})
        iid = r.json()["id"]
        client.patch(f"{BASE}/items/{iid}/stock", json={"delta": 5})
        assert "stock_adjusted" in self._audit_actions(client)

    def test_order_added_audit(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T4"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        iid = r.json()["id"]
        client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 1})
        assert "order_added" in self._audit_actions(client)

    def test_order_deleted_audit(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T5"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        iid = r.json()["id"]
        r = client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 1})
        oid = r.json()["id"]
        client.delete(f"{BASE}/tables/{tid}/orders/{oid}")
        assert "order_deleted" in self._audit_actions(client)


# ── Task 6: Pagination ─────────────────────────────────────────────────────────

class TestPagination:
    def test_items_limit(self, client):
        for i in range(5):
            client.post(f"{BASE}/items/", json={"name": f"Item{i}", "price": float(i + 1)})
        r = client.get(f"{BASE}/items/?limit=3&skip=0")
        assert len(r.json()) == 3

    def test_items_skip(self, client):
        for i in range(5):
            client.post(f"{BASE}/items/", json={"name": f"Item{i}", "price": float(i + 1)})
        r_all = client.get(f"{BASE}/items/?limit=1000")
        r_skip = client.get(f"{BASE}/items/?skip=2&limit=1000")
        assert len(r_skip.json()) == len(r_all.json()) - 2

    def test_tables_limit(self, client):
        for i in range(4):
            client.post(f"{BASE}/tables/", json={"table_name": f"Table{i}"})
        r = client.get(f"{BASE}/tables/?limit=2")
        assert len(r.json()) == 2

    def test_tables_skip(self, client):
        for i in range(4):
            client.post(f"{BASE}/tables/", json={"table_name": f"Table{i}"})
        r_all = client.get(f"{BASE}/tables/?limit=500")
        r_skip = client.get(f"{BASE}/tables/?skip=1&limit=500")
        assert len(r_skip.json()) == len(r_all.json()) - 1

    def test_audit_skip(self, client):
        for i in range(3):
            client.post(f"{BASE}/items/", json={"name": f"Item{i}", "price": float(i + 1)})
        r_all = client.get(f"{BASE}/audit/events?limit=500")
        r_skip = client.get(f"{BASE}/audit/events?skip=1&limit=500")
        assert len(r_skip.json()) == len(r_all.json()) - 1


# ── Task 7: Date-range stats ───────────────────────────────────────────────────

class TestDateRangeStats:
    def test_daily_stats_default(self, client):
        r = client.get(f"{BASE}/stats/daily")
        assert r.status_code == 200
        data = r.json()
        assert "date" in data
        assert "revenue_total" in data

    def test_daily_stats_single_date(self, client):
        r = client.get(f"{BASE}/stats/daily?date=2026-04-01")
        assert r.status_code == 200
        assert r.json()["date"] == "2026-04-01"

    def test_daily_stats_range(self, client):
        r = client.get(f"{BASE}/stats/daily?date_from=2026-04-01&date_to=2026-04-07")
        assert r.status_code == 200
        assert r.json()["date"] == "2026-04-01 / 2026-04-07"

    def test_daily_stats_date_from_only(self, client):
        r = client.get(f"{BASE}/stats/daily?date_from=2026-04-05")
        assert r.status_code == 200
        assert r.json()["date"] == "2026-04-05"

    def test_daily_stats_invalid_date(self, client):
        r = client.get(f"{BASE}/stats/daily?date_from=not-a-date")
        assert r.status_code == 400

    def test_range_aggregates_orders(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 10.0})
        iid = r.json()["id"]
        client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 2})

        today = __import__('datetime').date.today().isoformat()
        r = client.get(f"{BASE}/stats/daily?date_from={today}&date_to={today}")
        assert r.status_code == 200
        assert r.json()["orders_count"] == 1
        assert r.json()["revenue_total"] == 20.0


# ── Task 10: Discounts ─────────────────────────────────────────────────────────

class TestDiscount:
    def test_order_with_discount_stored(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 10.0})
        iid = r.json()["id"]

        r = client.post(f"{BASE}/tables/{tid}/orders/", json={
            "item_id": iid, "quantity": 1, "discount": 10.0
        })
        assert r.status_code == 200
        assert r.json()["discount"] == 10.0

    def test_order_default_no_discount(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T2"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 10.0})
        iid = r.json()["id"]

        r = client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 1})
        assert r.status_code == 200
        assert r.json()["discount"] == 0.0

    def test_close_table_applies_discount(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T3"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 10.0})
        iid = r.json()["id"]
        # 10.0 * 1 * (1 - 10/100) = 9.0
        client.post(f"{BASE}/tables/{tid}/orders/", json={
            "item_id": iid, "quantity": 1, "discount": 10.0
        })
        r = client.post(f"{BASE}/tables/{tid}/close")
        assert r.status_code == 200
        assert r.json()["total"] == 9.0

    def test_close_table_no_discount(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T4"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 10.0})
        iid = r.json()["id"]
        client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 2})
        r = client.post(f"{BASE}/tables/{tid}/close")
        assert r.json()["total"] == 20.0

    def test_discount_reflected_in_stats(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T5"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 100.0})
        iid = r.json()["id"]
        # 100 * 1 * 0.5 = 50
        client.post(f"{BASE}/tables/{tid}/orders/", json={
            "item_id": iid, "quantity": 1, "discount": 50.0
        })

        today = __import__('datetime').date.today().isoformat()
        r = client.get(f"{BASE}/stats/daily?date={today}")
        assert r.json()["revenue_total"] == 50.0

    def test_discount_validation_max(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T6"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        iid = r.json()["id"]
        r = client.post(f"{BASE}/tables/{tid}/orders/", json={
            "item_id": iid, "quantity": 1, "discount": 150.0
        })
        assert r.status_code == 422  # discount > 100 rejected by schema

    def test_orders_log_has_discount(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T7"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 10.0})
        iid = r.json()["id"]
        client.post(f"{BASE}/tables/{tid}/orders/", json={
            "item_id": iid, "quantity": 1, "discount": 20.0
        })

        today = __import__('datetime').date.today().isoformat()
        r = client.get(f"{BASE}/stats/daily?date={today}")
        log = r.json()["orders_log"]
        assert len(log) == 1
        assert log[0]["discount"] == 20.0
        assert log[0]["line_total"] == 8.0  # 10 * 1 * 0.8


# ── Task 11: Historical top-items report ───────────────────────────────────────

class TestTopItems:
    def test_top_items_empty(self, client):
        r = client.get(f"{BASE}/stats/top-items?date_from=2020-01-01&date_to=2020-01-31")
        assert r.status_code == 200
        assert r.json() == []

    def test_top_items_returns_data(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        iid = r.json()["id"]
        client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 3})

        r = client.get(f"{BASE}/stats/top-items?date_from=2026-01-01&date_to=2027-01-01")
        assert r.status_code == 200
        assert len(r.json()) >= 1
        top = r.json()[0]
        assert top["item_name"] == "Beer"
        assert top["quantity"] == 3.0
        assert top["revenue"] == 15.0
        assert top["orders_count"] == 1

    def test_top_items_limit(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        tid = r.json()["id"]
        for i in range(5):
            r = client.post(f"{BASE}/items/", json={"name": f"Item{i}", "price": float(i + 1)})
            iid = r.json()["id"]
            client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": iid, "quantity": 1})

        r = client.get(f"{BASE}/stats/top-items?limit=3&date_from=2026-01-01&date_to=2027-01-01")
        assert r.status_code == 200
        assert len(r.json()) == 3

    def test_top_items_sorted_by_revenue(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        tid = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Cheap", "price": 1.0})
        cheap_id = r.json()["id"]
        r = client.post(f"{BASE}/items/", json={"name": "Expensive", "price": 100.0})
        exp_id = r.json()["id"]
        client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": cheap_id, "quantity": 5})
        client.post(f"{BASE}/tables/{tid}/orders/", json={"item_id": exp_id, "quantity": 1})

        r = client.get(f"{BASE}/stats/top-items?date_from=2026-01-01&date_to=2027-01-01")
        items = r.json()
        assert items[0]["item_name"] == "Expensive"
        assert items[1]["item_name"] == "Cheap"

    def test_top_items_default_date_range(self, client):
        r = client.get(f"{BASE}/stats/top-items")
        assert r.status_code == 200

    def test_top_items_invalid_date(self, client):
        r = client.get(f"{BASE}/stats/top-items?date_from=bad-date")
        assert r.status_code == 400
