from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    # Verify KPI Fields
    assert "waste_volume" in data
    assert data["waste_volume"] > 0
    assert data["active_routes"] >= 10
    assert data["average_eta_min"] > 0
    assert data["eta_accuracy_pct"] > 0
    assert "/" in data["available_vehicles"]
    assert "workload_status" in data
    assert data["is_demo"] is True
    assert data["phase"] == 2

    # Verify Operating Conditions
    cond = data["operating_conditions"]
    assert bool(cond["weather"])
    assert bool(cond["traffic"])
    assert bool(cond["event_impact"])
    assert bool(cond["road_restrictions"])
    assert bool(cond["waste_volume"])

    # Verify Analytics / Charts demo data
    assert len(data["waste_volume_trends"]) == 7
    assert len(data["eta_comparisons"]) >= 5
    assert len(data["eta_errors"]) >= 5
    assert len(data["vehicle_utilization"]) >= 5
