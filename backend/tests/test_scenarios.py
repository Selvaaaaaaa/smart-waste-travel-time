from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_scenario_options():
    response = client.get("/api/scenarios/options")
    assert response.status_code == 200
    data = response.json()
    assert "weather_options" in data
    assert "traffic_options" in data
    assert "event_options" in data
    assert "road_restriction_options" in data
    assert "waste_volume_options" in data
    assert "time_of_day_options" in data
    assert data["is_demo"] is True

    assert "Clear" in data["weather_options"]
    assert "Heavy Rain" in data["weather_options"]
    assert "Medium" in data["traffic_options"]
    assert "Major Event" in data["event_options"]
