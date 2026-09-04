def test_get_vehicles_api(client):
    response = client.get("/api/vehicles?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 10
    assert len(data["items"]) == 5
    assert data["items"][0]["capacity_tons"] > 0


def test_get_drivers_api(client):
    response = client.get("/api/drivers?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 15
    assert data["items"][0]["max_work_minutes_per_shift"] == 480


def test_get_weather_api(client):
    response = client.get("/api/weather?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 5
    assert "condition" in data["items"][0]


def test_get_traffic_api(client):
    response = client.get("/api/traffic?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 5
    assert 0 <= data["items"][0]["congestion_index"] <= 100


def test_get_events_api(client):
    response = client.get("/api/events")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 5


def test_get_road_restrictions_api(client):
    response = client.get("/api/road-restrictions")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 5


def test_get_scenarios_api(client):
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 5


def test_get_experiments_api(client):
    response = client.get("/api/experiments")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 5
    assert len(data["items"][0]["results"]) >= 1


def test_get_observations_api(client):
    response = client.get("/api/observations?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 50


def test_safety_validate_capacity_endpoint(client):
    response = client.post(
        "/api/safety/validate-capacity",
        json={"vehicle_id": 1, "assigned_waste_tons": 5.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True


def test_safety_validate_capacity_overload_endpoint(client):
    response = client.post(
        "/api/safety/validate-capacity",
        json={"vehicle_id": 1, "assigned_waste_tons": 500.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["violation_type"] == "PAYLOAD_CAPACITY_EXCEEDED"
