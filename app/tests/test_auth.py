BASE = "/api/v1"


class TestRoles:
    def test_create_role(self, client):
        r = client.post(f"{BASE}/roles/", json={
            "name": "barman",
            "description": "Bartender",
            "permissions": ["tables"],
        })
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "barman"
        assert data["permissions"] == ["tables"]

    def test_list_roles(self, client):
        client.post(f"{BASE}/roles/", json={"name": "cook", "permissions": ["stock", "items"]})
        client.post(f"{BASE}/roles/", json={"name": "manager", "permissions": ["tables", "stats"]})
        r = client.get(f"{BASE}/roles/")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_get_role(self, client):
        r = client.post(f"{BASE}/roles/", json={"name": "cook", "permissions": ["stock"]})
        role_id = r.json()["id"]
        r = client.get(f"{BASE}/roles/{role_id}")
        assert r.status_code == 200
        assert r.json()["name"] == "cook"

    def test_update_role_permissions(self, client):
        r = client.post(f"{BASE}/roles/", json={"name": "barman", "permissions": ["tables"]})
        role_id = r.json()["id"]
        r = client.patch(f"{BASE}/roles/{role_id}", json={"permissions": ["tables", "stats"]})
        assert r.status_code == 200
        assert set(r.json()["permissions"]) == {"tables", "stats"}

    def test_duplicate_role_name_rejected(self, client):
        client.post(f"{BASE}/roles/", json={"name": "barman", "permissions": []})
        r = client.post(f"{BASE}/roles/", json={"name": "barman", "permissions": []})
        assert r.status_code == 400
        assert "already exists" in r.json()["detail"]

    def test_invalid_permission_rejected(self, client):
        r = client.post(f"{BASE}/roles/", json={"name": "test", "permissions": ["fly"]})
        assert r.status_code == 400
        assert "Unknown permissions" in r.json()["detail"]

    def test_delete_role(self, client):
        r = client.post(f"{BASE}/roles/", json={"name": "temp", "permissions": []})
        role_id = r.json()["id"]
        assert client.delete(f"{BASE}/roles/{role_id}").status_code == 200
        assert client.get(f"{BASE}/roles/{role_id}").status_code == 404

    def test_cannot_delete_admin_role(self, client):
        r = client.post(f"{BASE}/roles/", json={"name": "admin", "permissions": []})
        role_id = r.json()["id"]
        r = client.delete(f"{BASE}/roles/{role_id}")
        assert r.status_code == 400
        assert "admin" in r.json()["detail"]

    def test_cannot_delete_role_with_users(self, client):
        r = client.post(f"{BASE}/roles/", json={"name": "barman", "permissions": ["tables"]})
        role_id = r.json()["id"]
        client.post(f"{BASE}/users/", json={
            "name": "Alice", "username": "alice", "password": "pass", "role_id": role_id
        })
        r = client.delete(f"{BASE}/roles/{role_id}")
        assert r.status_code == 400
        assert "assigned users" in r.json()["detail"]


class TestAuth:
    def _create_role_and_user(self, client, username="alice", password="secret"):
        r = client.post(f"{BASE}/roles/", json={"name": "barman", "permissions": ["tables"]})
        role_id = r.json()["id"]
        client.post(f"{BASE}/users/", json={
            "name": "Alice", "username": username, "password": password, "role_id": role_id
        })
        return role_id

    def test_login_success(self, client):
        self._create_role_and_user(client, "alice", "secret")
        r = client.post(f"{BASE}/auth/login", json={"username": "alice", "password": "secret"})
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "alice"
        assert data["role_name"] == "barman"
        assert "tables" in data["permissions"]

    def test_login_wrong_password(self, client):
        self._create_role_and_user(client, "alice", "secret")
        r = client.post(f"{BASE}/auth/login", json={"username": "alice", "password": "wrong"})
        assert r.status_code == 401

    def test_login_unknown_user(self, client):
        r = client.post(f"{BASE}/auth/login", json={"username": "nobody", "password": "x"})
        assert r.status_code == 401

    def test_permissions_reflect_role(self, client):
        r = client.post(f"{BASE}/roles/", json={
            "name": "manager", "permissions": ["tables", "stats", "users"]
        })
        role_id = r.json()["id"]
        client.post(f"{BASE}/users/", json={
            "name": "Bob", "username": "bob", "password": "pass", "role_id": role_id
        })
        r = client.post(f"{BASE}/auth/login", json={"username": "bob", "password": "pass"})
        assert r.status_code == 200
        perms = set(r.json()["permissions"])
        assert perms == {"tables", "stats", "users"}

    def test_duplicate_username_rejected(self, client):
        role_id = self._create_role_and_user(client, "alice", "pass")
        r = client.post(f"{BASE}/users/", json={
            "name": "Alice2", "username": "alice", "password": "pass", "role_id": role_id
        })
        assert r.status_code == 400
        assert "already taken" in r.json()["detail"]

    def test_login_returns_access_token(self, client):
        self._create_role_and_user(client, "alice", "secret")
        r = client.post(f"{BASE}/auth/login", json={"username": "alice", "password": "secret"})
        assert r.status_code == 200
        assert "access_token" in r.json()
        assert len(r.json()["access_token"]) > 20


class TestTokenEnforcement:
    """Tests that protected routes reject requests with missing or invalid tokens."""

    def test_no_token_returns_401(self, raw_client):
        r = raw_client.get(f"{BASE}/items/")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, raw_client):
        r = raw_client.get(
            f"{BASE}/items/",
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert r.status_code == 401

    def test_expired_token_returns_401(self, raw_client):
        from datetime import datetime, timedelta, timezone
        from jose import jwt

        expired_token = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            "change-me-in-production",
            algorithm="HS256",
        )
        r = raw_client.get(
            f"{BASE}/items/",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert r.status_code == 401

