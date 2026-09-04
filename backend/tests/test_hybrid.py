import pytest
from app.ml.hybrid_policy import POLICY_VERSION, HYBRID_THRESHOLDS
from app.ml.hybrid import select_model_pre_trip, predict_hybrid_eta, compute_prediction_spread
from app.services.hybrid_eta_service import HybridETAService
from app.services.experiment_service import ExperimentService
from app.ml.train import train_and_evaluate
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="module", autouse=True)
def ensure_ml_trained(setup_test_db):
    session = TestingSessionLocal()
    train_and_evaluate(session, model_type="random_forest", n_estimators=50, random_state=42)
    session.close()


def test_data_leakage_invariance():
    """
    Ensure the hybrid model selector does NOT depend on actual travel times,
    future states, or target labels.
    """
    pre_trip_context = {
        "weather_condition": "CLEAR",
        "rainfall_mm": 0.0,
        "traffic_level": "LOW",
        "congestion_index": 15.0,
        "event_level": "NONE",
        "road_restriction_type": "NONE",
        "waste_volume_tons": 4.0,
    }
    
    # 1. Normal context without actual info
    sel1, reason1 = select_model_pre_trip(pre_trip_context)
    assert sel1 == "BASELINE"
    assert reason1 == "NOMINAL_ENVIRONMENTAL_CONDITIONS"

    # 2. Add fake actual outcomes or future variables to the input dict
    context_with_leakage_attempts = dict(pre_trip_context)
    context_with_leakage_attempts["actual_travel_minutes"] = 120.0  # Even if actual was huge
    context_with_leakage_attempts["future_accident"] = True

    sel2, reason2 = select_model_pre_trip(context_with_leakage_attempts)
    assert sel2 == "BASELINE"
    assert reason2 == "NOMINAL_ENVIRONMENTAL_CONDITIONS"


def test_hybrid_policy_switching_rules():
    """Verify each heuristic rule in the hybrid decision policy."""
    # 1. Normal -> Baseline
    sel, r = select_model_pre_trip({"weather_condition": "CLEAR", "traffic_level": "LOW", "congestion_index": 10.0})
    assert sel == "BASELINE"

    # 2. Heavy Rain -> Context-Aware
    sel, r = select_model_pre_trip({"weather_condition": "HEAVY_RAIN", "rainfall_mm": 20.0, "traffic_level": "LOW"})
    assert sel == "CONTEXT_AWARE"
    assert "WEATHER" in r

    # 3. High / Severe Traffic -> Context-Aware
    sel, r = select_model_pre_trip({"weather_condition": "CLEAR", "traffic_level": "HIGH", "congestion_index": 75.0})
    assert sel == "CONTEXT_AWARE"
    assert "TRAFFIC" in r

    # 4. Major Event -> Context-Aware
    sel, r = select_model_pre_trip({"weather_condition": "CLEAR", "event_level": "HIGH", "traffic_level": "LOW"})
    assert sel == "CONTEXT_AWARE"
    assert "EVENT" in r

    # 5. Road Closure -> Context-Aware
    sel, r = select_model_pre_trip({"weather_condition": "CLEAR", "road_restriction_type": "ROAD_CLOSURE"})
    assert sel == "CONTEXT_AWARE"
    assert "ROAD_RESTRICTION" in r


def test_prediction_spread_estimation():
    """Verify uncertainty / spread estimation across Random Forest trees."""
    params = {
        "distance_km": 25.0,
        "waste_volume_tons": 6.0,
        "weather_condition": "STORM",
        "rainfall_mm": 30.0,
        "visibility_km": 2.0,
        "traffic_level": "SEVERE",
        "congestion_index": 90.0,
        "average_speed_kmh": 15.0,
        "event_level": "HIGH",
        "event_radius": 3.0,
        "road_restriction_type": "ROAD_CLOSURE",
        "road_restriction_severity": "FULL",
        "hour_of_day": 17,
        "day_of_week": 4,
    }
    spread = compute_prediction_spread(params)
    assert spread is not None
    assert spread >= 0.0
    assert isinstance(spread, float)


def test_safety_first_hybrid_prediction(db_session):
    """
    Ensure safety constraints run before model selection.
    Unsafe vehicle payload or driver workload breaches must block prediction with UNSAFE_ASSIGNMENT.
    """
    # Over capacity (e.g. 50 tons)
    res = HybridETAService.predict_hybrid(
        params={
            "distance_km": 25.0,
            "waste_volume_tons": 50.0,
            "vehicle_id": 1,  # Capacity is e.g. 8-12 tons
        },
        db=db_session,
    )
    assert res["is_safe"] is False
    assert res["safety_status"] == "UNSAFE_ASSIGNMENT"
    assert res["predicted_eta_minutes"] is None
    assert "CAPACITY" in res["constraint_violation"]["type"]


def test_hybrid_prediction_api(client):
    """Test POST /api/eta/hybrid API endpoint."""
    payload = {
        "distance_km": 22.5,
        "waste_volume_tons": 4.5,
        "weather_condition": "CLEAR",
        "traffic_level": "LOW",
        "congestion_index": 12.0,
        "average_speed_kmh": 40.0,
        "event_level": "NONE",
        "road_restriction_type": "NONE",
        "hour_of_day": 10,
        "day_of_week": 2,
    }
    response = client.post("/api/eta/hybrid", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_model"] == "BASELINE"
    assert data["predicted_eta_minutes"] > 0
    assert data["safety_status"] == "SAFE"
    assert data["policy_version"] == POLICY_VERSION


def test_hybrid_disrupted_api(client):
    """Test POST /api/eta/hybrid for a major event scenario."""
    payload = {
        "distance_km": 30.0,
        "waste_volume_tons": 6.0,
        "weather_condition": "RAIN",
        "traffic_level": "HIGH",
        "congestion_index": 80.0,
        "average_speed_kmh": 20.0,
        "event_level": "HIGH",
        "road_restriction_type": "PARTIAL_CLOSURE",
        "hour_of_day": 18,
        "day_of_week": 5,
    }
    response = client.post("/api/eta/hybrid", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_model"] == "CONTEXT_AWARE"
    assert data["predicted_eta_minutes"] > 0
    assert data["prediction_spread_minutes"] is not None


def test_predict_both_extended_endpoint(client):
    """Test POST /api/eta/predict returns backward compatible and hybrid fields."""
    payload = {
        "distance_km": 18.0,
        "waste_volume_tons": 3.5,
        "weather_condition": "CLEAR",
        "traffic_level": "LOW",
    }
    response = client.post("/api/eta/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "baseline_eta_minutes" in data
    assert "context_aware_eta_minutes" in data
    assert "hybrid_eta_minutes" in data
    assert "selected_model" in data


def test_hybrid_full_suite_benchmark(db_session):
    """Test full 3-model benchmark execution across 5 repetitions."""
    benchmark = ExperimentService.run_full_suite_benchmark(
        db=db_session,
        repetitions=5,
        include_hybrid=True,
    )
    assert benchmark["total_scenarios"] == 6
    assert benchmark["total_experiment_runs"] == 30
    assert "hybrid" in benchmark["global_metrics"]
    assert "hybrid_vs_baseline_mae_impr_pct" in benchmark["global_metrics"]
    assert benchmark["global_winner"] in ["ADAPTIVE_HYBRID", "CONTEXT_AWARE", "BASELINE"]

    # Check scenario breakdown selection rates
    for sc in benchmark["scenario_breakdown"]:
        assert "selection_rates" in sc
        assert "baseline_selected_pct" in sc["selection_rates"]
        assert "context_aware_selected_pct" in sc["selection_rates"]
        assert sc["selection_rates"]["baseline_selected_pct"] + sc["selection_rates"]["context_aware_selected_pct"] == 100.0
