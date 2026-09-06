"""Tests for Phase 7 Multi-Vehicle Fleet State Management and API Endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.fleet.fleet_state import FleetStateManager, DEFAULT_INITIAL_FLEET

client = TestClient(app)


def test_fleet_state_manager_initialization():
    mgr = FleetStateManager()
    vehicles = mgr.get_all_vehicles()
    assert len(vehicles) >= 5
    summary = mgr.get_fleet_summary()
    assert summary.total_vehicles >= 5
    assert summary.available >= 1
    assert 0.0 <= summary.mean_utilization_pct <= 100.0
    assert 0.0 <= summary.load_balance_score <= 1.0


def test_vehicle_overload_thresholds():
    mgr = FleetStateManager()
    v = mgr.get_vehicle("V-03")
    assert v is not None
    cap = v["capacity_kg"]

    # < 80%: NORMAL
    mgr.update_vehicle("V-03", current_payload_kg=cap * 0.5)
    assert mgr.get_vehicle("V-03")["overload_status"] == "NORMAL"

    # 80-95%: WARNING
    mgr.update_vehicle("V-03", current_payload_kg=cap * 0.85)
    assert mgr.get_vehicle("V-03")["overload_status"] == "WARNING"

    # 95-100%: CRITICAL
    mgr.update_vehicle("V-03", current_payload_kg=cap * 0.98)
    assert mgr.get_vehicle("V-03")["overload_status"] == "CRITICAL"

    # > 100%: OVERLOADED
    mgr.update_vehicle("V-03", current_payload_kg=cap * 1.05)
    assert mgr.get_vehicle("V-03")["overload_status"] == "OVERLOADED"
    assert mgr.get_vehicle("V-03")["status"] == "OVERLOADED"


def test_vehicle_breakdown_and_recovery():
    mgr = FleetStateManager()
    mgr.trigger_breakdown("V-04")
    assert mgr.get_vehicle("V-04")["status"] == "BREAKDOWN"

    mgr.recover_vehicle("V-04")
    assert mgr.get_vehicle("V-04")["status"] == "AVAILABLE"


def test_api_fleet_state_endpoints(client):
    response = client.get("/api/fleet/state")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "vehicles" in data
    assert data["summary"]["total_vehicles"] >= 5
    assert "disclaimer" in data

    resp_veh = client.get("/api/fleet/vehicles")
    assert resp_veh.status_code == 200
    veh_list = resp_veh.json()
    assert len(veh_list) >= 5


def test_api_fleet_tasks_and_creation(client):
    response = client.get("/api/fleet/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) >= 1

    create_resp = client.post(
        "/api/fleet/tasks",
        json={
            "location_node": "COLLECTION_ZONE_D",
            "estimated_waste_kg": 1350.0,
            "priority": "HIGH",
            "request_type": "SCHEDULED_COLLECTION",
            "notes": "Integration test task",
        },
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["location_node"] == "COLLECTION_ZONE_D"
    assert created["status"] == "PENDING"


def test_api_fleet_simulation_step(client):
    response = client.post(
        "/api/fleet/simulate-step",
        json={"step_duration_minutes": 10.0, "auto_rebalance_on_disruption": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["step_duration_minutes"] == 10.0
    assert "fleet_summary" in data
