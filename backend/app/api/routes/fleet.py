"""FastAPI routing endpoints for Phase 7 Fleet Coordination & Dynamic Task Allocation."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.fleet.fleet_service import fleet_service
from app.models.fleet_models import CollectionTask, FleetAuditEvent
from app.schemas.fleet import (
    FleetStateResponse,
    VehicleFleetItem,
    CollectionTaskCreate,
    CollectionTaskResponse,
    TaskAssignResponse,
    VehicleBreakdownRequest,
    VehicleBreakdownResponse,
    FleetRebalanceRequest,
    FleetRebalanceResponse,
    FleetAuditEventResponse,
    FleetSimulationStepRequest,
    FleetSimulationStepResponse,
    FleetExperimentSummaryResponse,
)

router = APIRouter(prefix="/fleet", tags=["fleet-coordination"])


@router.get("/state", response_model=FleetStateResponse)
def get_fleet_state(db: Session = Depends(get_db)):
    """Retrieve complete fleet operational state, KPI summary, and all vehicle statuses."""
    active_count = db.query(CollectionTask).filter(CollectionTask.status.in_(["ASSIGNED", "IN_PROGRESS"])).count()
    pending_count = db.query(CollectionTask).filter(CollectionTask.status == "PENDING").count()
    return fleet_service.state_mgr.get_fleet_state_response(
        active_tasks_count=active_count,
        pending_tasks_count=pending_count,
    )


@router.get("/vehicles", response_model=List[VehicleFleetItem])
def get_fleet_vehicles():
    """Retrieve detailed state of all active fleet vehicles."""
    state_res = fleet_service.state_mgr.get_fleet_state_response()
    return state_res.vehicles


@router.get("/tasks", response_model=List[CollectionTaskResponse])
def get_fleet_tasks(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, ASSIGNED, COMPLETED, DEFERRED"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve list of collection tasks."""
    return fleet_service.list_tasks(db=db, status=status, limit=limit)


@router.post("/tasks", response_model=CollectionTaskResponse, status_code=201)
def create_collection_task(
    task_in: CollectionTaskCreate,
    db: Session = Depends(get_db),
):
    """Create a new municipal collection task or emergency request."""
    return fleet_service.create_task(db=db, task_in=task_in)


@router.post("/tasks/{task_id}/assign", response_model=TaskAssignResponse)
def assign_collection_task(
    task_id: str,
    db: Session = Depends(get_db),
):
    """Trigger the multi-criteria allocation engine to assign task to the safest and best vehicle."""
    try:
        return fleet_service.assign_task(db=db, task_id=task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tasks/{task_id}/emergency", response_model=TaskAssignResponse)
def emergency_collection_request(
    task_id: str,
    db: Session = Depends(get_db),
):
    """Elevate task to URGENT emergency request and trigger dynamic insertion/allocation."""
    try:
        return fleet_service.trigger_emergency_task(db=db, task_id=task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/vehicles/{vehicle_id}/breakdown", response_model=VehicleBreakdownResponse)
def trigger_vehicle_breakdown(
    vehicle_id: str,
    breakdown_in: Optional[VehicleBreakdownRequest] = None,
    db: Session = Depends(get_db),
):
    """Simulate mid-trip breakdown of a vehicle and auto-redistribute affected tasks."""
    try:
        reason = breakdown_in.reason if breakdown_in else "MECHANICAL_FAILURE"
        return fleet_service.trigger_breakdown(db=db, vehicle_id=vehicle_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/vehicles/{vehicle_id}/recover")
def recover_broken_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
):
    """Restore a broken vehicle back to AVAILABLE status."""
    try:
        return fleet_service.recover_vehicle(db=db, vehicle_id=vehicle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rebalance", response_model=FleetRebalanceResponse)
def rebalance_fleet(
    req: Optional[FleetRebalanceRequest] = None,
    db: Session = Depends(get_db),
):
    """Trigger dynamic fleet rebalancing to resolve overloads or reassign pending tasks."""
    reason = req.trigger_reason if req else "MANUAL_REBALANCE"
    aff_id = req.affected_vehicle_id if req else None
    return fleet_service.rebalance(db=db, trigger_reason=reason, affected_vehicle_id=aff_id)


@router.get("/events", response_model=List[FleetAuditEventResponse])
def get_fleet_events(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve chronological fleet audit events."""
    return fleet_service.list_audit_events(db=db, limit=limit)


@router.post("/simulate-step", response_model=FleetSimulationStepResponse)
def simulate_fleet_step(
    step_in: Optional[FleetSimulationStepRequest] = None,
    db: Session = Depends(get_db),
):
    """Simulate a time-step advancement across all vehicles in the fleet simultaneously."""
    step_min = step_in.step_duration_minutes if step_in else 10.0
    auto_reb = step_in.auto_rebalance_on_disruption if step_in else True
    return fleet_service.simulate_fleet_step(db=db, step_minutes=step_min, auto_rebalance=auto_reb)


@router.post("/experiments/run", response_model=FleetExperimentSummaryResponse)
def run_fleet_experiments():
    """Run Phase 7 benchmark suite: 7 Scenarios x 5 Seeds = 35 Runs."""
    return fleet_service.run_benchmark_experiments()
