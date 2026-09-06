"""Tests for Fleet Rebalancing Engine, Vehicle Breakdown, and Audit Events."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routing.graph import get_default_network_graph
from app.fleet.fleet_state import FleetStateManager
from app.fleet.task_allocator import TaskAllocator
from app.fleet.fleet_rebalancer import FleetRebalancer

client = TestClient(app)


def test_breakdown_rebalancing_logic():
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    allocator = TaskAllocator(graph, state_mgr)
    rebalancer = FleetRebalancer(graph, state_mgr, allocator)

    # Put V-01 in BREAKDOWN with an active task
    state_mgr.trigger_breakdown("V-01")
    state_mgr.update_vehicle("V-01", current_task_id="TASK-BREAK-TEST", current_route=["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "LANDFILL_MAIN"])

    res = rebalancer.rebalance_fleet(
        trigger_reason="VEHICLE_BREAKDOWN",
        affected_vehicle_id="V-01",
    )

    assert res.rebalance_triggered
    assert res.affected_tasks_count >= 1
    assert res.reassigned_tasks_count >= 1

    # Verify V-01 was NOT selected as the new vehicle
    for ev in res.audit_events:
        assert ev.new_vehicle_id != "V-01", "Broken vehicle must NEVER be reassigned tasks."
        assert ev.safety_result == "SAFE"


def test_api_breakdown_and_recovery(client):
    # 1. Trigger breakdown on V-02
    resp_bd = client.post(
        "/api/fleet/vehicles/V-02/breakdown",
        json={"reason": "TRANSMISSION_FAILURE"},
    )
    assert resp_bd.status_code == 200
    bd_data = resp_bd.json()
    assert bd_data["vehicle_id"] == "V-02"
    assert bd_data["new_status"] == "BREAKDOWN"

    # Verify vehicle state reflects breakdown
    state_resp = client.get("/api/fleet/state")
    v2 = next(v for v in state_resp.json()["vehicles"] if v["vehicle_id"] == "V-02")
    assert v2["status"] == "BREAKDOWN"

    # 2. Recover V-02
    resp_rec = client.post("/api/fleet/vehicles/V-02/recover")
    assert resp_rec.status_code == 200
    assert resp_rec.json()["status"] == "AVAILABLE"

    # Verify state is restored
    state_resp2 = client.get("/api/fleet/state")
    v2_rec = next(v for v in state_resp2.json()["vehicles"] if v["vehicle_id"] == "V-02")
    assert v2_rec["status"] == "AVAILABLE"


def test_api_rebalance_endpoint(client):
    response = client.post(
        "/api/fleet/rebalance",
        json={"trigger_reason": "MANUAL_DISPATCH_REBALANCE"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["rebalance_triggered"]


def test_api_fleet_audit_events(client):
    response = client.get("/api/fleet/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    if len(events) > 0:
        ev = events[0]
        assert "event_type" in ev
        assert "safety_result" in ev
        assert "reason" in ev
