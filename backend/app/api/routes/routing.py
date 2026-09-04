"""REST API endpoints for Phase 6 Dynamic Routing and Real-time Optimization Engine."""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.routing import (
    ActiveTripCreate,
    ActiveTripResponse,
    DisruptionInjectRequest,
    RerouteRequest,
    RerouteResponse,
    SimulateStepRequest,
    SimulationStepResponse,
    NetworkGraphResponse,
    RoutingExperimentSummary,
)
from app.services.rerouting_service import ReroutingService
from app.services.rerouting_experiment_service import ReroutingExperimentService

router = APIRouter(prefix="/routing", tags=["Dynamic Routing & Rerouting"])

# Shared service instances
_service_instance: ReroutingService = ReroutingService()
_experiment_service: ReroutingExperimentService = ReroutingExperimentService()


@router.get("/graph", response_model=NetworkGraphResponse)
def get_road_network_graph():
    """Retrieve simulated deterministic municipal road network graph."""
    graph = _service_instance.get_graph()
    nodes = [
        {
            "id": node_id,
            "name": data["name"],
            "lat": data["lat"],
            "lng": data["lng"],
            "node_type": data["node_type"],
        }
        for node_id, data in graph.nodes.items()
    ]

    edges = [
        {
            "source": u,
            "target": v,
            "distance_km": data["distance_km"],
            "speed_limit_kmh": data["speed_limit_kmh"],
            "base_traversal_time_min": round((data["distance_km"] / data["speed_limit_kmh"]) * 60.0, 2),
            "current_traversal_time_min": round(graph.compute_edge_cost(u, v, weight_mode="time"), 2),
            "is_blocked": data.get("is_blocked", False),
            "congestion_factor": data.get("congestion_factor", 1.0),
            "weather_penalty_factor": data.get("weather_penalty_factor", 1.0),
            "road_type": data.get("road_type", "arterial"),
        }
        for (u, v), data in graph.edges.items()
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "disclaimer": (
            "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
            "It does not represent live municipal routing or live GPS data."
        ),
    }


@router.post("/trips", response_model=ActiveTripResponse, status_code=status.HTTP_201_CREATED)
def create_active_trip(trip_in: ActiveTripCreate, db: Session = Depends(get_db)):
    """Initialize a new active municipal waste collection trip."""
    trip = _service_instance.create_trip(db=db, trip_in=trip_in)
    return trip


@router.get("/trips", response_model=List[ActiveTripResponse])
def list_active_trips(limit: int = 50, db: Session = Depends(get_db)):
    """List active and historical simulation trips."""
    trips = _service_instance.list_trips(db=db, limit=limit)
    return trips


@router.get("/trips/{trip_id}", response_model=ActiveTripResponse)
def get_active_trip(trip_id: str, db: Session = Depends(get_db)):
    """Get detailed state of an active trip."""
    trip = _service_instance.get_trip(db=db, trip_id=trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail=f"Active trip {trip_id} not found.")
    return trip


@router.post("/trips/{trip_id}/inject-disruption")
def inject_trip_disruption(
    trip_id: str,
    disruption: DisruptionInjectRequest,
    db: Session = Depends(get_db),
):
    """Inject real-time disruption (closure, congestion spike, storm, extra waste)."""
    try:
        res = _service_instance.inject_disruption(db=db, trip_id=trip_id, disruption=disruption)
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/trips/{trip_id}/reroute", response_model=RerouteResponse)
def execute_trip_reroute(
    trip_id: str,
    reroute_in: RerouteRequest,
    db: Session = Depends(get_db),
):
    """Evaluate candidate paths with Adaptive Hybrid ETA and safety constraints, executing reroute if optimal."""
    try:
        res = _service_instance.execute_reroute(
            db=db,
            trip_id=trip_id,
            reroute_in=reroute_in,
            trigger_type="USER_REQUESTED" if not reroute_in.force_reroute else "FORCE_REROUTE",
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/trips/{trip_id}/step", response_model=SimulationStepResponse)
def simulate_trip_step(
    trip_id: str,
    step_in: SimulateStepRequest,
    db: Session = Depends(get_db),
):
    """Advance active trip forward by one node step in the simulation."""
    try:
        res = _service_instance.simulate_step(
            db=db,
            trip_id=trip_id,
            step_duration_minutes=step_in.step_duration_minutes,
            auto_reroute=step_in.auto_reroute_on_disruption,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/experiments/run", response_model=RoutingExperimentSummary)
def run_phase6_benchmark():
    """Run full Phase 6 empirical benchmark (7 scenarios x 5 random seeds = 35 runs)."""
    summary = _experiment_service.run_full_benchmark()
    return summary
