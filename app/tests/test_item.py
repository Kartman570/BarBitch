class TestItemAPI:
    item_1 = {"name": "Beer", "price": 10}
    item_2 = {"name": "Wine", "price": 20}

    def test_smoke(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_add_item(self, client):
        url = "/api/items/items/"
        response = client.post(url, json=self.item_1)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == self.item_1["name"]
        assert data["price"] == self.item_1["price"]
        assert isinstance(data["id"], int)
    
    def test_read_items_empty(self, client):
        url = "/api/items/items/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

    def test_read_items_list(self, client):
        # empty list
        url = "/api/items/items/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0

        # one item
        response = client.post(url, json=self.item_1)
        url = "/api/items/items/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == self.item_1["name"]
        assert response.json()[0]["price"] == self.item_1["price"]

        # two items
        response = client.post(url, json=self.item_2)
        url = "/api/items/items/"
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 2
        assert response.json()[0]["name"] == self.item_1["name"]
        assert response.json()[0]["price"] == self.item_1["price"]
        assert response.json()[1]["name"] == self.item_2["name"]
        assert response.json()[1]["price"] == self.item_2["price"]
    
    def test_read_item(self, client):
        url = "/api/items/items/"
        created_item = client.post(url, json=self.item_1)
        response = client.get(url+f"{created_item.json()['id']}/")
        assert response.status_code == 200
        assert response.json()["name"] == self.item_1["name"]
        assert response.json()["price"] == self.item_1["price"]
        assert response.json()["id"] == created_item.json()["id"]
    
    def test_delete_item(self, client):
        url = "/api/items/items/"
        created_item = client.post(url, json=self.item_1)
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 1

        response = client.delete(url+f"{created_item.json()['id']}/")
        assert response.status_code == 200
        assert response.json() == {"message": "Item deleted successfully"}
        response = client.get(url)
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 0
    
    def test_update_item(self, client):
        url = "/api/items/items/"
        created_item = client.post(url, json=self.item_1)
        response = client.get(url+f"{created_item.json()['id']}/")
        assert response.status_code == 200
        assert response.json()["name"] == self.item_1["name"]
        assert response.json()["price"] == self.item_1["price"]
        assert response.json()["id"] == created_item.json()["id"]

        response = client.patch(url+f"{created_item.json()['id']}/", json={"price": self.item_2["price"]})
        assert response.status_code == 200
        assert response.json()["name"] == self.item_1["name"]
        assert response.json()["price"] == self.item_2["price"]
        assert response.json()["id"] == created_item.json()["id"]
        
        response = client.get(url+f"{created_item.json()['id']}/")
        assert response.status_code == 200
        assert response.json()["name"] == self.item_1["name"]
        assert response.json()["price"] == self.item_2["price"]
