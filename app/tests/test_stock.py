BASE = "/api/v1"


class TestStock:
    def test_stock_untracked_by_default(self, client):
        """New item without stock_qty should have it as None."""
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        assert data["stock_qty"] is None

    def test_set_initial_stock(self, client):
        """Create item with initial stock_qty."""
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 50}
        )
        assert r.status_code == 200
        data = r.json()
        assert data["stock_qty"] == 50

    def test_add_stock(self, client):
        """Add stock to an item."""
        # Create item with initial stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 50}
        )
        item_id = r.json()["id"]

        # Add 20 units
        r = client.patch(
            f"{BASE}/items/{item_id}/stock",
            json={"delta": 20}
        )
        assert r.status_code == 200
        assert r.json()["stock_qty"] == 70

    def test_remove_stock(self, client):
        """Remove stock from an item."""
        # Create item with initial stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 50}
        )
        item_id = r.json()["id"]

        # Remove 5 units
        r = client.patch(
            f"{BASE}/items/{item_id}/stock",
            json={"delta": -5}
        )
        assert r.status_code == 200
        assert r.json()["stock_qty"] == 45

    def test_remove_too_much_stock(self, client):
        """Cannot remove more stock than available."""
        # Create item with initial stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 10}
        )
        item_id = r.json()["id"]

        # Try to remove 999 units
        r = client.patch(
            f"{BASE}/items/{item_id}/stock",
            json={"delta": -999}
        )
        assert r.status_code == 400
        assert "Insufficient stock" in r.json()["detail"]

        # Verify stock unchanged
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 10

    def test_adjust_untracked_stock(self, client):
        """Cannot adjust stock for items with stock_qty=None."""
        # Create item without stock tracking
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Service Item", "price": 100.0}
        )
        item_id = r.json()["id"]

        # Try to adjust
        r = client.patch(
            f"{BASE}/items/{item_id}/stock",
            json={"delta": 10}
        )
        assert r.status_code == 400
        assert "Stock not tracked" in r.json()["detail"]

    def test_stock_in_item_list(self, client):
        """GET /items/ includes stock_qty field."""
        client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0, "stock_qty": 50})
        client.post(f"{BASE}/items/", json={"name": "Wine", "price": 8.0})

        r = client.get(f"{BASE}/items/")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 2

        # Find items
        beer = next(i for i in items if i["name"] == "Beer")
        wine = next(i for i in items if i["name"] == "Wine")

        assert beer["stock_qty"] == 50
        assert wine["stock_qty"] is None

    def test_stock_zero_allowed(self, client):
        """Stock can be zero (item out of stock)."""
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 0}
        )
        assert r.status_code == 200
        assert r.json()["stock_qty"] == 0

        # Can add to it
        item_id = r.json()["id"]
        r = client.patch(
            f"{BASE}/items/{item_id}/stock",
            json={"delta": 5}
        )
        assert r.status_code == 200
        assert r.json()["stock_qty"] == 5

    def test_order_decreases_tracked_stock(self, client):
        """Adding an order should decrease stock if item has stock tracking."""
        # Create item with stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 10}
        )
        item_id = r.json()["id"]

        # Create table
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        table_id = r.json()["id"]

        # Add order for 3 units
        r = client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 3}
        )
        assert r.status_code == 200

        # Check stock decreased
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["stock_qty"] == 7  # 10 - 3

    def test_order_fails_insufficient_stock(self, client):
        """Cannot add order if insufficient stock."""
        # Create item with limited stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 5}
        )
        item_id = r.json()["id"]

        # Create table
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        table_id = r.json()["id"]

        # Try to add order for more than available
        r = client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 10}
        )
        assert r.status_code == 400
        assert "Insufficient stock" in r.json()["detail"]

        # Verify stock unchanged
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 5

    def test_multiple_orders_decrease_stock(self, client):
        """Multiple orders should cumulatively decrease stock."""
        # Create item with stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 20}
        )
        item_id = r.json()["id"]

        # Create table
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        table_id = r.json()["id"]

        # Add first order for 5 units
        client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 5}
        )

        # Add second order for 7 units
        client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 7}
        )

        # Check stock decreased by total
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 8  # 20 - 5 - 7

    def test_order_untracked_stock_no_deduction(self, client):
        """Orders on untracked items should not affect stock."""
        # Create item without stock tracking
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Service", "price": 100.0}
        )
        item_id = r.json()["id"]

        # Create table
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        table_id = r.json()["id"]

        # Add order should succeed
        r = client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 100}
        )
        assert r.status_code == 200

        # Verify stock_qty is still None
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] is None

    def test_increase_order_qty_decreases_stock(self, client):
        """Increasing order quantity should deduct additional stock."""
        # Create item with stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 20}
        )
        item_id = r.json()["id"]

        # Create table and order
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        table_id = r.json()["id"]
        r = client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 5}
        )
        order_id = r.json()["id"]

        # Stock should be 15 now (20 - 5)
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 15

        # Increase order quantity to 8
        r = client.patch(
            f"{BASE}/tables/{table_id}/orders/{order_id}",
            json={"quantity": 8}
        )
        assert r.status_code == 200

        # Stock should be 12 now (15 - 3 additional)
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 12

    def test_decrease_order_qty_restores_stock(self, client):
        """Decreasing order quantity should restore stock."""
        # Create item with stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 20}
        )
        item_id = r.json()["id"]

        # Create table and order
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        table_id = r.json()["id"]
        r = client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 10}
        )
        order_id = r.json()["id"]

        # Stock should be 10 now (20 - 10)
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 10

        # Decrease order quantity to 6
        r = client.patch(
            f"{BASE}/tables/{table_id}/orders/{order_id}",
            json={"quantity": 6}
        )
        assert r.status_code == 200

        # Stock should be 14 now (10 + 4 restored)
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 14

    def test_increase_order_qty_insufficient_stock(self, client):
        """Cannot increase order quantity if insufficient stock."""
        # Create item with limited stock
        r = client.post(
            f"{BASE}/items/",
            json={"name": "Beer", "price": 5.0, "stock_qty": 10}
        )
        item_id = r.json()["id"]

        # Create table and order
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        table_id = r.json()["id"]
        r = client.post(
            f"{BASE}/tables/{table_id}/orders/",
            json={"item_id": item_id, "quantity": 8}
        )
        order_id = r.json()["id"]

        # Stock is 2 now (10 - 8)
        # Try to increase to 11 (would need 3 more, but only 2 available)
        r = client.patch(
            f"{BASE}/tables/{table_id}/orders/{order_id}",
            json={"quantity": 11}
        )
        assert r.status_code == 400
        assert "Insufficient stock" in r.json()["detail"]

        # Verify stock unchanged and order quantity unchanged
        r = client.get(f"{BASE}/items/{item_id}")
        assert r.json()["stock_qty"] == 2
        r = client.get(f"{BASE}/tables/{table_id}/orders/{order_id}")
        assert r.json()["quantity"] == 8
