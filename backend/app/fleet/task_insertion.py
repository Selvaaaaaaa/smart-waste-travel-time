"""Dynamic route insertion algorithm for tasks into active vehicle routes."""
from typing import List, Dict, Any, Optional, Tuple
from app.routing.graph import RoadNetworkGraph
from app.routing.rerouting import DynamicReroutingEngine
from app.ml.hybrid import predict_hybrid_eta
from app.fleet.fleet_scoring import calculate_allocation_score, evaluate_vehicle_safety_gate


class DynamicTaskInserter:
    """Evaluates incremental insertion of a task into an existing active vehicle route."""

    def __init__(self, graph: RoadNetworkGraph):
        self.graph = graph
        self.engine = DynamicReroutingEngine(self.graph)

    def evaluate_route_insertions(
        self,
        current_path: List[str],
        task_node: str,
        task_waste_kg: float,
        current_payload_kg: float,
        vehicle_capacity_kg: float,
        driver_current_work_min: float,
        driver_max_shift_min: float,
        environmental_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Evaluate all possible safe insertion points in current_path.
        Returns the best safe insertion or NO_SAFE_INSERTION.
        """
        if not current_path or len(current_path) < 2:
            current_path = ["DEPOT_CENTRAL", "LANDFILL_MAIN"]

        env_ctx = environmental_context or {}
        original_dist = self.graph.compute_path_distance(current_path)

        # Baseline original ETA
        orig_params = {
            "distance_km": max(0.5, original_dist),
            "waste_volume_tons": current_payload_kg / 1000.0,
            "weather_condition": env_ctx.get("weather_condition", "CLEAR"),
            "rainfall_mm": env_ctx.get("rainfall_mm", 0.0),
            "visibility_km": env_ctx.get("visibility_km", 10.0),
            "traffic_level": env_ctx.get("traffic_level", "LOW"),
            "congestion_index": env_ctx.get("congestion_index", 15.0),
            "event_level": env_ctx.get("event_level", "NONE"),
            "road_restriction_type": env_ctx.get("road_restriction_type", "NONE"),
        }
        orig_eta_res = predict_hybrid_eta(orig_params)
        original_eta_min = orig_eta_res["predicted_eta_minutes"]

        evaluated_positions: List[Dict[str, Any]] = []
        best_candidate: Optional[Dict[str, Any]] = None
        lowest_score = float("inf")

        # Evaluate inserting between every consecutive pair of stops (not after landfill)
        num_positions = len(current_path) - 1
        for i in range(num_positions):
            inserted_waypoints = current_path[:i + 1] + [task_node] + current_path[i + 1:]
            inserted_path = self.engine.candidate_generator.generate_path_for_waypoints(
                inserted_waypoints, weight_mode="balanced"
            )

            if not inserted_path:
                evaluated_positions.append({
                    "insertion_index": i + 1,
                    "is_safe": False,
                    "rejection_reason": "ROUTE_UNAVAILABLE: No traversable road connects to task node",
                })
                continue
            
            # Check closures along the inserted path
            has_closure = False
            for k in range(len(inserted_path) - 1):
                edge = self.graph.get_edge(inserted_path[k], inserted_path[k + 1])
                if edge and edge.get("is_blocked", False):
                    has_closure = True
                    break

            cand_dist = self.graph.compute_path_distance(inserted_path)
            added_dist = max(0.0, cand_dist - original_dist)

            # Predict hybrid ETA for inserted route
            cand_params = dict(orig_params)
            cand_params["distance_km"] = max(0.5, cand_dist)
            cand_params["waste_volume_tons"] = (current_payload_kg + task_waste_kg) / 1000.0
            cand_eta_res = predict_hybrid_eta(cand_params)
            cand_eta_min = cand_eta_res["predicted_eta_minutes"]
            added_eta = max(0.0, cand_eta_min - original_eta_min)

            # Safety Gate
            is_safe, rejection_reason = evaluate_vehicle_safety_gate(
                vehicle_status="AVAILABLE",
                current_payload_kg=current_payload_kg,
                task_waste_kg=task_waste_kg,
                vehicle_capacity_kg=vehicle_capacity_kg,
                driver_status="AVAILABLE",
                current_driver_work_min=driver_current_work_min,
                estimated_trip_min=cand_eta_min,
                max_driver_shift_min=driver_max_shift_min,
                route_is_blocked=has_closure,
            )

            score = None
            if is_safe:
                score = calculate_allocation_score(
                    predicted_eta_minutes=cand_eta_min,
                    additional_distance_km=added_dist,
                    projected_payload_kg=current_payload_kg + task_waste_kg,
                    vehicle_capacity_kg=vehicle_capacity_kg,
                    projected_shift_minutes=driver_current_work_min + cand_eta_min,
                    max_shift_minutes=driver_max_shift_min,
                    traffic_congestion_index=env_ctx.get("congestion_index", 15.0),
                    weather_severity_index=env_ctx.get("rainfall_mm", 0.0) * 1.5,
                    vehicle_workload_min=driver_current_work_min + cand_eta_min,
                    fleet_mean_workload_min=env_ctx.get("fleet_mean_workload_min", 180.0),
                    disruption_cost_factor=1.0 if not has_closure else 4.0,
                )
                if score < lowest_score:
                    lowest_score = score
                    best_candidate = {
                        "insertion_index": i + 1,
                        "inserted_path": inserted_path,
                        "additional_distance_km": round(added_dist, 2),
                        "predicted_eta_minutes": cand_eta_min,
                        "added_eta_minutes": round(added_eta, 2),
                        "allocation_score": score,
                        "selected_eta_model": cand_eta_res["selected_model"],
                        "prediction_spread_min": cand_eta_res.get("prediction_spread_minutes", 1.5),
                        "is_safe": True,
                    }

            evaluated_positions.append({
                "insertion_index": i + 1,
                "is_safe": is_safe,
                "rejection_reason": rejection_reason,
                "allocation_score": score,
                "additional_distance_km": round(added_dist, 2),
                "predicted_eta_minutes": cand_eta_min,
            })

        if best_candidate:
            return {
                "success": True,
                "best_insertion": best_candidate,
                "evaluated_positions": evaluated_positions,
            }

        return {
            "success": False,
            "rejection_reason": "NO_SAFE_INSERTION",
            "evaluated_positions": evaluated_positions,
        }

    def evaluate_emergency_insertion_across_fleet(
        self,
        vehicles: List[Dict[str, Any]],
        task_id: str,
        location_node: str,
        estimated_waste_kg: float,
        priority: str = "URGENT",
        environmental_context: Optional[Dict[str, Any]] = None,
        fleet_mean_workload_min: float = 180.0,
    ) -> Dict[str, Any]:
        """
        10-step Emergency Waste Request Optimization:
        1. Identify available vehicles.
        2. Remove unsafe vehicles.
        3. Generate possible insertion positions.
        4. Estimate incremental ETA.
        5. Estimate incremental distance.
        6. Check payload capacity.
        7. Check driver shift.
        8. Check active route restrictions.
        9. Calculate optimization score.
        10. Select the safest and most efficient feasible insertion.
        """
        env_ctx = environmental_context or {}
        env_ctx["fleet_mean_workload_min"] = fleet_mean_workload_min
        rejected_reasons: List[str] = []
        feasible_insertions: List[Dict[str, Any]] = []

        # Step 1 & 2: Identify available vehicles & filter out breakdown/maintenance/overloaded
        for v in vehicles:
            v_id = v["vehicle_id"]
            v_code = v["vehicle_code"]
            v_status = v["status"]
            v_cap = v["capacity_kg"]
            v_payload = v["current_payload_kg"]
            d_work = 480.0 - v["driver_shift_remaining_min"]
            d_max = 480.0

            if v_status in ["BREAKDOWN", "MAINTENANCE", "UNAVAILABLE"]:
                rejected_reasons.append(f"{v_code}: VEHICLE_{v_status}")
                continue

            # Step 6: Payload capacity check
            if (v_payload + estimated_waste_kg) > v_cap:
                rejected_reasons.append(
                    f"{v_code}: PAYLOAD_CAPACITY_EXCEEDED ({v_payload + estimated_waste_kg:.0f}kg > {v_cap:.0f}kg)"
                )
                continue

            current_route = v.get("current_route", [])

            # Step 3, 4, 5, 7, 8, 9:
            if current_route and len(current_route) >= 2 and v_status in ["ASSIGNED", "EN_ROUTE"]:
                ins_res = self.evaluate_route_insertions(
                    current_path=current_route,
                    task_node=location_node,
                    task_waste_kg=estimated_waste_kg,
                    current_payload_kg=v_payload,
                    vehicle_capacity_kg=v_cap,
                    driver_current_work_min=d_work,
                    driver_max_shift_min=d_max,
                    environmental_context=env_ctx,
                )
                if ins_res["success"]:
                    best = ins_res["best_insertion"]
                    feasible_insertions.append({
                        "vehicle_id": v_id,
                        "vehicle_code": v_code,
                        "insertion_position": best["insertion_index"],
                        "inserted_route": best["inserted_path"],
                        "incremental_eta_min": best["added_eta_minutes"],
                        "incremental_distance_km": best["additional_distance_km"],
                        "predicted_eta_minutes": best["predicted_eta_minutes"],
                        "allocation_score": best["allocation_score"],
                        "safety_status": "SAFE",
                        "vehicle_ref": v,
                    })
                else:
                    rejected_reasons.append(f"{v_code}: {ins_res.get('rejection_reason', 'NO_SAFE_INSERTION')}")
            else:
                # Idle / available vehicle route generation
                cand_path = self.engine.candidate_generator.generate_path_for_waypoints(
                    [v.get("current_location", "DEPOT_CENTRAL"), location_node, "LANDFILL_MAIN"],
                    weight_mode="balanced",
                )
                if not cand_path:
                    rejected_reasons.append(f"{v_code}: ROUTE_UNAVAILABLE")
                    continue

                # Check road restrictions & closures
                has_closure = False
                for k in range(len(cand_path) - 1):
                    edge = self.graph.get_edge(cand_path[k], cand_path[k + 1])
                    if edge and edge.get("is_blocked", False):
                        has_closure = True
                        break
                if has_closure:
                    rejected_reasons.append(f"{v_code}: ROAD_SEGMENT_IMPASSABLE")
                    continue

                cand_dist = self.graph.compute_path_distance(cand_path)
                eta_params = {
                    "distance_km": max(0.5, cand_dist),
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
                cand_eta = eta_res["predicted_eta_minutes"]

                if (d_work + cand_eta) > d_max:
                    rejected_reasons.append(f"{v_code}: DRIVER_SHIFT_EXCEEDED")
                    continue

                score = calculate_allocation_score(
                    predicted_eta_minutes=cand_eta,
                    additional_distance_km=cand_dist,
                    projected_payload_kg=v_payload + estimated_waste_kg,
                    vehicle_capacity_kg=v_cap,
                    projected_shift_minutes=d_work + cand_eta,
                    max_shift_minutes=d_max,
                    traffic_congestion_index=env_ctx.get("congestion_index", 15.0),
                    weather_severity_index=env_ctx.get("rainfall_mm", 0.0) * 1.5,
                    vehicle_workload_min=d_work + cand_eta,
                    fleet_mean_workload_min=fleet_mean_workload_min,
                )

                feasible_insertions.append({
                    "vehicle_id": v_id,
                    "vehicle_code": v_code,
                    "insertion_position": 1,
                    "inserted_route": cand_path,
                    "incremental_eta_min": round(cand_eta, 1),
                    "incremental_distance_km": round(cand_dist, 2),
                    "predicted_eta_minutes": round(cand_eta, 1),
                    "allocation_score": score,
                    "safety_status": "SAFE",
                    "vehicle_ref": v,
                })

        # Step 10: Select the safest and most efficient feasible insertion (lowest score)
        if not feasible_insertions:
            return {
                "task_id": task_id,
                "selected_vehicle_id": None,
                "insertion_position": None,
                "incremental_eta_min": None,
                "incremental_distance_km": None,
                "safety_status": "UNSAFE_REJECTED_ALL",
                "decision_reason": "NO_FEASIBLE_VEHICLE: All vehicles rejected due to safety or capacity constraints.",
                "rejected_vehicle_count": len(rejected_reasons),
                "rejected_candidate_reasons": rejected_reasons,
                "inserted_route": [],
                "allocation_score": None,
            }

        feasible_insertions.sort(key=lambda x: x["allocation_score"])
        winner = feasible_insertions[0]

        reason = (
            f"Vehicle {winner['vehicle_code']} selected at insertion position {winner['insertion_position']} "
            f"because it is the safest and most efficient candidate (Optimization Score: {winner['allocation_score']:.4f}, "
            f"Incremental ETA: +{winner['incremental_eta_min']}m, Incremental Dist: +{winner['incremental_distance_km']}km)."
        )

        return {
            "task_id": task_id,
            "selected_vehicle_id": winner["vehicle_id"],
            "insertion_position": winner["insertion_position"],
            "incremental_eta_min": winner["incremental_eta_min"],
            "incremental_distance_km": winner["incremental_distance_km"],
            "safety_status": "SAFE",
            "decision_reason": reason,
            "rejected_vehicle_count": len(rejected_reasons),
            "rejected_candidate_reasons": rejected_reasons,
            "inserted_route": winner["inserted_route"],
            "allocation_score": winner["allocation_score"],
            "winner_ref": winner["vehicle_ref"],
            "predicted_eta_minutes": winner["predicted_eta_minutes"],
        }

