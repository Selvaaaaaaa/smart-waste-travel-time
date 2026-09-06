"""Task allocation engine for assigning collection tasks to the safest and most efficient vehicle."""
import logging
from typing import Dict, List, Any, Optional, Tuple
from app.routing.graph import RoadNetworkGraph, get_default_network_graph
from app.routing.rerouting import DynamicReroutingEngine
from app.ml.hybrid import predict_hybrid_eta
from app.fleet.fleet_scoring import calculate_allocation_score, evaluate_vehicle_safety_gate
from app.fleet.fleet_state import FleetStateManager, fleet_state_manager
from app.fleet.task_insertion import DynamicTaskInserter
from app.schemas.fleet import CandidateVehicleEvaluation, TaskAssignResponse

logger = logging.getLogger(__name__)


class TaskAllocator:
    """Orchestrates candidate filtering, hybrid ETA evaluation, multi-criteria scoring, and assignment."""

    def __init__(
        self,
        graph: Optional[RoadNetworkGraph] = None,
        state_mgr: Optional[FleetStateManager] = None,
    ):
        self.graph = graph or get_default_network_graph()
        self.state_mgr = state_mgr or fleet_state_manager
        self.engine = DynamicReroutingEngine(self.graph)
        self.inserter = DynamicTaskInserter(self.graph)

    def allocate_task(
        self,
        task_id: str,
        location_node: str,
        estimated_waste_kg: float,
        priority: str = "NORMAL",
        request_type: str = "SCHEDULED_COLLECTION",
        environmental_context: Optional[Dict[str, Any]] = None,
        strategy: str = "ADVANCED_OPTIMIZER",
    ) -> TaskAssignResponse:
        """
        Evaluate all fleet vehicles for a given task.
        Filters unsafe vehicles, computes Hybrid ETA, scores safe candidates, and assigns winner.
        Supports strategy="ADVANCED_OPTIMIZER" (multi-objective + workload balancing)
        or strategy="BASELINE" (nearest/first safe vehicle without workload optimization).
        """
        env_ctx = environmental_context or {}
        vehicles = self.state_mgr.get_all_vehicles()
        evaluations: List[CandidateVehicleEvaluation] = []
        safe_candidates: List[Tuple[float, Dict[str, Any], CandidateVehicleEvaluation]] = []

        wl_metrics = self.state_mgr.get_workload_metrics()
        fleet_mean_wl = wl_metrics["mean_workload_min"]

        for v in vehicles:
            v_id = v["vehicle_id"]
            v_code = v["vehicle_code"]
            v_status = v["status"]
            v_cap = v["capacity_kg"]
            v_payload = v["current_payload_kg"]
            v_loc = v["current_location"]
            d_work = 480.0 - v["driver_shift_remaining_min"]
            d_max = 480.0

            # 1. Immediate Operational Check
            if v_status in ["BREAKDOWN", "MAINTENANCE", "UNAVAILABLE"]:
                evaluations.append(
                    CandidateVehicleEvaluation(
                        vehicle_id=v_id,
                        vehicle_code=v_code,
                        is_safe=False,
                        rejection_reason=f"VEHICLE_{v_status}",
                        projected_payload_kg=v_payload + estimated_waste_kg,
                        projected_shift_minutes=d_work,
                        selected_eta_model="NONE",
                        prediction_spread_min=0.0,
                    )
                )
                continue

            # 2. Capacity Check before route building
            if (v_payload + estimated_waste_kg) > v_cap:
                evaluations.append(
                    CandidateVehicleEvaluation(
                        vehicle_id=v_id,
                        vehicle_code=v_code,
                        is_safe=False,
                        rejection_reason=(
                            f"PAYLOAD_CAPACITY_EXCEEDED: Projected {v_payload + estimated_waste_kg:.0f}kg "
                            f"exceeds capacity {v_cap:.0f}kg"
                        ),
                        projected_payload_kg=v_payload + estimated_waste_kg,
                        projected_shift_minutes=d_work,
                        selected_eta_model="NONE",
                        prediction_spread_min=0.0,
                    )
                )
                continue

            # 3. Candidate Route Formulation
            cand_path: Optional[List[str]] = None
            added_dist = 0.0

            if v.get("current_route") and len(v["current_route"]) >= 2 and v_status in ["ASSIGNED", "EN_ROUTE"]:
                # Try dynamic insertion
                ins_res = self.inserter.evaluate_route_insertions(
                    current_path=v["current_route"],
                    task_node=location_node,
                    task_waste_kg=estimated_waste_kg,
                    current_payload_kg=v_payload,
                    vehicle_capacity_kg=v_cap,
                    driver_current_work_min=d_work,
                    driver_max_shift_min=d_max,
                    environmental_context=env_ctx,
                )
                if ins_res["success"]:
                    best_ins = ins_res["best_insertion"]
                    cand_path = best_ins["inserted_path"]
                    added_dist = best_ins["additional_distance_km"]
                    pred_eta = best_ins["predicted_eta_minutes"]
                    selected_model = best_ins["selected_eta_model"]
                    spread = best_ins["prediction_spread_min"]
                    if strategy == "BASELINE":
                        from app.fleet.fleet_scoring import calculate_baseline_score
                        score = calculate_baseline_score(added_dist, pred_eta)
                    else:
                        score = best_ins["allocation_score"]
                else:
                    evaluations.append(
                        CandidateVehicleEvaluation(
                            vehicle_id=v_id,
                            vehicle_code=v_code,
                            is_safe=False,
                            rejection_reason=ins_res.get("rejection_reason", "NO_SAFE_INSERTION"),
                            projected_payload_kg=v_payload + estimated_waste_kg,
                            projected_shift_minutes=d_work,
                            selected_eta_model="NONE",
                            prediction_spread_min=0.0,
                        )
                    )
                    continue
            else:
                cand_path = self.engine.candidate_generator.generate_path_for_waypoints(
                    [v_loc, location_node, "LANDFILL_MAIN"], weight_mode="balanced"
                )
                if not cand_path:
                    evaluations.append(
                        CandidateVehicleEvaluation(
                            vehicle_id=v_id,
                            vehicle_code=v_code,
                            is_safe=False,
                            rejection_reason="ROUTE_UNAVAILABLE: Unconnected or blocked road to task location",
                            projected_payload_kg=v_payload + estimated_waste_kg,
                            projected_shift_minutes=d_work,
                            selected_eta_model="NONE",
                            prediction_spread_min=0.0,
                        )
                    )
                    continue

                added_dist = self.graph.compute_path_distance(cand_path)

                # Check road closures along cand_path
                has_closure = False
                for k in range(len(cand_path) - 1):
                    edge = self.graph.get_edge(cand_path[k], cand_path[k + 1])
                    if edge and edge.get("is_blocked", False):
                        has_closure = True
                        break

                if has_closure:
                    evaluations.append(
                        CandidateVehicleEvaluation(
                            vehicle_id=v_id,
                            vehicle_code=v_code,
                            is_safe=False,
                            rejection_reason="ROAD_SEGMENT_IMPASSABLE: Route traverses blocked road segment",
                            projected_payload_kg=v_payload + estimated_waste_kg,
                            projected_shift_minutes=d_work,
                            selected_eta_model="NONE",
                            prediction_spread_min=0.0,
                        )
                    )
                    continue

                # Adaptive Hybrid ETA prediction (NO DATA LEAKAGE: strictly pre-trip features)
                eta_params = {
                    "distance_km": max(0.5, added_dist),
                    "waste_volume_tons": (v_payload + estimated_waste_kg) / 1000.0,
                    "weather_condition": env_ctx.get("weather_condition", "CLEAR"),
                    "rainfall_mm": env_ctx.get("rainfall_mm", 0.0),
                    "visibility_km": env_ctx.get("visibility_km", 10.0),
                    "traffic_level": env_ctx.get("traffic_level", "LOW"),
                    "congestion_index": env_ctx.get("congestion_index", 15.0),
                    "event_level": env_ctx.get("event_level", "NONE"),
                    "road_restriction_type": env_ctx.get("road_restriction_type", "NONE"),
                }
                eta_res = predict_hybrid_eta(eta_params)
                pred_eta = eta_res["predicted_eta_minutes"]
                selected_model = eta_res["selected_model"]
                spread = eta_res.get("prediction_spread_minutes", 1.5)

                # Safety Gate check on driver shift and severe weather
                is_safe, rej_reason = evaluate_vehicle_safety_gate(
                    vehicle_status=v_status,
                    current_payload_kg=v_payload,
                    task_waste_kg=estimated_waste_kg,
                    vehicle_capacity_kg=v_cap,
                    driver_status="AVAILABLE",
                    current_driver_work_min=d_work,
                    estimated_trip_min=pred_eta,
                    max_driver_shift_min=d_max,
                    route_is_blocked=False,
                    weather_condition=env_ctx.get("weather_condition", "CLEAR"),
                )

                if not is_safe:
                    evaluations.append(
                        CandidateVehicleEvaluation(
                            vehicle_id=v_id,
                            vehicle_code=v_code,
                            is_safe=False,
                            rejection_reason=rej_reason,
                            projected_payload_kg=v_payload + estimated_waste_kg,
                            projected_shift_minutes=d_work + pred_eta,
                            selected_eta_model=selected_model,
                            prediction_spread_min=spread,
                        )
                    )
                    continue

                if strategy == "BASELINE":
                    from app.fleet.fleet_scoring import calculate_baseline_score
                    score = calculate_baseline_score(added_dist, pred_eta)
                else:
                    score = calculate_allocation_score(
                        predicted_eta_minutes=pred_eta,
                        additional_distance_km=added_dist,
                        projected_payload_kg=v_payload + estimated_waste_kg,
                        vehicle_capacity_kg=v_cap,
                        projected_shift_minutes=d_work + pred_eta,
                        max_shift_minutes=d_max,
                        traffic_congestion_index=env_ctx.get("congestion_index", 15.0),
                        weather_severity_index=env_ctx.get("rainfall_mm", 0.0) * 1.5,
                        vehicle_workload_min=d_work + pred_eta,
                        fleet_mean_workload_min=fleet_mean_wl,
                        disruption_cost_factor=1.0,
                    )

            # Record safe candidate
            eval_item = CandidateVehicleEvaluation(
                vehicle_id=v_id,
                vehicle_code=v_code,
                is_safe=True,
                rejection_reason=None,
                allocation_score=score,
                predicted_eta_min=round(pred_eta, 1),
                additional_distance_km=round(added_dist, 2),
                projected_payload_kg=round(v_payload + estimated_waste_kg, 1),
                projected_shift_minutes=round(d_work + pred_eta, 1),
                selected_eta_model=selected_model,
                prediction_spread_min=round(spread, 2),
            )
            evaluations.append(eval_item)
            safe_candidates.append((score, {
                "vehicle": v,
                "path": cand_path,
                "pred_eta": pred_eta,
                "score": score,
                "added_dist": added_dist,
                "selected_model": selected_model,
            }, eval_item))

        # 4. Selection & Assignment
        if not safe_candidates:
            return TaskAssignResponse(
                task_id=task_id,
                status="DEFERRED",
                selection_reason="NO_SAFE_VEHICLE: All candidate vehicles were rejected by safety constraints.",
                candidate_evaluations=evaluations,
                safety_result="REJECTED_ALL_CANDIDATES",
            )

        # Sort by lowest score (best)
        safe_candidates.sort(key=lambda x: x[0])
        best_score, best_info, best_eval = safe_candidates[0]
        sel_veh = best_info["vehicle"]
        sel_path = best_info["path"]
        sel_eta = best_info["pred_eta"]
        sel_dist = best_info["added_dist"]

        # Update vehicle in fleet state manager with workload tracking
        new_payload = sel_veh["current_payload_kg"] + estimated_waste_kg
        new_remaining_shift = max(0.0, sel_veh["driver_shift_remaining_min"] - sel_eta)
        existing_assigned = list(sel_veh.get("assigned_tasks", []))
        if task_id not in existing_assigned:
            existing_assigned.append(task_id)

        prior_workload = float(sel_veh.get("estimated_workload_minutes", 0.0))
        prior_dist = float(sel_veh.get("route_distance_km", 0.0))

        self.state_mgr.update_vehicle(
            sel_veh["vehicle_id"],
            current_payload_kg=new_payload,
            driver_shift_remaining_min=new_remaining_shift,
            current_route=sel_path,
            current_task_id=task_id,
            assigned_tasks=existing_assigned,
            estimated_workload_minutes=round(prior_workload + sel_eta, 1),
            route_distance_km=round(prior_dist + sel_dist, 2),
            status="ASSIGNED",
            estimated_available_time_min=round(sel_eta, 1),
        )

        reason = (
            f"Vehicle {sel_veh['vehicle_code']} selected ({strategy} Score: {best_score:.4f}, ETA: {sel_eta:.1f}m, "
            f"Payload: {new_payload:.0f}/{sel_veh['capacity_kg']:.0f}kg, Distance: {sel_dist:.1f}km). "
            f"Passed all physical capacity, shift fatigue, and impassable road safety checks."
        )

        return TaskAssignResponse(
            task_id=task_id,
            status="ASSIGNED",
            selected_vehicle_id=sel_veh["vehicle_id"],
            selected_driver_id=sel_veh.get("driver_id"),
            selected_route=sel_path,
            predicted_eta_minutes=round(sel_eta, 1),
            allocation_score=best_score,
            selection_reason=reason,
            candidate_evaluations=evaluations,
            safety_result="SAFE",
        )

