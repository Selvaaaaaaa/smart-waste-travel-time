import pytest
from app.services.scenario_engine import ScenarioEngine, STANDARD_SCENARIOS


def test_standard_scenarios_exist():
    expected = ["NORMAL", "HEAVY_RAIN", "MAJOR_EVENT", "ROAD_CLOSURE", "HIGH_WASTE", "COMBINED_STRESS"]
    for sc in expected:
        assert sc in STANDARD_SCENARIOS
        assert "weather_condition" in STANDARD_SCENARIOS[sc]
        assert "congestion_index" in STANDARD_SCENARIOS[sc]


def test_scenario_reproducibility():
    engine1 = ScenarioEngine(random_seed=42)
    engine2 = ScenarioEngine(random_seed=42)

    params = {"distance_km": 25.0, "average_speed_kmh": 30.0, "rainfall_mm": 10.0}
    t1 = engine1.simulate_actual_travel_minutes(params)
    t2 = engine2.simulate_actual_travel_minutes(params)

    assert t1 == t2


def test_run_normal_scenario(db_session):
    engine = ScenarioEngine(random_seed=42)
    res = engine.run_scenario({"scenario_key": "NORMAL", "distance_km": 20.0}, db=db_session)

    assert res["status"] == "COMPLETED"
    assert res["is_safe"] is True
    assert res["baseline_eta_minutes"] is not None
    assert res["context_aware_eta_minutes"] is not None
    assert res["simulated_actual_minutes"] is not None


def test_scenario_unsafe_payload_violation(db_session):
    engine = ScenarioEngine(random_seed=42)
    res = engine.run_scenario(
        {"scenario_key": "NORMAL", "waste_volume_tons": 50.0},  # Exceeds max vehicle capacity
        db=db_session,
    )

    assert res["status"] == "UNSAFE_ASSIGNMENT"
    assert res["is_safe"] is False
    assert res["constraint_violation"]["type"] == "PAYLOAD_CAPACITY_EXCEEDED"
