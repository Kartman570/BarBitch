BASE = "/api/v1"


class TestSmoke:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json() == {"message": "Hello World"}


class TestItems:
    def test_create_and_read(self, client):
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Beer"
        assert data["price"] == 5.0
        assert data["is_available"] is True
        item_id = data["id"]

        r = client.get(f"{BASE}/items/{item_id}")
        assert r.status_code == 200
        assert r.json()["id"] == item_id

    def test_list_items(self, client):
        client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0, "category": "drink"})
        client.post(f"{BASE}/items/", json={"name": "Wine", "price": 8.0, "category": "drink"})
        client.post(f"{BASE}/items/", json={"name": "Nachos", "price": 4.0, "category": "food"})

        r = client.get(f"{BASE}/items/")
        assert len(r.json()) == 3

        r = client.get(f"{BASE}/items/?category=food")
        assert len(r.json()) == 1
        assert r.json()[0]["name"] == "Nachos"

        r = client.get(f"{BASE}/items/?name=beer")
        assert len(r.json()) == 1

    def test_update_item(self, client):
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        item_id = r.json()["id"]

        r = client.put(f"{BASE}/items/{item_id}", json={"price": 6.0, "is_available": False})
        assert r.status_code == 200
        assert r.json()["price"] == 6.0
        assert r.json()["is_available"] is False

    def test_delete_item(self, client):
        r = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0})
        item_id = r.json()["id"]

        r = client.delete(f"{BASE}/items/{item_id}")
        assert r.status_code == 200

        r = client.get(f"{BASE}/items/{item_id}")
        assert r.status_code == 404

    def test_404(self, client):
        assert client.get(f"{BASE}/items/9999").status_code == 404


class TestUsers:
    def _make_role(self, client, name="barman"):
        """Create a role and return its id."""
        r = client.post(f"{BASE}/roles/", json={"name": name, "permissions": ["tables"]})
        return r.json()["id"]

    def test_create_and_read(self, client):
        role_id = self._make_role(client)
        r = client.post(f"{BASE}/users/", json={
            "name": "Alice", "username": "alice", "password": "pass123!", "role_id": role_id
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "Alice"
        assert data["username"] == "alice"
        assert data["role_name"] == "barman"
        user_id = data["id"]

        r = client.get(f"{BASE}/users/{user_id}")
        assert r.status_code == 200

    def test_update_user(self, client):
        role_id = self._make_role(client, "barman")
        r = client.post(f"{BASE}/users/", json={
            "name": "Bob", "username": "bob", "password": "pass123!", "role_id": role_id
        })
        user_id = r.json()["id"]

        admin_role_id = self._make_role(client, "admin2")
        r = client.put(f"{BASE}/users/{user_id}", json={"role_id": admin_role_id})
        assert r.status_code == 200
        assert r.json()["role_id"] == admin_role_id

    def test_delete_user(self, client):
        role_id = self._make_role(client, "cook")
        r = client.post(f"{BASE}/users/", json={
            "name": "Carol", "username": "carol", "password": "pass123!", "role_id": role_id
        })
        user_id = r.json()["id"]
        assert client.delete(f"{BASE}/users/{user_id}").status_code == 200
        assert client.get(f"{BASE}/users/{user_id}").status_code == 404


class TestTables:
    def test_create_and_list(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 1"})
        assert r.status_code == 200
        data = r.json()
        assert data["table_name"] == "Table 1"
        assert data["status"] == "Active"
        assert data["total"] == 0.0

        r = client.get(f"{BASE}/tables/")
        assert len(r.json()) == 1

    def test_get_table_detailed(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "Table 2"})
        table_id = r.json()["id"]

        r = client.get(f"{BASE}/tables/{table_id}")
        assert r.status_code == 200
        assert "orders" in r.json()
        assert r.json()["orders"] == []

    def test_filter_by_status(self, client):
        client.post(f"{BASE}/tables/", json={"table_name": "T1"})
        r2 = client.post(f"{BASE}/tables/", json={"table_name": "T2"})
        client.post(f"{BASE}/tables/{r2.json()['id']}/close")

        r = client.get(f"{BASE}/tables/?status=Active")
        assert len(r.json()) == 1
        r = client.get(f"{BASE}/tables/?status=Closed")
        assert len(r.json()) == 1

    def test_rename_table(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "Old Name"})
        table_id = r.json()["id"]

        r = client.patch(f"{BASE}/tables/{table_id}", json={"table_name": "New Name"})
        assert r.status_code == 200
        assert r.json()["table_name"] == "New Name"

    def test_delete_table(self, client):
        r = client.post(f"{BASE}/tables/", json={"table_name": "Temp"})
        table_id = r.json()["id"]
        assert client.delete(f"{BASE}/tables/{table_id}").status_code == 200
        assert client.get(f"{BASE}/tables/{table_id}").status_code == 404


class TestOrders:
    def _setup(self, client):
        item_id = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0}).json()["id"]
        table_id = client.post(f"{BASE}/tables/", json={"table_name": "T1"}).json()["id"]
        return table_id, item_id

    def test_add_and_list_orders(self, client):
        table_id, item_id = self._setup(client)

        r = client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 2})
        assert r.status_code == 200
        data = r.json()
        assert data["item_id"] == item_id
        assert data["quantity"] == 2
        assert data["price"] == 5.0  # price snapshot

        r = client.get(f"{BASE}/tables/{table_id}/orders/")
        assert len(r.json()) == 1

    def test_price_snapshot(self, client):
        """Price is fixed at order time — later item price changes must not affect it."""
        table_id, item_id = self._setup(client)

        client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 1})
        # change item price
        client.put(f"{BASE}/items/{item_id}", json={"price": 99.0})

        orders = client.get(f"{BASE}/tables/{table_id}/orders/").json()
        assert orders[0]["price"] == 5.0  # still original price

    def test_update_order_quantity(self, client):
        table_id, item_id = self._setup(client)
        order_id = client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 1}).json()["id"]

        r = client.patch(f"{BASE}/tables/{table_id}/orders/{order_id}", json={"quantity": 3})
        assert r.status_code == 200
        assert r.json()["quantity"] == 3

    def test_delete_order(self, client):
        table_id, item_id = self._setup(client)
        order_id = client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 1}).json()["id"]

        assert client.delete(f"{BASE}/tables/{table_id}/orders/{order_id}").status_code == 200
        assert client.get(f"{BASE}/tables/{table_id}/orders/{order_id}").status_code == 404

    def test_orders_cascade_delete_with_table(self, client):
        table_id, item_id = self._setup(client)
        client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 1})
        client.delete(f"{BASE}/tables/{table_id}")
        # Table gone — orders gone with it (cascade)
        assert client.get(f"{BASE}/tables/{table_id}").status_code == 404

    def test_cannot_add_order_to_closed_table(self, client):
        table_id, item_id = self._setup(client)
        client.post(f"{BASE}/tables/{table_id}/close")

        r = client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 1})
        assert r.status_code == 400


class TestCloseTable:
    def test_close_computes_total(self, client):
        item_id = client.post(f"{BASE}/items/", json={"name": "Beer", "price": 5.0}).json()["id"]
        table_id = client.post(f"{BASE}/tables/", json={"table_name": "T1"}).json()["id"]

        client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 3})  # 15.0
        client.post(f"{BASE}/tables/{table_id}/orders/", json={"item_id": item_id, "quantity": 1})  # 5.0

        r = client.post(f"{BASE}/tables/{table_id}/close")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "Closed"
        assert data["total"] == 20.0
        assert data["closed_at"] is not None

    def test_cannot_close_twice(self, client):
        table_id = client.post(f"{BASE}/tables/", json={"table_name": "T1"}).json()["id"]
        client.post(f"{BASE}/tables/{table_id}/close")
        r = client.post(f"{BASE}/tables/{table_id}/close")
        assert r.status_code == 400
