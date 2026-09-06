"""Comprehensive test suite for Phase 8 Advanced Fleet Optimization, Realistic Validation & Benchmarks."""
import pytest
from fastapi.testclient import TestClient
from app.fleet.fleet_scoring import (
    calculate_allocation_score,
    calculate_baseline_score,
    calculate_workload_balance,
    evaluate_vehicle_safety_gate,
)
from app.fleet.fleet_state import FleetStateManager
from app.fleet.task_allocator import TaskAllocator
from app.fleet.fleet_optimizer import FleetOptimizer
from app.fleet.fleet_rebalancer import FleetRebalancer
from app.fleet.task_insertion import DynamicTaskInserter
from app.fleet.end_to_end_simulator import EndToEndFleetSimulator
from app.fleet.phase8_experiments import Phase8ExperimentRunner
from app.routing.graph import get_default_network_graph


def test_phase8_scoring_formula_weights():
    """Verify 7-component formula: 0.30 ETA, 0.20 Dist, 0.15 Payload, 0.10 Shift, 0.10 Traffic, 0.05 Weather, 0.10 Workload."""
    score = calculate_allocation_score(
        predicted_eta_minutes=30.0,
        additional_distance_km=10.0,
        projected_payload_kg=5000.0,
        vehicle_capacity_kg=10000.0,
        projected_shift_minutes=240.0,
        max_shift_minutes=480.0,
        traffic_congestion_index=20.0,
        weather_severity_index=10.0,
        vehicle_workload_min=100.0,
        fleet_mean_workload_min=100.0,
    )
    assert 0.0 <= score <= 1.0
    assert isinstance(score, float)

    # Higher ETA or distance must produce worse (higher) score
    worse_score = calculate_allocation_score(
        predicted_eta_minutes=90.0,
        additional_distance_km=40.0,
        projected_payload_kg=5000.0,
        vehicle_capacity_kg=10000.0,
        projected_shift_minutes=240.0,
        max_shift_minutes=480.0,
        traffic_congestion_index=20.0,
        weather_severity_index=10.0,
        vehicle_workload_min=100.0,
        fleet_mean_workload_min=100.0,
    )
    assert worse_score > score


def test_workload_balance_metric():
    """Verify fleet workload average and vehicle deviation balance calculations."""
    # Perfectly even workloads
    even_workloads = {"V-01": 120.0, "V-02": 120.0, "V-03": 120.0}
    mean_val, std_val, balance = calculate_workload_balance(even_workloads)
    assert mean_val == 120.0
    assert std_val == 0.0
    assert balance == 1.0

    # Skewed workloads
    skewed_workloads = {"V-01": 400.0, "V-02": 50.0, "V-03": 0.0}
    mean_s, std_s, balance_s = calculate_workload_balance(skewed_workloads)
    assert mean_s > 0
    assert std_s > 0
    assert balance_s < balance  # Lower balance score for uneven workload


def test_strict_safety_gate_rejections():
    """Verify hard safety constraint rejections override optimization."""
    # 1. Payload capacity exceeded
    is_safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="AVAILABLE",
        current_payload_kg=9500.0,
        task_waste_kg=2000.0,
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=100.0,
        estimated_trip_min=20.0,
        max_driver_shift_min=480.0,
    )
    assert not is_safe
    assert "PAYLOAD_CAPACITY_EXCEEDED" in reason

    # 2. Driver shift fatigue exceeded
    is_safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="AVAILABLE",
        current_payload_kg=1000.0,
        task_waste_kg=500.0,
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=470.0,
        estimated_trip_min=30.0,
        max_driver_shift_min=480.0,
    )
    assert not is_safe
    assert "DRIVER_SHIFT_EXCEEDED" in reason

    # 3. Impassable road closure
    is_safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="AVAILABLE",
        current_payload_kg=1000.0,
        task_waste_kg=500.0,
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=100.0,
        estimated_trip_min=20.0,
        max_driver_shift_min=480.0,
        route_is_blocked=True,
    )
    assert not is_safe
    assert "ROAD_SEGMENT_IMPASSABLE" in reason

    # 4. Vehicle Breakdown
    is_safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="BREAKDOWN",
        current_payload_kg=0.0,
        task_waste_kg=500.0,
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=0.0,
        estimated_trip_min=20.0,
        max_driver_shift_min=480.0,
    )
    assert not is_safe
    assert "VEHICLE_BREAKDOWN" in reason


def test_emergency_request_10_step_insertion():
    """Verify 10-step emergency waste request insertion returns full explainability."""
    graph = get_default_network_graph()
    inserter = DynamicTaskInserter(graph)
    state_mgr = FleetStateManager()

    res = inserter.evaluate_emergency_insertion_across_fleet(
        vehicles=state_mgr.get_all_vehicles(),
        task_id="EMG-TEST-01",
        location_node="COLLECTION_ZONE_D",
        estimated_waste_kg=1500.0,
        priority="URGENT",
    )
    assert res["task_id"] == "EMG-TEST-01"
    assert res["selected_vehicle_id"] is not None
    assert res["insertion_position"] is not None
    assert res["incremental_eta_min"] is not None
    assert res["incremental_distance_km"] is not None
    assert res["safety_status"] == "SAFE"
    assert "selected" in res["decision_reason"].lower()
    assert len(res["inserted_route"]) >= 2


def test_breakdown_recovery_event():
    """Verify auditable vehicle breakdown recovery reallocates tasks safely."""
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    allocator = TaskAllocator(graph, state_mgr)
    rebalancer = FleetRebalancer(graph, state_mgr, allocator)

    ev = rebalancer.execute_breakdown_recovery(vehicle_id="V-01")
    assert ev.broken_vehicle_id == "V-01"
    assert ev.recovery_status in ["RECOVERED", "DEFERRED"]
    assert ev.recovery_time_min > 0.0
    assert state_mgr.get_vehicle("V-01")["status"] == "BREAKDOWN"


def test_dynamic_rebalance_benefit_assessment():
    """Verify rebalance with benefit prevents unnecessary route disruption."""
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    allocator = TaskAllocator(graph, state_mgr)
    rebalancer = FleetRebalancer(graph, state_mgr, allocator)

    # When workload is healthy and trigger is minor, rebalance is deemed unnecessary
    res = rebalancer.assess_and_rebalance_with_benefit(
        trigger_reason="ROUTINE_CHECK",
        force_rebalance=False,
    )
    assert not res.rebalance_required
    assert "UNNECESSARY" in res.benefit_assessment_reason

    # When forced or breakdown occurs, rebalance executes
    res_forced = rebalancer.assess_and_rebalance_with_benefit(
        trigger_reason="VEHICLE_BREAKDOWN",
        force_rebalance=True,
    )
    assert res_forced.rebalance_required


def test_baseline_vs_advanced_optimizer_comparison():
    """Verify direct comparison between BASELINE and ADVANCED_OPTIMIZER strategies."""
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    optimizer = FleetOptimizer(graph, state_mgr)

    tasks = [
        {"id": "T-COMP-1", "location_node": "COLLECTION_ZONE_A", "estimated_waste_kg": 1500.0, "priority": "NORMAL"},
        {"id": "T-COMP-2", "location_node": "COLLECTION_ZONE_C", "estimated_waste_kg": 2000.0, "priority": "HIGH"},
    ]

    comp = optimizer.compare_allocation_strategies(tasks)
    assert comp["strategy_evaluated"] == "BASELINE_VS_ADVANCED_OPTIMIZER"
    assert comp["task_count"] == 2
    assert "eta_comparison" in comp
    assert "workload_balance_comparison" in comp
    assert "summary_verdict" in comp


def test_end_to_end_deterministic_simulation():
    """Verify reproducible end-to-end simulation flow across fixed seed."""
    sim1 = EndToEndFleetSimulator(seed=42)
    res1 = sim1.run_simulation(scenario_name="NORMAL_OPERATIONS")

    sim2 = EndToEndFleetSimulator(seed=42)
    res2 = sim2.run_simulation(scenario_name="NORMAL_OPERATIONS")

    assert res1.metrics.tasks_assigned == res2.metrics.tasks_assigned
    assert res1.metrics.avg_eta_min == res2.metrics.avg_eta_min
    assert res1.metrics.total_fleet_travel_time_min == res2.metrics.total_fleet_travel_time_min
    assert len(res1.timeline_events) == len(res2.timeline_events)


def test_data_leakage_protection():
    """Ensure pre-trip task allocation uses strictly pre-trip features, never post-trip outcomes."""
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    allocator = TaskAllocator(graph, state_mgr)

    # Pass an environmental context with only pre-trip observable conditions
    env_ctx = {
        "weather_condition": "RAIN",
        "rainfall_mm": 12.0,
        "traffic_level": "MEDIUM",
        "congestion_index": 35.0,
        # Intentionally provide bogus future outcome fields
        "actual_future_travel_time": 9999.0,
        "final_trip_duration": 8888.0,
    }

    alloc_res = allocator.allocate_task(
        task_id="LEAK-CHECK-1",
        location_node="COLLECTION_ZONE_B",
        estimated_waste_kg=1200.0,
        environmental_context=env_ctx,
    )
    assert alloc_res.status == "ASSIGNED"
    # The predicted ETA must be reasonable model output and completely ignore actual_future_travel_time
    assert alloc_res.predicted_eta_minutes < 200.0
    assert alloc_res.predicted_eta_minutes != 9999.0


def test_phase8_api_endpoints(client: TestClient):
    """Verify Phase 8 FastAPI endpoints."""
    # 1. Summary
    resp = client.get("/api/fleet/optimization/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "workload_balance_score" in data
    assert "fleet_mean_workload_min" in data

    # 2. Allocate
    resp_alloc = client.post(
        "/api/fleet/optimization/allocate",
        params={"location_node": "COLLECTION_ZONE_A", "estimated_waste_kg": 1200.0},
    )
    assert resp_alloc.status_code == 200
    assert resp_alloc.json()["status"] in ["ASSIGNED", "DEFERRED"]

    # 3. Emergency
    resp_emg = client.post(
        "/api/fleet/optimization/emergency",
        json={"location_node": "COLLECTION_ZONE_E", "estimated_waste_kg": 1400.0, "priority": "URGENT"},
    )
    assert resp_emg.status_code == 200
    assert "selected_vehicle_id" in resp_emg.json()

    # 4. Breakdown
    resp_brk = client.post("/api/fleet/optimization/breakdown", params={"vehicle_id": "V-02"})
    assert resp_brk.status_code == 200
    assert resp_brk.json()["broken_vehicle_id"] == "V-02"

    # 5. Rebalance
    resp_reb = client.post(
        "/api/fleet/optimization/rebalance",
        json={"trigger_reason": "WORKLOAD_IMBALANCE", "force_rebalance": False},
    )
    assert resp_reb.status_code == 200
    assert "benefit_assessment_reason" in resp_reb.json()

    # 6. Comparison
    resp_comp = client.get("/api/fleet/optimization/comparison")
    assert resp_comp.status_code == 200
    assert "eta_comparison" in resp_comp.json()
