import pytest
from fastapi.testclient import TestClient


def test_get_ml_status(client: TestClient):
    response = client.get("/api/ml/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_trained" in data
    assert "synthetic_disclaimer" in data


def test_ml_train_and_predict_flow(client: TestClient):
    # 1. Train model endpoint
    train_res = client.post("/api/ml/train", json={"model_type": "random_forest", "n_estimators": 50})
    assert train_res.status_code == 200
    train_data = train_res.json()
    assert train_data["status"] == "SUCCESS"
    assert train_data["metadata"]["is_trained"] is True
    assert train_data["metadata"]["metrics"]["context_aware"]["mae"] >= 0

    # 2. Predict ETA endpoint
    pred_res = client.post(
        "/api/eta/predict",
        json={
            "distance_km": 30.0,
            "waste_volume_tons": 6.0,
            "weather_condition": "CLEAR",
            "traffic_level": "LOW",
            "congestion_index": 20.0,
            "average_speed_kmh": 40.0,
            "hour_of_day": 10,
            "day_of_week": 2,
        },
    )
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert pred_data["baseline_eta_minutes"] == 72.0  # 30km / 25km/h * 60 = 72 min
    assert pred_data["context_aware_eta_minutes"] > 0
    assert "difference_minutes" in pred_data


def test_predict_validation_error(client: TestClient):
    # Invalid distance <= 0
    res = client.post("/api/eta/predict", json={"distance_km": -10.0})
    assert res.status_code == 422


def test_scenario_run_api(client: TestClient):
    # Run heavy rain scenario
    res = client.post("/api/scenarios/run", json={"scenario_key": "HEAVY_RAIN", "distance_km": 25.0})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["baseline_eta_minutes"] == 60.0
    assert data["context_aware_eta_minutes"] > 0
    assert data["simulated_actual_minutes"] > 0


def test_scenario_unsafe_assignment_api(client: TestClient):
    # Overweight payload
    res = client.post(
        "/api/scenarios/run",
        json={"scenario_key": "NORMAL", "distance_km": 25.0, "waste_volume_tons": 100.0},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UNSAFE_ASSIGNMENT"
    assert data["is_safe"] is False
    assert data["constraint_violation"]["type"] == "PAYLOAD_CAPACITY_EXCEEDED"
