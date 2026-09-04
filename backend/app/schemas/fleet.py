"""Pydantic schemas for Phase 7 Multi-Vehicle Fleet Coordination & Dynamic Task Allocation."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FleetVehicleState(BaseModel):
    vehicle_id: str
    vehicle_type: str = "COMPACTOR_HEAVY"
    capacity_kg: float
    current_payload_kg: float
    current_location: str
    driver_id: str
    driver_name: str
    driver_shift_remaining_min: float
    current_route: List[str] = Field(default_factory=list)
    assigned_task_ids: List[str] = Field(default_factory=list)
    status: str = "AVAILABLE"  # AVAILABLE, ASSIGNED, EN_ROUTE, AT_STOP, LOADING, RETURNING, OVERLOADED, BREAKDOWN, OFF_DUTY
    utilization_pct: float
    warning_level: str = "NORMAL"  # NORMAL, WARNING, CRITICAL, OVERLOADED
    is_operational: bool = True
    estimated_available_time_min: float = 0.0

    class Config:
        from_attributes = True


class FleetSummaryResponse(BaseModel):
    total_vehicles: int
    available_count: int
    assigned_count: int
    en_route_count: int
    overloaded_count: int
    breakdown_count: int
    off_duty_count: int
    average_utilization_pct: float
    utilization_variance: float
    vehicles: List[FleetVehicleState]
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic fleet coordination simulation. "
        "It does not represent live municipal fleet dispatch."
    )


class CollectionTaskCreate(BaseModel):
    location_node: str
    estimated_waste_kg: float = Field(default=1200.0, ge=100.0, le=10000.0)
    priority: str = "NORMAL"  # LOW, NORMAL, HIGH, URGENT
    request_type: str = "SCHEDULED_COLLECTION"  # SCHEDULED_COLLECTION, EMERGENCY_REQUEST
    deadline_minutes: Optional[float] = None
    notes: Optional[str] = None


class CollectionTaskResponse(BaseModel):
    id: str
    location_node: str
    estimated_waste_kg: float
    priority: str
    request_type: str
    status: str
    assigned_vehicle_id: Optional[str] = None
    assigned_driver_id: Optional[str] = None
    deadline_minutes: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskAssignRequest(BaseModel):
    target_vehicle_id: Optional[str] = None  # None = let fleet allocator choose optimal safe vehicle
    notes: Optional[str] = None


class EmergencyTaskRequest(BaseModel):
    location_node: str
    estimated_waste_kg: float = Field(default=1500.0, ge=100.0, le=10000.0)
    priority: str = "URGENT"
    deadline_minutes: Optional[float] = 60.0
    description: Optional[str] = None


class BreakdownRequest(BaseModel):
    reason: Optional[str] = "Hydraulic compactor pump failure"
    auto_rebalance: bool = True


class FleetRebalanceRequest(BaseModel):
    trigger_type: str = "MANUAL"
    notes: Optional[str] = None


class AllocationCandidateEvaluation(BaseModel):
    vehicle_id: str
    driver_id: str
    is_safe: bool
    safety_violations: List[str]
    projected_payload_kg: float
    projected_shift_minutes: float
    predicted_eta_minutes: float
    additional_distance_km: float
    allocation_score: float
    is_selected: bool
    rejection_reason: Optional[str] = None


class AllocationDecisionResponse(BaseModel):
    task_id: str
    selected_vehicle_id: Optional[str]
    selected_driver_id: Optional[str]
    selected_route: List[str]
    predicted_eta_minutes: float
    allocation_score: float
    selection_reason: str
    safety_status: str
    is_safe: bool
    action_type: str  # DIRECT_ASSIGNMENT, ROUTE_INSERTION, REBALANCED, DEFERRED
    candidate_evaluations: List[AllocationCandidateEvaluation]
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic fleet coordination simulation. "
        "It does not represent live municipal fleet dispatch."
    )


class FleetAuditEventResponse(BaseModel):
    id: str
    event_type: str
    task_id: Optional[str]
    previous_vehicle_id: Optional[str]
    new_vehicle_id: Optional[str]
    previous_route: List[str]
    new_route: List[str]
    predicted_eta_before: Optional[float]
    predicted_eta_after: Optional[float]
    distance_difference_km: float
    safety_result: str
    selected_eta_model: str
    reason: str
    timestamp: datetime

    class Config:
        from_attributes = True


class FleetSimulationStepResponse(BaseModel):
    active_vehicles_count: int
    steps_taken: List[Dict[str, Any]]
    completed_tasks: List[str]
    rebalancing_occurred: bool
    rebalancing_event_ids: List[str]
    fleet_summary: FleetSummaryResponse
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic fleet coordination simulation. "
        "It does not represent live municipal fleet dispatch."
    )


class FleetScenarioResult(BaseModel):
    scenario_name: str
    seed: int
    total_tasks: int
    tasks_assigned: int
    tasks_deferred: int
    assignment_success_rate_pct: float
    safe_assignment_rate_pct: float
    emergency_fulfillment_rate_pct: float
    breakdown_recovery_rate_pct: float
    mean_assignment_eta_min: float
    mean_fleet_utilization_pct: float
    fleet_load_balance_variance: float
    unsafe_assignments_prevented: int
    total_reassignments: int
    decision_rationale: str


class FleetExperimentSummary(BaseModel):
    total_runs: int
    scenarios_evaluated: List[str]
    task_assignment_success_rate_pct: float
    safe_assignment_rate_pct: float
    emergency_fulfillment_rate_pct: float
    breakdown_recovery_rate_pct: float
    mean_assignment_eta_min: float
    mean_fleet_travel_time_min: float
    mean_fleet_distance_km: float
    mean_fleet_utilization_pct: float
    fleet_load_balance_variance: float
    unsafe_assignments_prevented: int
    total_reassignments: int
    unassigned_task_rate_pct: float
    scenario_breakdown: Dict[str, Any]
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic fleet coordination simulation. "
        "It does not represent live municipal fleet dispatch."
    )
