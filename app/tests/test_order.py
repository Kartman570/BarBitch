class TestOrderAPI:
    order_1 = {"client_id": 1, "total_price": 100}
    order_2 = {"client_id": 2, "total_price": 200}

    def test_smoke(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    # def test_add_order(self, client):
    #     url = "/api/orders/orders/"
    #     response = client.post(url, json={"client_id": 1, "total_price": 100})
    #     assert response.status_code == 200
    #     data = response.json()
    #     assert data["client_id"] == 1
    #     assert data["total_price"] == 100
    #     assert isinstance(data["id"], int)
