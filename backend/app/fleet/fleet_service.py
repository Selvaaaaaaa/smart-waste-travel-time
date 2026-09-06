"""High-level service coordinating fleet state, persistence, rebalancing, and simulation steps."""
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.fleet_models import CollectionTask, FleetAuditEvent
from app.routing.graph import RoadNetworkGraph, get_default_network_graph
from app.fleet.fleet_state import FleetStateManager, fleet_state_manager
from app.fleet.task_allocator import TaskAllocator
from app.fleet.fleet_rebalancer import FleetRebalancer
from app.fleet.fleet_experiments import FleetExperimentRunner
from app.schemas.fleet import (
    CollectionTaskCreate,
    TaskAssignResponse,
    VehicleBreakdownResponse,
    FleetRebalanceResponse,
    FleetAuditEventResponse,
    FleetSimulationStepResponse,
    FleetExperimentSummaryResponse,
)

logger = logging.getLogger(__name__)


class FleetService:
    """Coordinates database persistence, fleet state management, and real-time operations."""

    def __init__(
        self,
        graph: Optional[RoadNetworkGraph] = None,
        state_mgr: Optional[FleetStateManager] = None,
    ):
        self.graph = graph or get_default_network_graph()
        self.state_mgr = state_mgr or fleet_state_manager
        self.allocator = TaskAllocator(self.graph, self.state_mgr)
        self.rebalancer = FleetRebalancer(self.graph, self.state_mgr, self.allocator)
        self.experiment_runner = FleetExperimentRunner()

    def create_task(self, db: Session, task_in: CollectionTaskCreate) -> CollectionTask:
        """Create and persist a collection task."""
        t_id = f"TSK-{uuid.uuid4().hex[:8].upper()}"
        task = CollectionTask(
            id=t_id,
            location_node=task_in.location_node,
            estimated_waste_kg=task_in.estimated_waste_kg,
            priority=task_in.priority,
            request_type=task_in.request_type,
            status="PENDING",
            deadline_minutes=task_in.deadline_minutes,
            notes=task_in.notes or "Scheduled municipal collection task.",
            created_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def get_task(self, db: Session, task_id: str) -> Optional[CollectionTask]:
        return db.query(CollectionTask).filter(CollectionTask.id == task_id).first()

    def list_tasks(
        self,
        db: Session,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[CollectionTask]:
        query = db.query(CollectionTask)
        if status:
            query = query.filter(CollectionTask.status == status)
        return query.order_by(CollectionTask.created_at.desc()).limit(limit).all()

    def assign_task(
        self,
        db: Session,
        task_id: str,
        environmental_context: Optional[Dict[str, Any]] = None,
    ) -> TaskAssignResponse:
        """Execute allocation algorithm for a task and log audit event."""
        task = self.get_task(db, task_id)
        if not task:
            raise ValueError(f"Collection task {task_id} not found.")

        res = self.allocator.allocate_task(
            task_id=task.id,
            location_node=task.location_node,
            estimated_waste_kg=task.estimated_waste_kg,
            priority=task.priority,
            request_type=task.request_type,
            environmental_context=environmental_context,
        )

        if res.status == "ASSIGNED":
            task.status = "ASSIGNED"
            task.assigned_vehicle_id = res.selected_vehicle_id
            task.assigned_driver_id = res.selected_driver_id
            task.assigned_at = datetime.utcnow()
            db.commit()

            # Persist Audit Event
            audit = FleetAuditEvent(
                id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
                event_type="TASK_ASSIGNED",
                task_id=task.id,
                previous_vehicle_id=None,
                new_vehicle_id=res.selected_vehicle_id,
                previous_route=[],
                new_route=res.selected_route,
                predicted_eta_before=None,
                predicted_eta_after=res.predicted_eta_minutes,
                distance_difference_km=round(self.graph.compute_path_distance(res.selected_route), 2),
                safety_result="SAFE",
                selected_eta_model="ADAPTIVE_HYBRID",
                reason=res.selection_reason,
                timestamp=datetime.utcnow(),
            )
            db.add(audit)
            db.commit()
        else:
            task.status = "DEFERRED"
            db.commit()

        return res

    def trigger_emergency_task(
        self,
        db: Session,
        task_id: str,
        environmental_context: Optional[Dict[str, Any]] = None,
    ) -> TaskAssignResponse:
        """Assign an urgent emergency task, attempting dynamic route insertion."""
        task = self.get_task(db, task_id)
        if not task:
            raise ValueError(f"Collection task {task_id} not found.")

        task.priority = "URGENT"
        task.request_type = "EMERGENCY_REQUEST"
        db.commit()

        return self.assign_task(db, task_id, environmental_context)

    def trigger_breakdown(
        self,
        db: Session,
        vehicle_id: str,
        reason: str = "MECHANICAL_FAILURE",
    ) -> VehicleBreakdownResponse:
        """Mark vehicle as broken down and automatically trigger task rebalancing."""
        veh = self.state_mgr.get_vehicle(vehicle_id)
        if not veh:
            raise ValueError(f"Vehicle {vehicle_id} not found in fleet.")

        prev_status = veh["status"]
        self.state_mgr.trigger_breakdown(vehicle_id)

        # Identify affected tasks in DB assigned to this vehicle
        assigned_tasks = db.query(CollectionTask).filter(
            CollectionTask.assigned_vehicle_id == vehicle_id,
            CollectionTask.status.in_(["ASSIGNED", "IN_PROGRESS"]),
        ).all()

        affected_ids = [t.id for t in assigned_tasks]
        for t in assigned_tasks:
            t.status = "PENDING"
            t.assigned_vehicle_id = None
        db.commit()

        # Execute fleet rebalancing
        rebalance_res = self.rebalancer.rebalance_fleet(
            trigger_reason=f"BREAKDOWN_{vehicle_id}",
            affected_vehicle_id=vehicle_id,
            known_tasks=[
                {
                    "id": t.id,
                    "location_node": t.location_node,
                    "estimated_waste_kg": t.estimated_waste_kg,
                    "assigned_vehicle_id": vehicle_id,
                }
                for t in assigned_tasks
            ],
        )

        # Log audit events into DB
        for ev in rebalance_res.audit_events:
            db_ev = FleetAuditEvent(
                id=ev.id,
                event_type=ev.event_type,
                task_id=ev.task_id,
                previous_vehicle_id=ev.previous_vehicle_id,
                new_vehicle_id=ev.new_vehicle_id,
                previous_route=ev.previous_route,
                new_route=ev.new_route,
                predicted_eta_before=ev.predicted_eta_before,
                predicted_eta_after=ev.predicted_eta_after,
                distance_difference_km=ev.distance_difference_km,
                safety_result=ev.safety_result,
                selected_eta_model=ev.selected_eta_model,
                reason=ev.reason,
                timestamp=ev.timestamp,
            )
            db.add(db_ev)
        db.commit()

        return VehicleBreakdownResponse(
            vehicle_id=vehicle_id,
            previous_status=prev_status,
            new_status="BREAKDOWN",
            affected_tasks=affected_ids,
            rebalance_result=rebalance_res,
            message=f"Vehicle {vehicle_id} marked as BREAKDOWN. {len(affected_ids)} tasks reassigned.",
        )

    def recover_vehicle(self, db: Session, vehicle_id: str) -> Dict[str, Any]:
        """Recover vehicle from BREAKDOWN back to AVAILABLE."""
        veh = self.state_mgr.recover_vehicle(vehicle_id)
        if not veh:
            raise ValueError(f"Vehicle {vehicle_id} not found.")

        # Log recovery audit event
        db_ev = FleetAuditEvent(
            id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            event_type="VEHICLE_RECOVERED",
            task_id=None,
            previous_vehicle_id=vehicle_id,
            new_vehicle_id=vehicle_id,
            previous_route=[],
            new_route=[],
            predicted_eta_before=None,
            predicted_eta_after=None,
            distance_difference_km=0.0,
            safety_result="SAFE",
            selected_eta_model="NONE",
            reason=f"Vehicle {vehicle_id} completed maintenance and is restored to AVAILABLE.",
            timestamp=datetime.utcnow(),
        )
        db.add(db_ev)
        db.commit()

        return {
            "vehicle_id": vehicle_id,
            "status": "AVAILABLE",
            "message": f"Vehicle {vehicle_id} recovered successfully.",
        }

    def rebalance(
        self,
        db: Session,
        trigger_reason: str = "MANUAL_REBALANCE",
        affected_vehicle_id: Optional[str] = None,
    ) -> FleetRebalanceResponse:
        """Trigger rebalancing across pending or overloaded tasks."""
        pending_tasks = db.query(CollectionTask).filter(CollectionTask.status == "PENDING").all()
        known = [
            {
                "id": t.id,
                "location_node": t.location_node,
                "estimated_waste_kg": t.estimated_waste_kg,
                "assigned_vehicle_id": t.assigned_vehicle_id,
            }
            for t in pending_tasks
        ]
        res = self.rebalancer.rebalance_fleet(
            trigger_reason=trigger_reason,
            affected_vehicle_id=affected_vehicle_id,
            known_tasks=known,
        )

        for ev in res.audit_events:
            db_ev = FleetAuditEvent(
                id=ev.id,
                event_type=ev.event_type,
                task_id=ev.task_id,
                previous_vehicle_id=ev.previous_vehicle_id,
                new_vehicle_id=ev.new_vehicle_id,
                previous_route=ev.previous_route,
                new_route=ev.new_route,
                predicted_eta_before=ev.predicted_eta_before,
                predicted_eta_after=ev.predicted_eta_after,
                distance_difference_km=ev.distance_difference_km,
                safety_result=ev.safety_result,
                selected_eta_model=ev.selected_eta_model,
                reason=ev.reason,
                timestamp=ev.timestamp,
            )
            db.add(db_ev)
            # Update task in DB if reassigned
            if ev.task_id and ev.new_vehicle_id:
                t = db.query(CollectionTask).filter(CollectionTask.id == ev.task_id).first()
                if t:
                    t.status = "ASSIGNED"
                    t.assigned_vehicle_id = ev.new_vehicle_id
                    t.assigned_at = datetime.utcnow()
        db.commit()
        return res

    def list_audit_events(self, db: Session, limit: int = 50) -> List[FleetAuditEvent]:
        return db.query(FleetAuditEvent).order_by(FleetAuditEvent.timestamp.desc()).limit(limit).all()

    def simulate_fleet_step(
        self,
        db: Session,
        step_minutes: float = 10.0,
        auto_rebalance: bool = True,
    ) -> FleetSimulationStepResponse:
        """Advance the fleet by a simulation time step."""
        events_detected = []
        tasks_completed = []
        vehicles_updated = 0

        for v in self.state_mgr.get_all_vehicles():
            if v["status"] in ["ASSIGNED", "EN_ROUTE"]:
                v_route = v.get("current_route", [])
                if len(v_route) > 1:
                    # Advance one node
                    visited_node = v_route.pop(0)
                    v["current_location"] = v_route[0]
                    v["driver_shift_remaining_min"] = max(0.0, v["driver_shift_remaining_min"] - step_minutes)
                    v["estimated_available_time_min"] = max(0.0, v["estimated_available_time_min"] - step_minutes)
                    vehicles_updated += 1

                    if len(v_route) <= 1:
                        # Reached destination (landfill)
                        v["status"] = "AVAILABLE"
                        v["current_route"] = []
                        if v.get("current_task_id"):
                            t_id = v["current_task_id"]
                            tasks_completed.append(t_id)
                            t = db.query(CollectionTask).filter(CollectionTask.id == t_id).first()
                            if t:
                                t.status = "COMPLETED"
                                t.completed_at = datetime.utcnow()
                            v["current_task_id"] = None
                        v["current_payload_kg"] = 0.0  # emptied at landfill
                    else:
                        v["status"] = "EN_ROUTE"

        db.commit()

        rebalance_res = None
        if auto_rebalance and events_detected:
            rebalance_res = self.rebalance(db, trigger_reason="STEP_DISRUPTION")

        summary = self.state_mgr.get_fleet_summary()

        return FleetSimulationStepResponse(
            step_duration_minutes=step_minutes,
            events_detected=events_detected,
            vehicles_updated=vehicles_updated,
            tasks_completed=tasks_completed,
            rebalance_performed=(rebalance_res is not None),
            rebalance_details=rebalance_res,
            fleet_summary=summary,
        )

    def run_benchmark_experiments(self) -> FleetExperimentSummaryResponse:
        """Execute full 35-run benchmark suite."""
        return self.experiment_runner.run_full_suite()


fleet_service = FleetService()
