"""Automated test suite for Phase 6 Dynamic Routing & Real-Time Rerouting Engine."""
import pytest
from app.routing.graph import RoadNetworkGraph, get_default_network_graph
from app.routing.route_candidates import CandidateRouteGenerator
from app.routing.route_scoring import RouteSafetyAndScoringEngine
from app.routing.rerouting import DynamicReroutingEngine
from app.services.rerouting_experiment_service import ReroutingExperimentService


def test_road_network_graph_initialization():
    """Verify default graph is populated with all 14 nodes and bidirectional connectivity."""
    graph = get_default_network_graph()
    assert len(graph.nodes) == 14
    assert "DEPOT_CENTRAL" in graph.nodes
    assert "LANDFILL_MAIN" in graph.nodes
    assert len(graph.edges) > 0


def test_dijkstra_shortest_path_normal_and_blocked():
    """Verify Dijkstra algorithm calculates correct path and avoids blocked edges."""
    graph = get_default_network_graph()

    # Normal shortest path
    res = graph.dijkstra_shortest_path("COLLECTION_ZONE_A", "COLLECTION_ZONE_B", weight_mode="distance")
    assert res is not None
    path, cost = res
    assert path[0] == "COLLECTION_ZONE_A"
    assert path[-1] == "COLLECTION_ZONE_B"
    assert cost > 0

    # Block direct edge
    graph.set_edge_blocked("COLLECTION_ZONE_A", "COLLECTION_ZONE_B", is_blocked=True)
    res_blocked = graph.dijkstra_shortest_path("COLLECTION_ZONE_A", "COLLECTION_ZONE_B", weight_mode="time")
    assert res_blocked is not None
    detour_path, detour_cost = res_blocked
    # Detour must not use the direct blocked edge
    assert detour_path != ["COLLECTION_ZONE_A", "COLLECTION_ZONE_B"]
    assert "COLLECTION_ZONE_A" in detour_path
    assert "COLLECTION_ZONE_B" in detour_path


def test_yen_k_shortest_paths():
    """Verify Yen's algorithm finds multiple distinct loopless paths."""
    graph = get_default_network_graph()
    k_paths = graph.yen_k_shortest_paths("DEPOT_CENTRAL", "LANDFILL_MAIN", k=3, weight_mode="time")
    assert len(k_paths) >= 2
    # Ensure all paths reach destination
    for p, cost in k_paths:
        assert p[0] == "DEPOT_CENTRAL"
        assert p[-1] == "LANDFILL_MAIN"
        assert cost > 0


def test_candidate_route_generator_strategies():
    """Verify candidate generator produces paths for all required strategies."""
    graph = get_default_network_graph()
    generator = CandidateRouteGenerator(graph)

    candidates = generator.generate_candidates(
        current_node="DEPOT_CENTRAL",
        remaining_stops=["COLLECTION_ZONE_A", "COLLECTION_ZONE_B"],
        destination_node="LANDFILL_MAIN",
    )

    assert len(candidates) >= 3
    strategies = [c.strategy for c in candidates]
    assert "SHORTEST_PATH" in strategies
    assert "BALANCED" in strategies


def test_route_safety_gate_capacity_violation():
    """Verify that exceeding vehicle payload capacity marks candidate unsafe and permanently rejects it."""
    graph = get_default_network_graph()
    scoring = RouteSafetyAndScoringEngine(graph)

    # Payload 9000 kg > Capacity 8000 kg
    is_safe, violations = scoring.evaluate_safety(
        candidate_path=["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "LANDFILL_MAIN"],
        current_payload_kg=5000.0,
        vehicle_capacity_kg=8000.0,
        expected_waste_kg=4000.0,
        elapsed_time_minutes=30.0,
        predicted_trip_minutes=40.0,
        max_shift_hours=4.0,
    )

    assert not is_safe
    assert len(violations) > 0
    assert "Payload capacity exceeded" in violations[0]


def test_route_safety_gate_shift_hours_violation():
    """Verify that exceeding driver maximum shift hours marks candidate unsafe."""
    graph = get_default_network_graph()
    scoring = RouteSafetyAndScoringEngine(graph)

    # 220 min elapsed + 60 min predicted = 280 min > 240 min limit (4.0 hrs)
    is_safe, violations = scoring.evaluate_safety(
        candidate_path=["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "LANDFILL_MAIN"],
        current_payload_kg=2000.0,
        vehicle_capacity_kg=8000.0,
        expected_waste_kg=1000.0,
        elapsed_time_minutes=220.0,
        predicted_trip_minutes=60.0,
        max_shift_hours=4.0,
    )

    assert not is_safe
    assert any("shift time exceeded" in v for v in violations)


def test_route_scoring_formula_and_winner_selection():
    """Verify multi-objective scoring formula selects the lowest score among safe routes."""
    graph = get_default_network_graph()
    scoring = RouteSafetyAndScoringEngine(graph)

    candidates_raw = [
        {
            "strategy": "ROUTE_A",
            "path": ["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "LANDFILL_MAIN"],
            "total_distance_km": 10.0,
            "hybrid_eta_minutes": 25.0,
            "baseline_eta_minutes": 24.0,
            "eta_uncertainty_minutes": 1.5,
        },
        {
            "strategy": "ROUTE_B",
            "path": ["DEPOT_CENTRAL", "COLLECTION_ZONE_B", "LANDFILL_MAIN"],
            "total_distance_km": 15.0,
            "hybrid_eta_minutes": 45.0,
            "baseline_eta_minutes": 36.0,
            "eta_uncertainty_minutes": 3.0,
        },
    ]

    scored = scoring.score_candidates(
        candidates_raw=candidates_raw,
        current_payload_kg=2000.0,
        vehicle_capacity_kg=8000.0,
        expected_waste_kg=1000.0,
        elapsed_time_minutes=10.0,
        max_shift_hours=4.0,
    )

    assert len(scored) == 2
    assert scored[0].is_selected is True
    assert scored[1].is_selected is False
    assert scored[0].optimization_score < scored[1].optimization_score


def test_api_routing_graph_endpoint(client):
    """Verify GET /api/routing/graph returns 14 nodes and disclaimer."""
    response = client.get("/api/routing/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 14
    assert "SIMULATION DISCLAIMER" in data["disclaimer"]


def test_api_active_trip_lifecycle_and_rerouting(client):
    """Verify active trip creation, step simulation, disruption injection, and reroute execution."""
    # 1. Create Trip
    create_payload = {
        "vehicle_id": "V-01",
        "driver_id": "EMP-001",
        "origin_node": "DEPOT_CENTRAL",
        "destination_node": "LANDFILL_MAIN",
        "initial_stops": ["COLLECTION_ZONE_A", "COLLECTION_ZONE_B"],
        "vehicle_capacity_kg": 8000.0,
        "initial_payload_kg": 1000.0,
        "max_shift_hours": 4.0,
    }
    create_res = client.post("/api/routing/trips", json=create_payload)
    assert create_res.status_code == 201
    trip = create_res.json()
    trip_id = trip["id"]
    assert trip["current_node"] == "DEPOT_CENTRAL"
    assert trip["status"] == "IN_PROGRESS"

    # 2. Get Trip
    get_res = client.get(f"/api/routing/trips/{trip_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == trip_id

    # 3. Step Simulation forward
    step_res = client.post(f"/api/routing/trips/{trip_id}/step", json={"step_duration_minutes": 10.0})
    assert step_res.status_code == 200
    step_data = step_res.json()
    assert step_data["step_taken_from"] == "DEPOT_CENTRAL"
    assert step_data["trip"]["current_node"] != "DEPOT_CENTRAL"

    # 4. Inject Disruption
    disr_payload = {
        "disruption_type": "ROAD_CLOSURE",
        "target_edge": ["COLLECTION_ZONE_B", "COLLECTION_ZONE_C"],
        "severity": 2.0,
        "description": "Emergency burst pipe closure",
    }
    disr_res = client.post(f"/api/routing/trips/{trip_id}/inject-disruption", json=disr_payload)
    assert disr_res.status_code == 200

    # 5. Execute Reroute
    reroute_res = client.post(f"/api/routing/trips/{trip_id}/reroute", json={"force_reroute": True})
    assert reroute_res.status_code == 200
    reroute_data = reroute_res.json()
    assert "all_candidates" in reroute_data
    assert len(reroute_data["all_candidates"]) > 0
    assert reroute_data["trip"]["reroute_count"] >= 1


def test_rerouting_experiment_service_benchmark():
    """Verify Phase 6 benchmark service runs all 7 scenarios across 5 seeds."""
    service = ReroutingExperimentService()
    summary = service.run_full_benchmark()
    assert summary["total_runs"] == 35
    assert len(summary["scenarios_evaluated"]) == 7
    assert summary["mean_time_saved_min"] >= 0.0
    assert summary["overall_safety_rate_dynamic_pct"] >= summary["overall_safety_rate_static_pct"]
