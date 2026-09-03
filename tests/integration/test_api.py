def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "app_name" in data
    assert "environment" in data
