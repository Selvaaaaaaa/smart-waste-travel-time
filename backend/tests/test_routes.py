from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_all_routes():
    response = client.get("/api/routes")
    assert response.status_code == 200
    data = response.json()
    assert "routes" in data
    assert data["total"] > 0
    assert data["is_demo"] is True

    first = data["routes"][0]
    assert "route_id" in first
    assert "vehicle_id" in first
    assert "driver_name" in first
    assert "waste_volume_tons" in first
    assert "distance_km" in first
    assert "baseline_eta_min" in first
    assert "context_eta_min" in first
    assert "status" in first


def test_filter_routes_by_status():
    response = client.get("/api/routes?status=Delayed")
    assert response.status_code == 200
    data = response.json()
    for route in data["routes"]:
        assert route["status"] == "Delayed"


def test_filter_routes_by_search():
    response = client.get("/api/routes?search=Mercer")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert "Mercer" in data["routes"][0]["driver_name"]
