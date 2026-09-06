"""Comprehensive tests for Phase 9: Real-Time IoT Telemetry, Sensor Fusion & RBAC."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.routing.graph import get_default_network_graph
from app.fleet.fleet_state import FleetStateManager
from app.telemetry.validation import TelemetryQualityValidator, classify_bin_fill_level
from app.telemetry.generator import TelemetryGenerator, haversine_distance_meters
from app.telemetry.ingestion import TelemetryIngestionService
from app.telemetry.fusion import SensorFusionService
from app.telemetry.depots import depot_service
from app.telemetry.auth import AuthService, ROLE_PERMISSIONS
from app.telemetry.audit import audit_service
from app.telemetry.phase9_experiments import Phase9ExperimentRunner


@pytest.fixture
def client():
    return TestClient(app)


# 1. GPS Telemetry Validation Tests
def test_gps_telemetry_validation():
    # Valid message
    valid_payload = {
        "vehicle_id": "V-01",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "speed_kmh": 35.0,
        "heading": 90.0,
        "telemetry_sequence": 1,
    }
    is_valid, reason, model = TelemetryQualityValidator.validate_gps_telemetry(valid_payload)
    assert is_valid is True
    assert model.vehicle_id == "V-01"
    assert model.speed_kmh == 35.0

    # Negative speed rejected
    bad_speed = dict(valid_payload, speed_kmh=-10.0)
    is_valid, reason, _ = TelemetryQualityValidator.validate_gps_telemetry(bad_speed)
    assert is_valid is False
    assert "Speed cannot be negative" in reason

    # Out of bounds coordinates rejected
    bad_lat = dict(valid_payload, latitude=120.0)
    is_valid, reason, _ = TelemetryQualityValidator.validate_gps_telemetry(bad_lat)
    assert is_valid is False
    assert "Latitude must be between -90 and 90" in reason

    # Impossible speed (> 140 km/h) rejected
    bad_speed_high = dict(valid_payload, speed_kmh=180.0)
    is_valid, reason, _ = TelemetryQualityValidator.validate_gps_telemetry(bad_speed_high)
    assert is_valid is False
    assert "Impossible speed" in reason


# 2. Smart Bin Telemetry Validation & Classification Tests
def test_bin_telemetry_validation_and_classification():
    assert classify_bin_fill_level(25.0) == "NORMAL"
    assert classify_bin_fill_level(65.0) == "MEDIUM"
    assert classify_bin_fill_level(82.0) == "HIGH"
    assert classify_bin_fill_level(95.0) == "CRITICAL"

    valid_bin = {
        "bin_id": "BIN-TEST-01",
        "location_node": "COLLECTION_ZONE_A",
        "fill_level_percent": 92.5,
        "estimated_waste_kg": 925.0,
        "sensor_battery_percent": 88.0,
        "sequence_number": 1,
    }
    is_valid, reason, model = TelemetryQualityValidator.validate_bin_telemetry(valid_bin)
    assert is_valid is True
    assert model.status_classification == "CRITICAL"
    assert model.sensor_status == "CRITICAL"

    # Out of bounds fill level rejected
    bad_fill = dict(valid_bin, fill_level_percent=125.0)
    is_valid, reason, _ = TelemetryQualityValidator.validate_bin_telemetry(bad_fill)
    assert is_valid is False
    assert "out of bounds" in reason


# 3. Duplicate and Stale Detection Tests
def test_duplicate_and_stale_telemetry_detection():
    ingestion = TelemetryIngestionService()
    now = datetime.utcnow()

    payload_1 = {
        "vehicle_id": "V-TEST",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "speed_kmh": 30.0,
        "telemetry_sequence": 1,
        "timestamp": now.isoformat(),
    }
    payload_dup = {
        "vehicle_id": "V-TEST",
        "latitude": 40.7130,
        "longitude": -74.0065,
        "speed_kmh": 32.0,
        "telemetry_sequence": 1,  # Same sequence number
        "timestamp": now.isoformat(),
    }

    acc1, health1, _ = ingestion.ingest_vehicle_gps(payload_1)
    assert acc1 is True
    assert health1 == "TELEMETRY_HEALTHY"

    acc2, health2, _ = ingestion.ingest_vehicle_gps(payload_dup)
    assert acc2 is True
    assert health2 == "TELEMETRY_DUPLICATE"

    # Stale telemetry test
    stale_time = now - timedelta(seconds=60)
    payload_stale = {
        "vehicle_id": "V-STALE",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "speed_kmh": 30.0,
        "telemetry_sequence": 1,
        "timestamp": stale_time.isoformat(),
    }
    acc3, health3, _ = ingestion.ingest_vehicle_gps(payload_stale)
    assert acc3 is True
    assert health3 == "TELEMETRY_STALE"


# 4. Route Deviation Detection Test
def test_route_deviation_detection():
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    ingestion = TelemetryIngestionService()
    fusion = SensorFusionService(graph, state_mgr, ingestion)

    # Planned route: DEPOT_CENTRAL -> COLLECTION_ZONE_A
    route = ["DEPOT_CENTRAL", "COLLECTION_ZONE_A"]
    depot_coord = graph.nodes["DEPOT_CENTRAL"]

    # Point on route
    is_dev_on, dist_on = fusion.calculate_route_deviation(depot_coord["lat"], depot_coord["lng"], route)
    assert is_dev_on is False
    assert dist_on < 10.0

    # Point heavily deviated (~500m off)
    is_dev_off, dist_off = fusion.calculate_route_deviation(depot_coord["lat"] + 0.005, depot_coord["lng"] + 0.005, route)
    assert is_dev_off is True
    assert dist_off > 100.0


# 5. Critical Bin Emergency Request Generation Test
def test_critical_bin_emergency_generation():
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    ingestion = TelemetryIngestionService()
    fusion = SensorFusionService(graph, state_mgr, ingestion)

    # Ingest a critical bin at 95%
    crit_bin_payload = {
        "bin_id": "BIN-CRIT-99",
        "location_node": "COLLECTION_ZONE_C",
        "fill_level_percent": 95.0,
        "estimated_waste_kg": 950.0,
        "sensor_battery_percent": 90.0,
        "sequence_number": 1,
    }
    ingestion.ingest_bin_sensor(crit_bin_payload)

    emergencies = fusion.evaluate_critical_bins_and_generate_requests()
    assert len(emergencies) == 1
    assert emergencies[0]["bin_id"] == "BIN-CRIT-99"
    assert emergencies[0]["priority"] == "URGENT"
    assert "CRITICAL_BIN_FILL_LEVEL" in emergencies[0]["reason"]


# 6. Real-time ETA Recalculation & Data Leakage Protection
def test_realtime_eta_updates_and_data_leakage():
    graph = get_default_network_graph()
    state_mgr = FleetStateManager()
    ingestion = TelemetryIngestionService()
    fusion = SensorFusionService(graph, state_mgr, ingestion)

    route = ["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "COLLECTION_ZONE_B", "LANDFILL_MAIN"]
    eta_clear = fusion.recalculate_realtime_eta("V-01", 40.7128, -74.006, route, weather="CLEAR", traffic="NORMAL")
    eta_heavy = fusion.recalculate_realtime_eta("V-01", 40.7128, -74.006, route, weather="HEAVY_RAIN", traffic="HEAVY")

    assert eta_clear > 0.0
    assert eta_heavy > eta_clear  # Adverse conditions increase estimated ETA

    # Data leakage check: Verify that post-trip actual arrival timestamp is never required
    assert "actual_arrival_time" not in fusion.__dict__


# 7. Multi-Depot Architecture Test
def test_multi_depot_architecture():
    depots = depot_service.get_all_depots()
    assert len(depots) >= 3
    depot_ids = [d.depot_id for d in depots]
    assert "DEPOT_CENTRAL" in depot_ids
    assert "DEPOT_NORTH" in depot_ids
    assert "DEPOT_SOUTH" in depot_ids

    # Nearest depot query
    near = depot_service.find_nearest_depot(40.7128, -74.0060)
    assert near.depot_id == "DEPOT_CENTRAL"


# 8. Authentication and RBAC Tests
def test_authentication_and_rbac():
    # Valid login
    user = AuthService.authenticate_user("dispatcher", "demo123")
    assert user is not None
    assert user.role == "DISPATCHER"
    assert "assign_tasks" in user.permissions

    # JWT generation & decoding
    token = AuthService.create_access_token(user)
    decoded = AuthService.decode_token(token)
    assert decoded is not None
    assert decoded.username == "dispatcher"
    assert decoded.role == "DISPATCHER"

    # Invalid login rejected
    bad_user = AuthService.authenticate_user("dispatcher", "wrong_password")
    assert bad_user is None


# 9. Operational Audit Logging Test
def test_audit_logging():
    event = audit_service.log_event(
        actor="dispatcher",
        role="DISPATCHER",
        action="TASK_ASSIGNED",
        entity_type="COLLECTION_TASK",
        entity_id="TSK-01",
        reason="Optimal vehicle selected",
        result="SUCCESS",
    )
    assert event.event_id.startswith("AUD-")
    events = audit_service.get_events(limit=5)
    assert any(e.event_id == event.event_id for e in events)


# 10. Scalability Benchmark Execution Test
def test_scalability_benchmark_execution():
    runner = Phase9ExperimentRunner()
    res = runner.run_scalability_benchmark()
    assert len(res.benchmarks) == 3  # 6, 20, 50 vehicles
    v50 = [b for b in res.benchmarks if b.vehicle_count == 50][0]
    assert v50.telemetry_messages_processed == 50 * 50
    assert v50.average_processing_latency_ms < 5.0
    assert v50.status == "PASS"


# 11. REST API Endpoints Test
def test_telemetry_api_endpoints(client):
    # GET health
    res_health = client.get("/api/telemetry/health")
    assert res_health.status_code == 200
    assert "telemetry_health_rate_pct" in res_health.json()

    # GET vehicles telemetry
    res_veh = client.get("/api/telemetry/vehicles")
    assert res_veh.status_code == 200

    # GET bins telemetry
    res_bins = client.get("/api/telemetry/bins")
    assert res_bins.status_code == 200

    # GET fused fleet state
    res_fleet = client.get("/api/realtime/fleet")
    assert res_fleet.status_code == 200
    assert "vehicles" in res_fleet.json()

    # GET depots
    res_depots = client.get("/api/realtime/depots")
    assert res_depots.status_code == 200
    assert len(res_depots.json()) >= 3

    # POST auth login
    res_login = client.post("/api/auth/login", json={"username": "dispatcher", "password": "demo123"})
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()
