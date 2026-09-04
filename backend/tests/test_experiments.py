import pytest
from fastapi.testclient import TestClient
from app.services.experiment_service import ExperimentService
from app.services.failure_analysis import classify_failure_case, analyze_failures, get_top_worst_errors
from app.experiments.generate_report import validate_dataset_science


def test_classify_failure_cases():
    # 1. Unsafe assignment
    unsafe_run = {"is_safe": False, "status": "UNSAFE_ASSIGNMENT"}
    assert classify_failure_case(unsafe_run) == "SAFETY_CONSTRAINT"

    # 2. Road closure mismatch
    closure_run = {
        "is_safe": True,
        "parameters": {"road_restriction_type": "ROAD_CLOSURE"},
        "context_aware_error_minutes": 25.0,
        "baseline_error_minutes": 10.0,
        "context_aware_eta_minutes": 40.0,
        "actual_travel_minutes": 65.0,
    }
    assert classify_failure_case(closure_run) == "ROAD_RESTRICTION_MISMATCH"

    # 3. Context mismatch (baseline outperformed context by > 5 min)
    mismatch_run = {
        "is_safe": True,
        "parameters": {},
        "context_aware_error_minutes": 20.0,
        "baseline_error_minutes": 5.0,
        "context_aware_eta_minutes": 50.0,
        "actual_travel_minutes": 30.0,
    }
    assert classify_failure_case(mismatch_run) == "CONTEXT_MISMATCH"


def test_experiment_single_scenario_execution(db_session):
    res = ExperimentService.run_scenario_experiment(
        scenario_key="HEAVY_RAIN",
        db=db_session,
        repetitions=5,
        persist_to_db=False,
    )
    assert res["scenario_key"] == "HEAVY_RAIN"
    assert res["repetitions"] == 5
    assert len(res["runs"]) == 5
    assert "metrics" in res
    assert "baseline" in res["metrics"]
    assert "context_aware" in res["metrics"]
    assert res["winner"] in ["BASELINE", "CONTEXT_AWARE", "TIE", "UNSAFE"]


def test_experiment_full_suite_benchmark(db_session):
    benchmark = ExperimentService.run_full_suite_benchmark(db=db_session, repetitions=3)
    assert benchmark["total_scenarios"] == 6
    assert benchmark["total_experiment_runs"] == 18
    assert "global_metrics" in benchmark
    assert "failure_analysis" in benchmark
    assert "top_worst_errors" in benchmark


def test_validate_dataset_science(db_session):
    val = validate_dataset_science(db_session)
    assert val["total_records"] > 0
    assert val["duplicate_rows"] == 0
    assert val["missing_targets"] == 0
    assert val["negative_travel_times"] == 0


def test_experiment_api_endpoints(client: TestClient):
    # 1. Run full benchmark via API
    run_res = client.post("/api/experiments/run", json={"scenario_key": "ALL", "repetitions": 3})
    assert run_res.status_code == 200
    data = run_res.json()
    assert data["total_scenarios"] == 6

    # 2. Get Results
    res = client.get("/api/experiments/results?repetitions=3")
    assert res.status_code == 200
    assert "global_metrics" in res.json()

    # 3. Get Failures
    failures = client.get("/api/experiments/failures?repetitions=3")
    assert failures.status_code == 200
    assert "category_breakdown" in failures.json()

    # 4. Get Comparison
    comp = client.get("/api/experiments/comparison?repetitions=3")
    assert comp.status_code == 200
    assert "comparison_table" in comp.json()
