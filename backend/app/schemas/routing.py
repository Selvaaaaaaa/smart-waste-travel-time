"""Pydantic schemas for Phase 6 Dynamic Routing and Real-time Optimization Engine."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LatLng(BaseModel):
    lat: float
    lng: float


class GraphNode(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    node_type: str  # depot, collection, transfer_station, landfill, intersection


class GraphEdge(BaseModel):
    source: str
    target: str
    distance_km: float
    speed_limit_kmh: float
    base_traversal_time_min: float
    current_traversal_time_min: float
    is_blocked: bool = False
    congestion_factor: float = 1.0
    weather_penalty_factor: float = 1.0
    road_type: str = "arterial"


class NetworkGraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal routing or live GPS data."
    )


class ActiveTripCreate(BaseModel):
    vehicle_id: str
    driver_id: str
    origin_node: str = "DEPOT_CENTRAL"
    destination_node: str = "LANDFILL_MAIN"
    initial_stops: List[str] = Field(
        default_factory=lambda: ["COLLECTION_ZONE_A", "COLLECTION_ZONE_B", "COLLECTION_ZONE_C"]
    )
    vehicle_capacity_kg: float = 8000.0
    initial_payload_kg: float = 0.0
    max_shift_hours: float = 8.0
    notes: Optional[str] = None


class ActiveTripResponse(BaseModel):
    id: str
    vehicle_id: str
    driver_id: str
    origin_node: str
    destination_node: str
    current_node: str
    visited_nodes: List[str]
    remaining_stops: List[str]
    current_path: List[str]
    current_payload_kg: float
    vehicle_capacity_kg: float
    elapsed_time_minutes: float
    max_shift_hours: float
    distance_traveled_km: float
    current_eta_minutes: float
    baseline_eta_minutes: float
    hybrid_eta_minutes: float
    eta_uncertainty_minutes: float
    status: str
    active_disruptions: List[Dict[str, Any]]
    reroute_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DisruptionInjectRequest(BaseModel):
    disruption_type: str  # ROAD_CLOSURE, TRAFFIC_SPIKE, HEAVY_RAIN, EVENT_BLOCK, HIGH_WASTE
    target_edge: Optional[List[str]] = None  # e.g., ["COLLECTION_ZONE_A", "COLLECTION_ZONE_B"]
    target_node: Optional[str] = None
    severity: float = Field(default=1.0, ge=0.0, le=5.0)
    additional_waste_kg: float = 0.0
    description: Optional[str] = None


class RouteCandidateResponse(BaseModel):
    id: Optional[str] = None
    strategy: str
    path: List[str]
    path_coordinates: List[LatLng]
    total_distance_km: float
    predicted_eta_minutes: float
    baseline_eta_minutes: float
    hybrid_eta_minutes: float
    eta_uncertainty_minutes: float
    safety_valid: bool
    safety_violations: List[str]
    optimization_score: float
    is_selected: bool
    rejection_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True



class RerouteRequest(BaseModel):
    candidate_strategies: Optional[List[str]] = None  # None = all default 5 strategies
    force_reroute: bool = False
    notes: Optional[str] = None


class ReroutingEventResponse(BaseModel):
    id: str
    trip_id: str
    trigger_type: str
    trigger_details: Dict[str, Any]
    previous_path: List[str]
    new_path: List[str]
    previous_eta_minutes: float
    new_eta_minutes: float
    time_saved_minutes: float
    distance_difference_km: float
    selected_candidate_id: Optional[str]
    candidate_count: int
    decision_rationale: str
    timestamp: datetime

    class Config:
        from_attributes = True


class RerouteResponse(BaseModel):
    trip_id: str
    reroute_executed: bool
    trigger_type: str
    decision_rationale: str
    selected_candidate: Optional[RouteCandidateResponse]
    all_candidates: List[RouteCandidateResponse]
    event: Optional[ReroutingEventResponse]
    trip: ActiveTripResponse
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal routing or live GPS data."
    )


class SimulateStepRequest(BaseModel):
    step_duration_minutes: float = 10.0
    auto_reroute_on_disruption: bool = True


class SimulationStepResponse(BaseModel):
    trip: ActiveTripResponse
    step_taken_from: str
    step_taken_to: str
    segment_distance_km: float
    segment_time_minutes: float
    waste_collected_kg: float
    trip_completed: bool
    reroute_occurred: bool
    reroute_event: Optional[ReroutingEventResponse] = None
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal routing or live GPS data."
    )


class RoutingScenarioResult(BaseModel):
    scenario_name: str
    seed: int
    static_baseline_travel_time_min: float
    static_baseline_distance_km: float
    static_baseline_success: bool
    dynamic_rerouted_travel_time_min: float
    dynamic_rerouted_distance_km: float
    dynamic_rerouted_success: bool
    time_saved_minutes: float
    pct_time_saved: float
    distance_penalty_km: float
    reroute_count: int
    safety_violations_prevented: int
    decision_rationale: str


class RoutingExperimentSummary(BaseModel):
    total_runs: int
    scenarios_evaluated: List[str]
    mean_time_saved_min: float
    mean_pct_time_saved: float
    overall_safety_rate_static_pct: float
    overall_safety_rate_dynamic_pct: float
    disruption_adaptation_effectiveness_pct: float
    scenario_breakdown: Dict[str, Dict[str, Any]]
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal routing or live GPS data."
    )
