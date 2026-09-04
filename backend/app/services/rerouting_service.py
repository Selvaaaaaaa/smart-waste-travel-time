"""Service layer for managing real-time active trips, disruptions, simulation steps, and rerouting."""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.routing_models import ActiveTrip, RouteCandidate, ReroutingEvent
from app.routing.graph import RoadNetworkGraph, get_default_network_graph
from app.routing.rerouting import DynamicReroutingEngine
from app.schemas.routing import ActiveTripCreate, DisruptionInjectRequest, RerouteRequest


class ReroutingService:
    """Singleton-like or instantiated service managing graph state and active trips."""

    def __init__(self, graph: Optional[RoadNetworkGraph] = None):
        self.graph = graph or get_default_network_graph()
        self.engine = DynamicReroutingEngine(self.graph)

    def get_graph(self) -> RoadNetworkGraph:
        return self.graph

    def create_trip(self, db: Session, trip_in: ActiveTripCreate) -> ActiveTrip:
        """Initialize and persist a new active municipal waste collection trip."""
        # Calculate initial path connecting origin -> initial_stops -> destination
        waypoints = [trip_in.origin_node] + trip_in.initial_stops + [trip_in.destination_node]
        initial_path = self.engine.candidate_generator.generate_path_for_waypoints(waypoints, weight_mode="balanced")
        if not initial_path:
            initial_path = waypoints

        # Calculate initial ETA via Adaptive Hybrid model
        ctx = self.engine.extract_path_context(initial_path)
        dist = self.graph.compute_path_distance(initial_path)
        base_eta = round(dist / 25.0 * 60.0, 2)
        
        trip = ActiveTrip(
            id=f"TRIP-{uuid.uuid4().hex[:8].upper()}",
            vehicle_id=trip_in.vehicle_id,
            driver_id=trip_in.driver_id,
            origin_node=trip_in.origin_node,
            destination_node=trip_in.destination_node,
            current_node=trip_in.origin_node,
            visited_nodes=[trip_in.origin_node],
            remaining_stops=list(trip_in.initial_stops),
            current_path=initial_path,
            current_payload_kg=trip_in.initial_payload_kg,
            vehicle_capacity_kg=trip_in.vehicle_capacity_kg,
            elapsed_time_minutes=0.0,
            max_shift_hours=trip_in.max_shift_hours,
            distance_traveled_km=0.0,
            current_eta_minutes=base_eta,
            baseline_eta_minutes=base_eta,
            hybrid_eta_minutes=base_eta,
            eta_uncertainty_minutes=2.0,
            status="IN_PROGRESS",
            active_disruptions=[],
            reroute_count=0,
            notes=trip_in.notes or "Municipal route initiated.",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(trip)
        db.commit()
        db.refresh(trip)
        return trip

    def get_trip(self, db: Session, trip_id: str) -> Optional[ActiveTrip]:
        return db.query(ActiveTrip).filter(ActiveTrip.id == trip_id).first()

    def list_trips(self, db: Session, limit: int = 50) -> List[ActiveTrip]:
        return db.query(ActiveTrip).order_by(ActiveTrip.created_at.desc()).limit(limit).all()

    def inject_disruption(
        self,
        db: Session,
        trip_id: str,
        disruption: DisruptionInjectRequest,
    ) -> Dict[str, Any]:
        """Inject real-time disruption (closure, traffic, storm) into road network and active trip."""
        trip = self.get_trip(db, trip_id)
        if not trip:
            raise ValueError(f"Trip with ID {trip_id} not found.")

        disr_entry = {
            "id": f"DISR-{uuid.uuid4().hex[:6].upper()}",
            "type": disruption.disruption_type,
            "target_edge": disruption.target_edge,
            "target_node": disruption.target_node,
            "severity": disruption.severity,
            "additional_waste_kg": disruption.additional_waste_kg,
            "description": disruption.description or f"Real-time {disruption.disruption_type} reported.",
            "injected_at": datetime.utcnow().isoformat(),
        }

        # Apply disruption onto road network graph
        if disruption.target_edge and len(disruption.target_edge) == 2:
            u, v = disruption.target_edge[0], disruption.target_edge[1]
            if disruption.disruption_type in ["ROAD_CLOSURE", "ROAD_BLOCKAGE"]:
                self.graph.set_edge_blocked(u, v, is_blocked=True)
            elif disruption.disruption_type in ["TRAFFIC_SPIKE", "CONGESTION"]:
                self.graph.set_edge_congestion(u, v, factor=max(2.0, disruption.severity * 2.0))
            elif disruption.disruption_type in ["HEAVY_RAIN", "FLOODING"]:
                self.graph.set_edge_weather_penalty(u, v, factor=max(1.8, disruption.severity * 1.5))
        elif disruption.target_node:
            # Apply to all edges adjacent to target node
            for neighbor in self.graph.adjacency.get(disruption.target_node, []):
                if disruption.disruption_type in ["ROAD_CLOSURE", "ROAD_BLOCKAGE"]:
                    self.graph.set_edge_blocked(disruption.target_node, neighbor, is_blocked=True)
                elif disruption.disruption_type in ["TRAFFIC_SPIKE", "EVENT_BLOCK"]:
                    self.graph.set_edge_congestion(disruption.target_node, neighbor, factor=3.0)

        # High waste scenario adds unexpected payload
        if disruption.additional_waste_kg > 0:
            trip.current_payload_kg += disruption.additional_waste_kg

        # Record in trip active disruptions
        current_disruptions = list(trip.active_disruptions or [])
        current_disruptions.append(disr_entry)
        trip.active_disruptions = current_disruptions
        trip.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(trip)

        return {
            "status": "DISRUPTION_INJECTED",
            "disruption": disr_entry,
            "trip": trip,
        }

    def execute_reroute(
        self,
        db: Session,
        trip_id: str,
        reroute_in: RerouteRequest,
        trigger_type: str = "MANUAL",
        trigger_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run candidate generation, scoring, and execute reroute if indicated."""
        trip = self.get_trip(db, trip_id)
        if not trip:
            raise ValueError(f"Trip with ID {trip_id} not found.")

        expected_remaining_waste = len(trip.remaining_stops) * 1200.0  # Approx 1.2 tons per remaining stop

        result = self.engine.evaluate_and_reroute(
            current_node=trip.current_node,
            remaining_stops=trip.remaining_stops,
            destination_node=trip.destination_node,
            current_path=trip.current_path,
            current_payload_kg=trip.current_payload_kg,
            vehicle_capacity_kg=trip.vehicle_capacity_kg,
            expected_remaining_waste_kg=expected_remaining_waste,
            elapsed_time_minutes=trip.elapsed_time_minutes,
            max_shift_hours=trip.max_shift_hours,
            trigger_type=trigger_type,
            trigger_details=trigger_details or {},
            strategies=reroute_in.candidate_strategies,
        )

        selected_cand_dict = result["selected_candidate"]
        candidate_entities = []

        # Persist candidate routes in database
        for c in result["all_candidates"]:
            cand_obj = RouteCandidate(
                id=f"CAND-{uuid.uuid4().hex[:8].upper()}",
                trip_id=trip.id,
                strategy=c["strategy"],
                path=c["path"],
                path_coordinates=c["path_coordinates"],
                total_distance_km=c["total_distance_km"],
                predicted_eta_minutes=c["predicted_eta_minutes"],
                baseline_eta_minutes=c["baseline_eta_minutes"],
                hybrid_eta_minutes=c["hybrid_eta_minutes"],
                eta_uncertainty_minutes=c["eta_uncertainty_minutes"],
                safety_valid=c["safety_valid"],
                safety_violations=c["safety_violations"],
                optimization_score=c["optimization_score"],
                is_selected=c["is_selected"],
                rejection_reason=c["rejection_reason"],
                created_at=datetime.utcnow(),
            )
            db.add(cand_obj)
            candidate_entities.append(cand_obj)

        event_obj = None
        if result["reroute_executed"] or reroute_in.force_reroute:
            # Update trip with new path and stats
            trip.current_path = result["new_path"]
            trip.current_eta_minutes = result["new_eta_minutes"]
            trip.hybrid_eta_minutes = result["new_eta_minutes"]
            if selected_cand_dict:
                trip.baseline_eta_minutes = selected_cand_dict.get("baseline_eta_minutes", result["new_eta_minutes"])
                trip.eta_uncertainty_minutes = selected_cand_dict.get("eta_uncertainty_minutes", 2.0)
            trip.reroute_count += 1
            trip.updated_at = datetime.utcnow()

            # Record ReroutingEvent
            event_obj = ReroutingEvent(
                id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
                trip_id=trip.id,
                trigger_type=trigger_type,
                trigger_details=trigger_details or {},
                previous_path=result["previous_path"],
                new_path=result["new_path"],
                previous_eta_minutes=result["previous_eta_minutes"],
                new_eta_minutes=result["new_eta_minutes"],
                time_saved_minutes=result["time_saved_minutes"],
                distance_difference_km=result["distance_difference_km"],
                selected_candidate_id=candidate_entities[0].id if candidate_entities else None,
                candidate_count=len(candidate_entities),
                decision_rationale=result["decision_rationale"],
                timestamp=datetime.utcnow(),
            )
            db.add(event_obj)

        db.commit()
        db.refresh(trip)

        return {
            "trip_id": trip.id,
            "reroute_executed": result["reroute_executed"] or reroute_in.force_reroute,
            "trigger_type": trigger_type,
            "decision_rationale": result["decision_rationale"],
            "selected_candidate": selected_cand_dict,
            "all_candidates": result["all_candidates"],
            "event": event_obj,
            "trip": trip,
        }

    def simulate_step(
        self,
        db: Session,
        trip_id: str,
        step_duration_minutes: float = 10.0,
        auto_reroute: bool = True,
    ) -> Dict[str, Any]:
        """Advance trip by one node along its current path."""
        trip = self.get_trip(db, trip_id)
        if not trip:
            raise ValueError(f"Trip with ID {trip_id} not found.")

        if trip.status == "COMPLETED":
            return {
                "trip": trip,
                "step_taken_from": trip.current_node,
                "step_taken_to": trip.current_node,
                "segment_distance_km": 0.0,
                "segment_time_minutes": 0.0,
                "waste_collected_kg": 0.0,
                "trip_completed": True,
                "reroute_occurred": False,
                "reroute_event": None,
            }

        # Determine next node along current_path
        current_idx = -1
        for idx, node in enumerate(trip.current_path):
            if node == trip.current_node:
                current_idx = idx
                break

        if current_idx == -1 or current_idx >= len(trip.current_path) - 1:
            # Trip arrived at destination
            trip.status = "COMPLETED"
            trip.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(trip)
            return {
                "trip": trip,
                "step_taken_from": trip.current_node,
                "step_taken_to": trip.destination_node,
                "segment_distance_km": 0.0,
                "segment_time_minutes": 0.0,
                "waste_collected_kg": 0.0,
                "trip_completed": True,
                "reroute_occurred": False,
                "reroute_event": None,
            }

        from_node = trip.current_path[current_idx]
        to_node = trip.current_path[current_idx + 1]

        # Calculate segment traversal metrics
        edge = self.graph.get_edge(from_node, to_node)
        seg_dist = edge["distance_km"] if edge else 2.0
        seg_time = self.graph.compute_edge_cost(from_node, to_node, weight_mode="time")
        if math_is_inf := (seg_time == float("inf")):
            seg_time = 15.0  # Safe fallback if blocked edge traversed accidentally

        # Update trip progress
        trip.current_node = to_node
        visited = list(trip.visited_nodes or [])
        visited.append(to_node)
        trip.visited_nodes = visited

        # If to_node was in remaining stops, remove it and add collected waste
        remaining = list(trip.remaining_stops or [])
        waste_collected = 0.0
        if to_node in remaining:
            remaining.remove(to_node)
            waste_collected = 1200.0  # Approx 1.2t per stop
            trip.current_payload_kg += waste_collected
        trip.remaining_stops = remaining

        trip.distance_traveled_km += seg_dist
        trip.elapsed_time_minutes += seg_time
        trip.current_eta_minutes = max(0.0, trip.current_eta_minutes - seg_time)

        # Check if trip is finished
        if to_node == trip.destination_node and not trip.remaining_stops:
            trip.status = "COMPLETED"

        trip.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(trip)

        reroute_occurred = False
        reroute_event = None

        # Check if downstream route has disruptions/closures and trigger auto-reroute
        if auto_reroute and trip.status != "COMPLETED":
            # Check if any upcoming edge is blocked or heavy traffic
            has_upcoming_block = False
            for k in range(current_idx + 1, len(trip.current_path) - 1):
                u, v = trip.current_path[k], trip.current_path[k + 1]
                e = self.graph.get_edge(u, v)
                if e and e.get("is_blocked", False):
                    has_upcoming_block = True
                    break

            if has_upcoming_block:
                reroute_res = self.execute_reroute(
                    db=db,
                    trip_id=trip.id,
                    reroute_in=RerouteRequest(),
                    trigger_type="ROAD_CLOSURE",
                    trigger_details={"blocked_edge_detected": True, "at_node": to_node},
                )
                reroute_occurred = reroute_res["reroute_executed"]
                reroute_event = reroute_res.get("event")

        return {
            "trip": trip,
            "step_taken_from": from_node,
            "step_taken_to": to_node,
            "segment_distance_km": round(seg_dist, 2),
            "segment_time_minutes": round(seg_time, 2),
            "waste_collected_kg": round(waste_collected, 2),
            "trip_completed": trip.status == "COMPLETED",
            "reroute_occurred": reroute_occurred,
            "reroute_event": reroute_event,
        }
