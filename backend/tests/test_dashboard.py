from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_summary():
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    data = response.json()

    # Verify KPI Fields
    assert "waste_volume" in data
    assert data["waste_volume"] == 8.4
    assert data["active_routes"] == 12
    assert data["average_eta_min"] == 42.0
    assert data["eta_accuracy_pct"] == 91.0
    assert data["available_vehicles"] == "8 / 10"
    assert data["workload_status"] == "Within Limits"
    assert data["is_demo"] is True
    assert data["phase"] == 2

    # Verify Operating Conditions
    cond = data["operating_conditions"]
    assert cond["weather"] == "Clear"
    assert cond["traffic"] == "Moderate"
    assert cond["event_impact"] == "Low"
    assert cond["road_restrictions"] == "None"
    assert cond["waste_volume"] == "Normal"

    # Verify Analytics / Charts demo data
    assert len(data["waste_volume_trends"]) == 7
    assert len(data["eta_comparisons"]) >= 5
    assert len(data["eta_errors"]) >= 5
    assert len(data["vehicle_utilization"]) >= 5
