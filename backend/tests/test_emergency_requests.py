"""Tests for Dynamic Task Insertion and Emergency Waste Requests."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routing.graph import get_default_network_graph
from app.fleet.task_insertion import DynamicTaskInserter

client = TestClient(app)


def test_dynamic_route_insertion_success():
    graph = get_default_network_graph()
    inserter = DynamicTaskInserter(graph)

    # Route: DEPOT_CENTRAL -> COLLECTION_ZONE_A -> LANDFILL_MAIN
    # Insert: COLLECTION_ZONE_B
    res = inserter.evaluate_route_insertions(
        current_path=["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "LANDFILL_MAIN"],
        task_node="COLLECTION_ZONE_B",
        task_waste_kg=1000.0,
        current_payload_kg=2000.0,
        vehicle_capacity_kg=10000.0,
        driver_current_work_min=100.0,
        driver_max_shift_min=480.0,
    )

    assert res["success"]
    assert "best_insertion" in res
    best = res["best_insertion"]
    assert best["is_safe"]
    assert "COLLECTION_ZONE_B" in best["inserted_path"]
    assert best["additional_distance_km"] >= 0.0


def test_dynamic_route_insertion_capacity_rejection():
    graph = get_default_network_graph()
    inserter = DynamicTaskInserter(graph)

    # Vehicle near capacity (9500kg of 10000kg) + 1500kg task -> Unsafe
    res = inserter.evaluate_route_insertions(
        current_path=["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "LANDFILL_MAIN"],
        task_node="COLLECTION_ZONE_B",
        task_waste_kg=1500.0,
        current_payload_kg=9500.0,
        vehicle_capacity_kg=10000.0,
        driver_current_work_min=100.0,
        driver_max_shift_min=480.0,
    )

    assert not res["success"]
    assert res["rejection_reason"] == "NO_SAFE_INSERTION"


def test_dynamic_route_insertion_road_blockage_rejection():
    graph = get_default_network_graph()
    # Block access to zone E
    graph.set_edge_blocked("INTERSECTION_CENTRAL_1", "COLLECTION_ZONE_E", is_blocked=True)
    graph.set_edge_blocked("COLLECTION_ZONE_E", "INTERSECTION_NORTH_1", is_blocked=True)

    inserter = DynamicTaskInserter(graph)
    res = inserter.evaluate_route_insertions(
        current_path=["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "LANDFILL_MAIN"],
        task_node="COLLECTION_ZONE_E",
        task_waste_kg=1000.0,
        current_payload_kg=1000.0,
        vehicle_capacity_kg=10000.0,
        driver_current_work_min=100.0,
        driver_max_shift_min=480.0,
    )

    assert not res["success"]


def test_api_emergency_request_handling(client):
    # 1. Create emergency task
    c_resp = client.post(
        "/api/fleet/tasks",
        json={
            "location_node": "COLLECTION_ZONE_E",
            "estimated_waste_kg": 1500.0,
            "priority": "URGENT",
            "request_type": "EMERGENCY_REQUEST",
            "deadline_minutes": 30.0,
        },
    )
    assert c_resp.status_code == 201
    task_id = c_resp.json()["id"]

    # 2. Trigger emergency allocation
    emg_resp = client.post(f"/api/fleet/tasks/{task_id}/emergency")
    assert emg_resp.status_code == 200
    data = emg_resp.json()
    assert data["task_id"] == task_id
    assert data["status"] in ["ASSIGNED", "DEFERRED"]
    assert "candidate_evaluations" in data
