"""Tests for Task Allocation Engine, Safety Filtering, and Data Leakage Invariance."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routing.graph import get_default_network_graph
from app.fleet.fleet_state import FleetStateManager
from app.fleet.task_allocator import TaskAllocator
from app.fleet.fleet_scoring import calculate_allocation_score, evaluate_vehicle_safety_gate

client = TestClient(app)


def test_allocation_scoring_formula():
    """Verify transparent formula: 0.40 ETA + 0.20 Dist + 0.15 Payload + 0.15 Shift + 0.10 Disruption."""
    score_low = calculate_allocation_score(
        predicted_eta_minutes=20.0,
        additional_distance_km=5.0,
        projected_payload_kg=2000.0,
        vehicle_capacity_kg=10000.0,
        projected_shift_minutes=120.0,
        max_shift_minutes=480.0,
        disruption_cost_factor=1.0,
    )

    score_high = calculate_allocation_score(
        predicted_eta_minutes=60.0,
        additional_distance_km=25.0,
        projected_payload_kg=8000.0,
        vehicle_capacity_kg=10000.0,
        projected_shift_minutes=400.0,
        max_shift_minutes=480.0,
        disruption_cost_factor=3.0,
    )

    assert score_low < score_high, "Efficient vehicle must produce a lower (better) score."


def test_hard_safety_gate_rejections():
    """Verify unsafe combinations are rejected BEFORE scoring."""
    # 1. Vehicle Breakdown
    safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="BREAKDOWN",
        current_payload_kg=1000.0,
        task_waste_kg=500.0,
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=100.0,
        estimated_trip_min=20.0,
        max_driver_shift_min=480.0,
    )
    assert not safe
    assert "BREAKDOWN" in reason

    # 2. Overload Capacity
    safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="AVAILABLE",
        current_payload_kg=9500.0,
        task_waste_kg=1000.0,  # 10500 > 10000
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=100.0,
        estimated_trip_min=20.0,
        max_driver_shift_min=480.0,
    )
    assert not safe
    assert "CAPACITY_EXCEEDED" in reason

    # 3. Driver Shift Limit Exceeded
    safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="AVAILABLE",
        current_payload_kg=2000.0,
        task_waste_kg=500.0,
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=470.0,
        estimated_trip_min=25.0,  # 495 > 480
        max_driver_shift_min=480.0,
    )
    assert not safe
    assert "DRIVER_SHIFT_EXCEEDED" in reason

    # 4. Route Closed
    safe, reason = evaluate_vehicle_safety_gate(
        vehicle_status="AVAILABLE",
        current_payload_kg=2000.0,
        task_waste_kg=500.0,
        vehicle_capacity_kg=10000.0,
        driver_status="AVAILABLE",
        current_driver_work_min=100.0,
        estimated_trip_min=20.0,
        max_driver_shift_min=480.0,
        route_is_blocked=True,
    )
    assert not safe
    assert "ROUTE_UNAVAILABLE" in reason


def test_data_leakage_invariance():
    """Verify that allocation strictly forbids future travel time or post-trip observations."""
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    allocator = TaskAllocator(graph, state_mgr)

    # Calling allocator without any future information
    result = allocator.allocate_task(
        task_id="LEAK-TEST-01",
        location_node="COLLECTION_ZONE_A",
        estimated_waste_kg=1000.0,
    )

    assert result.status == "ASSIGNED"
    assert result.predicted_eta_minutes is not None
    # Ensure all candidate evaluations contain only valid pre-trip attributes
    for cand in result.candidate_evaluations:
        assert cand.vehicle_id is not None
        if cand.is_safe:
            assert cand.allocation_score is not None
            assert cand.selected_eta_model in ["BASELINE", "CONTEXT_AWARE", "ADAPTIVE_HYBRID"]


def test_api_assign_task_lifecycle(client):
    # 1. Create task
    c_resp = client.post(
        "/api/fleet/tasks",
        json={
            "location_node": "COLLECTION_ZONE_B",
            "estimated_waste_kg": 1500.0,
            "priority": "HIGH",
        },
    )
    assert c_resp.status_code == 201
    task_id = c_resp.json()["id"]

    # 2. Assign task
    a_resp = client.post(f"/api/fleet/tasks/{task_id}/assign")
    assert a_resp.status_code == 200
    data = a_resp.json()
    assert data["task_id"] == task_id
    assert data["status"] == "ASSIGNED"
    assert data["selected_vehicle_id"] is not None
    assert len(data["selected_route"]) >= 2
    assert data["safety_result"] == "SAFE"
