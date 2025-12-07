class TestHappyPathsAPI:
    client_url = "/api/clients/clients/"
    item_url = "/api/items/items/"
    order_url = "/api/orders/with-items/"
    
    client_1 = {"name": "John Doe"}
    client_2 = {"name": "Bob Smith"}

    item_1_base = {"name": "Beer", "price": 10}
    item_2_base = {"name": "Wine", "price": 20}
    item_1 = {**item_1_base, "id": 1}
    item_2 = {**item_2_base, "id": 2}

    # order_1 = {"client_id": 1, "total_price": 100}
    # order_2 = {"client_id": 2, "total_price": 200}
    def init_items(self, client):
        response = client.get(self.item_url)
        assert response.json() == []
        client.post(self.item_url, json=self.item_1_base)
        client.post(self.item_url, json=self.item_2_base)
        response = client.get(self.item_url).json()
        
        self.item_1 = {**self.item_1_base, "id": response[0]["id"]}
        self.item_2 = {**self.item_2_base, "id": response[1]["id"]}
        assert response == [self.item_1, self.item_2]

    def test_smoke(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_new_client_orders(self, client):
        self.init_items(client)
        assert self.item_1["id"] == 1
        assert self.item_2["id"] == 2

        # new client got in bar - create entry in clients table
        response = client.post(self.client_url, json=self.client_1).json()
        client_id = response["id"]

        # new client orders beer - create entry in orders table
        response = client.post(
            self.order_url,
            json={
                "client_id": client_id,
                "items": [
                    {"item_id": self.item_1["id"], "quantity": 1},
                ]
            }
        ).json()
        print(response)
        assert response["client_id"] == client_id
        assert response["items"] == [
            {"id": response["items"][0]["id"], "item_id": self.item_1["id"], "quantity": 1},
        ]
        assert response["total_price"] == self.item_1["price"]
