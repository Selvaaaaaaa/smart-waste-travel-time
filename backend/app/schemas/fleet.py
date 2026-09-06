"""Pydantic schemas for Phase 7 Multi-Vehicle Fleet Coordination & Dynamic Task Allocation."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VehicleFleetItem(BaseModel):
    vehicle_id: str
    vehicle_code: str
    vehicle_type: str
    capacity_kg: float
    current_payload_kg: float
    current_location: str
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    driver_shift_remaining_min: float
    current_route: List[str] = Field(default_factory=list)
    current_task_id: Optional[str] = None
    status: str  # AVAILABLE, ASSIGNED, EN_ROUTE, AT_STOP, LOADING, RETURNING, OVERLOADED, BREAKDOWN, OFF_DUTY
    overload_status: str  # NORMAL, WARNING, CRITICAL, OVERLOADED
    utilization_pct: float
    safety_status: str
    estimated_available_time_min: float
    assigned_tasks_count: int = 0
    completed_tasks_count: int = 0
    pending_tasks_count: int = 0
    estimated_workload_minutes: float = 0.0
    route_distance_km: float = 0.0
    workload_deviation_minutes: float = 0.0


class FleetSummary(BaseModel):
    total_vehicles: int
    available: int
    assigned: int
    en_route: int
    overloaded: int
    breakdown: int
    off_duty: int
    mean_utilization_pct: float
    utilization_variance: float
    load_balance_score: float


class FleetStateResponse(BaseModel):
    summary: FleetSummary
    vehicles: List[VehicleFleetItem]
    active_tasks_count: int
    pending_tasks_count: int
    timestamp: datetime
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class CollectionTaskCreate(BaseModel):
    location_node: str
    estimated_waste_kg: float = Field(default=1000.0, ge=10.0, le=15000.0)
    priority: str = Field(default="NORMAL")  # LOW, NORMAL, HIGH, URGENT
    request_type: str = Field(default="SCHEDULED_COLLECTION")  # SCHEDULED_COLLECTION, EMERGENCY_REQUEST
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
    predicted_eta_minutes: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CandidateVehicleEvaluation(BaseModel):
    vehicle_id: str
    vehicle_code: str
    is_safe: bool
    rejection_reason: Optional[str] = None
    allocation_score: Optional[float] = None
    predicted_eta_min: Optional[float] = None
    additional_distance_km: Optional[float] = None
    projected_payload_kg: float
    projected_shift_minutes: float
    selected_eta_model: str
    prediction_spread_min: float


class TaskAssignResponse(BaseModel):
    task_id: str
    status: str  # ASSIGNED, DEFERRED, FAILED
    selected_vehicle_id: Optional[str] = None
    selected_driver_id: Optional[str] = None
    selected_route: List[str] = Field(default_factory=list)
    predicted_eta_minutes: Optional[float] = None
    allocation_score: Optional[float] = None
    selection_reason: str
    candidate_evaluations: List[CandidateVehicleEvaluation]
    safety_result: str
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class FleetAuditEventResponse(BaseModel):
    id: str
    event_type: str
    task_id: Optional[str] = None
    previous_vehicle_id: Optional[str] = None
    new_vehicle_id: Optional[str] = None
    previous_route: List[str] = Field(default_factory=list)
    new_route: List[str] = Field(default_factory=list)
    predicted_eta_before: Optional[float] = None
    predicted_eta_after: Optional[float] = None
    distance_difference_km: float = 0.0
    safety_result: str
    selected_eta_model: str
    reason: str
    timestamp: datetime

    class Config:
        from_attributes = True


class FleetRebalanceRequest(BaseModel):
    trigger_reason: str = Field(default="MANUAL_REBALANCE")
    affected_vehicle_id: Optional[str] = None
    notes: Optional[str] = None


class FleetRebalanceResponse(BaseModel):
    rebalance_triggered: bool
    trigger_reason: str
    affected_tasks_count: int
    reassigned_tasks_count: int
    deferred_tasks_count: int
    details: List[Dict[str, Any]] = Field(default_factory=list)
    audit_events: List[FleetAuditEventResponse] = Field(default_factory=list)
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class VehicleBreakdownRequest(BaseModel):
    reason: str = Field(default="MECHANICAL_FAILURE")


class VehicleBreakdownResponse(BaseModel):
    vehicle_id: str
    previous_status: str
    new_status: str
    affected_tasks: List[str]
    rebalance_result: Optional[FleetRebalanceResponse] = None
    message: str


class FleetSimulationStepRequest(BaseModel):
    step_duration_minutes: float = Field(default=10.0, ge=1.0, le=60.0)
    auto_rebalance_on_disruption: bool = True


class FleetSimulationStepResponse(BaseModel):
    step_duration_minutes: float
    events_detected: List[str]
    vehicles_updated: int
    tasks_completed: List[str]
    rebalance_performed: bool
    rebalance_details: Optional[FleetRebalanceResponse] = None
    fleet_summary: FleetSummary
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class FleetBenchmarkRunResult(BaseModel):
    scenario_name: str
    seed: int
    tasks_assigned: int
    tasks_total: int
    assignment_success_rate: float
    safe_assignment_rate: float
    avg_assignment_eta_min: float
    total_fleet_travel_time_min: float
    total_fleet_distance_km: float
    emergency_fulfilled: int
    emergency_total: int
    breakdown_recovered: int
    breakdown_total: int
    mean_vehicle_utilization_pct: float
    utilization_variance: float
    load_balance_score: float
    unsafe_assignments_prevented: int
    reassignments_count: int
    avg_rebalancing_improvement_min: float
    unassigned_task_count: int
    primary_failure_mode: Optional[str] = None


class FleetExperimentSummaryResponse(BaseModel):
    total_runs: int
    scenarios_evaluated: List[str]
    task_assignment_success_rate_pct: float
    safe_assignment_rate_pct: float
    avg_assignment_eta_min: float
    avg_fleet_travel_time_min: float
    avg_fleet_distance_km: float
    emergency_fulfillment_rate_pct: float
    breakdown_recovery_rate_pct: float
    avg_vehicle_utilization_pct: float
    utilization_variance: float
    fleet_load_balance_score: float
    unsafe_assignments_prevented: int
    reassignments_count: int
    avg_rebalancing_improvement_min: float
    unassigned_task_rate_pct: float
    scenario_breakdown: Dict[str, Dict[str, Any]]
    failure_analysis: Dict[str, int]
    detailed_runs: List[FleetBenchmarkRunResult]
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


# ============================================================================
# PHASE 8 SCHEMAS — ADVANCED OPTIMIZATION, REALISTIC VALIDATION & WORKLOAD
# ============================================================================

class ScoreBreakdown(BaseModel):
    eta_component: float
    distance_component: float
    payload_component: float
    shift_component: float
    traffic_component: float
    weather_component: float
    workload_balance_component: float
    total_score: float


class OptimizationDecisionExplanation(BaseModel):
    selected_vehicle_id: Optional[str] = None
    decision_score: Optional[float] = None
    decision_reason: str
    safety_status: str
    score_breakdown: Optional[ScoreBreakdown] = None
    candidate_count_evaluated: int = 0
    unsafe_candidates_count: int = 0
    rejected_reasons: List[str] = Field(default_factory=list)


class FleetOptimizationSummaryResponse(BaseModel):
    total_vehicles: int
    active_vehicles: int
    available_vehicles: int
    assigned_vehicles: int
    overloaded_vehicles: int
    breakdown_vehicles: int
    workload_balance_score: float
    fleet_mean_workload_min: float
    fleet_workload_std_min: float
    mean_utilization_pct: float
    emergency_requests_count: int
    unsafe_assignments_prevented: int
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class EmergencyOptimizeRequest(BaseModel):
    location_node: str
    estimated_waste_kg: float = Field(default=1500.0, ge=10.0, le=15000.0)
    priority: str = Field(default="URGENT")
    environmental_context: Optional[Dict[str, Any]] = None


class EmergencyOptimizeResponse(BaseModel):
    task_id: str
    selected_vehicle_id: Optional[str] = None
    insertion_position: Optional[int] = None
    incremental_eta_min: Optional[float] = None
    incremental_distance_km: Optional[float] = None
    safety_status: str
    decision_reason: str
    rejected_vehicle_count: int
    rejected_candidate_reasons: List[str] = Field(default_factory=list)
    inserted_route: List[str] = Field(default_factory=list)
    allocation_score: Optional[float] = None
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class BreakdownRecoveryEventResponse(BaseModel):
    event_id: str
    broken_vehicle_id: str
    affected_tasks: List[str]
    remaining_waste_kg: float
    replacement_vehicle_id: Optional[str] = None
    recovery_time_min: float
    additional_distance_km: float
    additional_eta_min: float
    recovery_status: str  # RECOVERED, PARTIAL, DEFERRED
    decision_reason: str
    timestamp: datetime
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class DynamicRebalanceBenefitRequest(BaseModel):
    trigger_reason: str = Field(default="WORKLOAD_IMBALANCE")
    affected_vehicle_id: Optional[str] = None
    environmental_context: Optional[Dict[str, Any]] = None
    force_rebalance: bool = False


class DynamicRebalanceBenefitResponse(BaseModel):
    rebalance_required: bool
    benefit_assessment_reason: str
    trigger_reason: str
    affected_vehicles: List[str] = Field(default_factory=list)
    affected_tasks: List[str] = Field(default_factory=list)
    previous_allocation: Dict[str, Optional[str]] = Field(default_factory=dict)
    new_allocation: Dict[str, Optional[str]] = Field(default_factory=dict)
    expected_eta_change_min: float = 0.0
    expected_distance_change_km: float = 0.0
    workload_balance_before: float = 0.0
    workload_balance_after: float = 0.0
    details: List[Dict[str, Any]] = Field(default_factory=list)
    audit_events: List[FleetAuditEventResponse] = Field(default_factory=list)
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class MetricComparison(BaseModel):
    baseline_value: float
    optimized_value: float
    absolute_difference: float
    percentage_improvement: float
    unit: str


class AllocationComparisonResponse(BaseModel):
    strategy_evaluated: str
    task_count: int
    eta_comparison: MetricComparison
    distance_comparison: MetricComparison
    utilization_comparison: MetricComparison
    workload_balance_comparison: MetricComparison
    safety_violations_prevented_comparison: MetricComparison
    reassignment_count_comparison: MetricComparison
    summary_verdict: str
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class FailureDiagnosticItem(BaseModel):
    scenario: str
    seed: int
    task_id: Optional[str] = None
    vehicle_id: Optional[str] = None
    failure_category: str
    failure_reason: str
    recovery_action: str
    final_status: str


class Phase8BenchmarkRunResult(BaseModel):
    scenario_name: str
    seed: int
    tasks_assigned: int
    tasks_total: int
    assignment_success_rate: float
    safe_assignment_rate: float
    unassigned_task_rate: float
    emergency_fulfillment_rate: float
    vehicle_utilization_mean_pct: float
    workload_balance_metric: float
    avg_tasks_per_vehicle: float
    reassignment_count: int
    avg_eta_min: float
    total_travel_time_min: float
    total_fleet_travel_time_min: Optional[float] = None
    avg_distance_km: float
    additional_distance_km: float
    rerouting_success_rate: float
    unsafe_candidates_rejected: int
    unsafe_assignments_prevented: int
    payload_violations_prevented: int
    shift_violations_prevented: int
    blocked_road_violations_prevented: int
    breakdown_recovery_rate: float
    avg_recovery_time_min: float
    affected_task_count: int
    baseline_allocation_score: float
    optimized_allocation_score: float
    optimization_improvement_pct: float
    execution_time_ms: float
    primary_failure_category: Optional[str] = None


class ScenarioStatisticalSummary(BaseModel):
    scenario_name: str
    num_runs: int
    eta_mean: float
    eta_median: float
    eta_min: float
    eta_max: float
    eta_std: float
    distance_mean: float
    distance_median: float
    distance_min: float
    distance_max: float
    distance_std: float
    score_mean: float
    score_median: float
    score_min: float
    score_max: float
    score_std: float
    workload_balance_mean: float
    workload_balance_median: float
    workload_balance_min: float
    workload_balance_max: float
    workload_balance_std: float
    recovery_time_mean: float
    recovery_time_std: float
    pct_improvement_over_baseline: float


class Phase8ExperimentSummaryResponse(BaseModel):
    total_runs: int
    scenarios_evaluated: List[str]
    seeds_evaluated: List[int]
    overall_assignment_success_rate_pct: float
    overall_safe_assignment_rate_pct: float
    overall_emergency_fulfillment_rate_pct: float
    overall_breakdown_recovery_rate_pct: float
    overall_mean_workload_balance: float
    overall_mean_utilization_pct: float
    total_unsafe_candidates_rejected: int
    total_unsafe_assignments_prevented: int
    total_payload_violations_prevented: int
    total_shift_violations_prevented: int
    total_blocked_road_violations_prevented: int
    mean_baseline_score: float
    mean_optimized_score: float
    overall_optimization_improvement_pct: float
    scenario_statistics: Dict[str, ScenarioStatisticalSummary]
    failure_distribution: Dict[str, int]
    failure_diagnostic_log: List[FailureDiagnosticItem]
    detailed_runs: List[Phase8BenchmarkRunResult]
    benchmark_execution_time_seconds: float
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )


class EndToEndSimulationRequest(BaseModel):
    scenario_name: str = Field(default="NORMAL_OPERATIONS")
    seed: int = Field(default=42)
    step_count: int = Field(default=10, ge=1, le=50)


class EndToEndSimulationResponse(BaseModel):
    scenario_name: str
    seed: int
    timeline_events: List[Dict[str, Any]]
    final_fleet_state: FleetStateResponse
    metrics: Phase8BenchmarkRunResult
    execution_time_ms: float
    disclaimer: str = (
        "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
        "It does not represent live municipal dispatch or GPS tracking."
    )

