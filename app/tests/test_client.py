
class TestClientAPI:
    client_name_1 = "John Doe"
    client_name_2 = "Jane Doe"

    def test_smoke(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_add_client(self, client):
        url = "/api/clients/clients/"
        response = client.post(url, json={"name": self.client_name_1})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == self.client_name_1
        assert isinstance(data["id"], int)
    
    def test_read_clients_empty(self, client):
        url = "/api/clients/clients/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    def test_read_clients_list(self, client):
        # empty list
        url = "/api/clients/clients/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

        # one client
        # self.test_add_client(client)
        response = client.post(url, json={"name": self.client_name_1})
        url = "/api/clients/clients/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == self.client_name_1

        # two clients
        # self.test_add_client(client)
        response = client.post(url, json={"name": self.client_name_2})
        url = "/api/clients/clients/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 2
        assert response.json()[0]["name"] == self.client_name_1
        assert response.json()[1]["name"] == self.client_name_2
    
    def test_read_client(self, client):
        url = "/api/clients/clients/"
        created_client = client.post(url, json={"name": self.client_name_1})
        response = client.get(url+f"{created_client.json()['id']}/")
        assert response.status_code == 200
        assert response.json()["name"] == self.client_name_1
        assert response.json()["id"] == created_client.json()["id"]
    
    def test_delete_client(self, client):
        url = "/api/clients/clients/"
        created_client = client.post(url, json={"name": self.client_name_1})
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1

        response = client.delete(url+f"{created_client.json()['id']}/")
        assert response.status_code == 200
        assert response.json() == {"message": "Client deleted successfully"}
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0
    
    def test_update_client(self, client):
        url = "/api/clients/clients/"
        created_client = client.post(url, json={"name": self.client_name_1})
        response = client.get(url+f"{created_client.json()['id']}/")
        assert response.status_code == 200
        assert response.json()["name"] == self.client_name_1
        assert response.json()["id"] == created_client.json()["id"]

        response = client.patch(url+f"{created_client.json()['id']}/", json={"name": self.client_name_2})
        assert response.status_code == 200
        assert response.json()["name"] == self.client_name_2
        assert response.json()["id"] == created_client.json()["id"]
        
        response = client.get(url+f"{created_client.json()['id']}/")
        assert response.status_code == 200
        assert response.json()["name"] == self.client_name_2
    
    def test_count_clients(self, client):
        url_client = "/api/clients/clients/"
        url_count = "/api/clients/clients/count/"
        response = client.get(url_count)
        assert response.status_code == 200
        assert response.json() == {"count": 0}

        response = client.post(url_client, json={"name": self.client_name_1})
        response = client.get(url_count)
        assert response.status_code == 200
        assert response.json() == {"count": 1}

        response = client.post(url_client, json={"name": self.client_name_2})
        response = client.get(url_count)
        assert response.status_code == 200
        assert response.json()["count"] == 2
