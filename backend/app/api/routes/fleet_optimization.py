"""FastAPI endpoints for Phase 8 Advanced Fleet Optimization, Realistic Validation, and Benchmarks."""
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.fleet.fleet_service import fleet_service
from app.fleet.fleet_optimizer import FleetOptimizer
from app.fleet.fleet_rebalancer import FleetRebalancer
from app.fleet.task_insertion import DynamicTaskInserter
from app.fleet.task_allocator import TaskAllocator
from app.fleet.end_to_end_simulator import EndToEndFleetSimulator
from app.fleet.phase8_experiments import (
    phase8_experiment_runner,
    PHASE8_SCENARIOS,
    PHASE8_SEEDS,
)
from app.schemas.fleet import (
    FleetOptimizationSummaryResponse,
    TaskAssignResponse,
    EmergencyOptimizeRequest,
    EmergencyOptimizeResponse,
    BreakdownRecoveryEventResponse,
    DynamicRebalanceBenefitRequest,
    DynamicRebalanceBenefitResponse,
    AllocationComparisonResponse,
    FailureDiagnosticItem,
    Phase8ExperimentSummaryResponse,
    EndToEndSimulationRequest,
    EndToEndSimulationResponse,
)

router = APIRouter(prefix="/fleet/optimization", tags=["fleet-optimization"])


@router.get("/summary", response_model=FleetOptimizationSummaryResponse)
def get_optimization_summary():
    """Retrieve high-level fleet optimization summary with workload distribution."""
    state_mgr = fleet_service.state_mgr
    vehicles = state_mgr.get_all_vehicles()
    summary = state_mgr.get_fleet_summary()
    wl = state_mgr.get_workload_metrics()

    return FleetOptimizationSummaryResponse(
        total_vehicles=summary.total_vehicles,
        active_vehicles=summary.assigned + summary.en_route,
        available_vehicles=summary.available,
        assigned_vehicles=summary.assigned,
        overloaded_vehicles=summary.overloaded,
        breakdown_vehicles=summary.breakdown,
        workload_balance_score=wl["workload_balance_score"],
        fleet_mean_workload_min=wl["mean_workload_min"],
        fleet_workload_std_min=wl["workload_std_dev"],
        mean_utilization_pct=summary.mean_utilization_pct,
        emergency_requests_count=sum(1 for v in vehicles if "EMG" in str(v.get("current_task_id", ""))),
        unsafe_assignments_prevented=sum(1 for v in vehicles if v.get("overload_status") == "OVERLOADED" or v.get("status") == "BREAKDOWN"),
    )


@router.post("/allocate", response_model=TaskAssignResponse)
def allocate_task_optimized(
    task_id: Optional[str] = None,
    location_node: str = "COLLECTION_ZONE_A",
    estimated_waste_kg: float = 1200.0,
    priority: str = "NORMAL",
    strategy: str = "ADVANCED_OPTIMIZER",
):
    """Allocate a task using the 7-component Multi-Objective Optimizer or Baseline Allocator."""
    t_id = task_id or f"TSK-OPT-{uuid.uuid4().hex[:6].upper()}"
    allocator = TaskAllocator(fleet_service.graph, fleet_service.state_mgr)
    return allocator.allocate_task(
        task_id=t_id,
        location_node=location_node,
        estimated_waste_kg=estimated_waste_kg,
        priority=priority,
        request_type="SCHEDULED_COLLECTION",
        strategy=strategy,
    )


@router.post("/rebalance", response_model=DynamicRebalanceBenefitResponse)
def rebalance_with_benefit(req: Optional[DynamicRebalanceBenefitRequest] = None):
    """Trigger dynamic fleet rebalancing with benefit assessment (avoids unnecessary route churn)."""
    trigger_reason = req.trigger_reason if req else "WORKLOAD_IMBALANCE"
    aff_veh = req.affected_vehicle_id if req else None
    env_ctx = req.environmental_context if req else None
    force = req.force_rebalance if req else False

    rebalancer = FleetRebalancer(fleet_service.graph, fleet_service.state_mgr)
    return rebalancer.assess_and_rebalance_with_benefit(
        trigger_reason=trigger_reason,
        affected_vehicle_id=aff_veh,
        environmental_context=env_ctx,
        force_rebalance=force,
    )


@router.post("/emergency", response_model=EmergencyOptimizeResponse)
def optimize_emergency_request(req: EmergencyOptimizeRequest):
    """Execute 10-step emergency waste request insertion across the active fleet."""
    inserter = DynamicTaskInserter(fleet_service.graph)
    state_mgr = fleet_service.state_mgr
    t_id = f"EMG-OPT-{uuid.uuid4().hex[:6].upper()}"

    res = inserter.evaluate_emergency_insertion_across_fleet(
        vehicles=state_mgr.get_all_vehicles(),
        task_id=t_id,
        location_node=req.location_node,
        estimated_waste_kg=req.estimated_waste_kg,
        priority=req.priority,
        environmental_context=req.environmental_context,
        fleet_mean_workload_min=state_mgr.get_workload_metrics()["mean_workload_min"],
    )

    return EmergencyOptimizeResponse(
        task_id=t_id,
        selected_vehicle_id=res.get("selected_vehicle_id"),
        insertion_position=res.get("insertion_position"),
        incremental_eta_min=res.get("incremental_eta_min"),
        incremental_distance_km=res.get("incremental_distance_km"),
        safety_status=res.get("safety_status", "SAFE"),
        decision_reason=res.get("decision_reason", ""),
        rejected_vehicle_count=res.get("rejected_vehicle_count", 0),
        rejected_candidate_reasons=res.get("rejected_candidate_reasons", []),
        inserted_route=res.get("inserted_route", []),
        allocation_score=res.get("allocation_score"),
    )


@router.post("/breakdown", response_model=BreakdownRecoveryEventResponse)
def execute_breakdown_recovery(
    vehicle_id: str = Query("V-01", description="ID of the broken vehicle"),
):
    """Trigger auditable mid-route breakdown recovery with safe task reallocation."""
    rebalancer = FleetRebalancer(fleet_service.graph, fleet_service.state_mgr)
    try:
        return rebalancer.execute_breakdown_recovery(vehicle_id=vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/simulate", response_model=EndToEndSimulationResponse)
def simulate_end_to_end(req: Optional[EndToEndSimulationRequest] = None):
    """Execute complete deterministic end-to-end simulation across all operational stages."""
    sc_name = req.scenario_name if req else "NORMAL_OPERATIONS"
    seed = req.seed if req else 42
    sim = EndToEndFleetSimulator(seed=seed)
    return sim.run_simulation(scenario_name=sc_name)


@router.post("/experiments/run", response_model=Phase8ExperimentSummaryResponse)
def run_benchmark_suite(force_fresh: bool = Query(True, description="Force re-execution of all 50 benchmark runs")):
    """Run all 10 scenarios x 5 deterministic seeds = 50 runs and return statistical evaluation."""
    return phase8_experiment_runner.run_benchmark_suite(force_fresh=force_fresh)


@router.get("/experiments", response_model=Phase8ExperimentSummaryResponse)
def get_benchmark_experiments():
    """Retrieve latest Phase 8 benchmark results across 50 runs."""
    return phase8_experiment_runner.run_benchmark_suite(force_fresh=False)


@router.get("/failures", response_model=List[FailureDiagnosticItem])
def get_failure_diagnostics():
    """Retrieve failure diagnostics and taxonomy breakdown across benchmark runs."""
    summary = phase8_experiment_runner.run_benchmark_suite(force_fresh=False)
    return summary.failure_diagnostic_log


@router.get("/comparison", response_model=AllocationComparisonResponse)
def compare_strategies():
    """Execute direct comparison between BASELINE allocator and ADVANCED_OPTIMIZER."""
    optimizer = FleetOptimizer(fleet_service.graph, fleet_service.state_mgr)
    test_tasks = [
        {"id": "COMP-TSK-1", "location_node": "COLLECTION_ZONE_A", "estimated_waste_kg": 1400.0, "priority": "NORMAL"},
        {"id": "COMP-TSK-2", "location_node": "COLLECTION_ZONE_B", "estimated_waste_kg": 1800.0, "priority": "NORMAL"},
        {"id": "COMP-TSK-3", "location_node": "COLLECTION_ZONE_C", "estimated_waste_kg": 2200.0, "priority": "HIGH"},
        {"id": "COMP-TSK-4", "location_node": "COLLECTION_ZONE_D", "estimated_waste_kg": 1100.0, "priority": "NORMAL"},
        {"id": "COMP-TSK-5", "location_node": "COLLECTION_ZONE_E", "estimated_waste_kg": 1600.0, "priority": "NORMAL"},
        {"id": "COMP-TSK-6", "location_node": "COLLECTION_ZONE_F", "estimated_waste_kg": 1900.0, "priority": "NORMAL"},
    ]
    return optimizer.compare_allocation_strategies(test_tasks)
