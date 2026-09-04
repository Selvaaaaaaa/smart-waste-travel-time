"""Dynamic Rerouting Engine orchestrating candidate generation, Adaptive Hybrid ETA evaluation, and safety scoring.

Research & Simulation Disclaimer:
This is a deterministic simulation and research prototype.
It does not represent live municipal routing or live GPS data.
"""
from typing import List, Dict, Any, Optional, Tuple
from app.routing.graph import RoadNetworkGraph
from app.routing.route_candidates import CandidateRouteGenerator
from app.routing.route_scoring import RouteSafetyAndScoringEngine, EvaluatedCandidate
from app.ml.hybrid import predict_hybrid_eta


class DynamicReroutingEngine:
    """Core coordinator for real-time dynamic rerouting decisions."""

    def __init__(self, graph: RoadNetworkGraph):
        self.graph = graph
        self.candidate_generator = CandidateRouteGenerator(graph)
        self.scoring_engine = RouteSafetyAndScoringEngine(graph)

    def extract_path_context(self, path: List[str], base_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Aggregate environmental and operational context along a path for the Adaptive Hybrid ETA model."""
        base_ctx = base_context.copy() if base_context else {}
        total_dist = self.graph.compute_path_distance(path)

        # Aggregate dynamic conditions along path edges
        max_congestion = 15.0
        max_weather_penalty = 1.0
        has_blockage = False

        for i in range(len(path) - 1):
            edge = self.graph.get_edge(path[i], path[i + 1])
            if edge:
                c_factor = edge.get("congestion_factor", 1.0)
                # Map 1.0 -> 15.0 index, 3.0 -> 75.0 index
                max_congestion = max(max_congestion, c_factor * 25.0)
                max_weather_penalty = max(max_weather_penalty, edge.get("weather_penalty_factor", 1.0))
                if edge.get("is_blocked", False):
                    has_blockage = True

        traffic_lvl = "HIGH" if max_congestion >= 50.0 else ("MODERATE" if max_congestion >= 25.0 else "LOW")
        weather_cond = "HEAVY_RAIN" if max_weather_penalty >= 1.5 else base_ctx.get("weather_condition", "CLEAR")
        rainfall = 30.0 if max_weather_penalty >= 1.5 else base_ctx.get("rainfall_mm", 0.0)

        context = {
            "distance_km": max(0.5, total_dist),
            "waste_volume_tons": base_ctx.get("waste_volume_tons", 2.0),
            "weather_condition": weather_cond,
            "rainfall_mm": rainfall,
            "visibility_km": 5.0 if max_weather_penalty >= 1.5 else base_ctx.get("visibility_km", 10.0),
            "traffic_level": traffic_lvl,
            "congestion_index": max_congestion,
            "average_speed_kmh": max(10.0, 45.0 / (max_congestion / 15.0)),
            "event_level": base_ctx.get("event_level", "NONE"),
            "event_radius": base_ctx.get("event_radius", 0.0),
            "road_restriction_type": "CLOSURE" if has_blockage else base_ctx.get("road_restriction_type", "NONE"),
            "road_restriction_severity": "FULL" if has_blockage else base_ctx.get("road_restriction_severity", "NONE"),
            "hour_of_day": base_ctx.get("hour_of_day", 10),
            "day_of_week": base_ctx.get("day_of_week", 2),
        }
        return context

    def evaluate_and_reroute(
        self,
        current_node: str,
        remaining_stops: List[str],
        destination_node: str,
        current_path: List[str],
        current_payload_kg: float,
        vehicle_capacity_kg: float,
        expected_remaining_waste_kg: float,
        elapsed_time_minutes: float,
        max_shift_hours: float,
        trigger_type: str = "MANUAL",
        trigger_details: Optional[Dict[str, Any]] = None,
        base_context: Optional[Dict[str, Any]] = None,
        strategies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate candidate routes, predict ETAs with Adaptive Hybrid model, evaluate safety, and decide optimal route."""
        # 1. Generate path candidates
        candidates_raw = self.candidate_generator.generate_candidates(
            current_node=current_node,
            remaining_stops=remaining_stops,
            destination_node=destination_node,
            strategies=strategies,
        )

        candidates_data = []
        for cand in candidates_raw:
            c_dict = cand.to_dict()
            p_context = self.extract_path_context(cand.path, base_context)

            # Predict ETA using Adaptive Hybrid Model (Phase 5)
            try:
                hybrid_res = predict_hybrid_eta(p_context)
                c_dict["predicted_eta_minutes"] = hybrid_res["predicted_eta_minutes"]
                c_dict["baseline_eta_minutes"] = hybrid_res["baseline_eta_minutes"]
                c_dict["hybrid_eta_minutes"] = hybrid_res["predicted_eta_minutes"]
                c_dict["eta_uncertainty_minutes"] = hybrid_res.get("prediction_spread_minutes") or 2.5
            except Exception:
                # Fallback calculation if model file unavailable
                base_time = c_dict["base_traversal_time_min"]
                c_dict["predicted_eta_minutes"] = base_time
                c_dict["baseline_eta_minutes"] = round(c_dict["total_distance_km"] / 25.0 * 60.0, 2)
                c_dict["hybrid_eta_minutes"] = base_time
                c_dict["eta_uncertainty_minutes"] = 1.0

            candidates_data.append(c_dict)

        # 2. Score candidates and enforce hard safety gates
        scored_candidates = self.scoring_engine.score_candidates(
            candidates_raw=candidates_data,
            current_payload_kg=current_payload_kg,
            vehicle_capacity_kg=vehicle_capacity_kg,
            expected_waste_kg=expected_remaining_waste_kg,
            elapsed_time_minutes=elapsed_time_minutes,
            max_shift_hours=max_shift_hours,
        )

        # 3. Find selected candidate
        selected_candidate = next((c for c in scored_candidates if c.is_selected), None)
        if not selected_candidate and scored_candidates:
            # If none selected (e.g. all unsafe), fallback to first candidate marked with rejection
            selected_candidate = scored_candidates[0]

        # 4. Check if reroute is beneficial or required compared to current path
        # Check current path safety
        current_safe, current_violations = self.scoring_engine.evaluate_safety(
            candidate_path=current_path,
            current_payload_kg=current_payload_kg,
            vehicle_capacity_kg=vehicle_capacity_kg,
            expected_waste_kg=expected_remaining_waste_kg,
            elapsed_time_minutes=elapsed_time_minutes,
            predicted_trip_minutes=selected_candidate.predicted_eta_minutes if selected_candidate else 30.0,
            max_shift_hours=max_shift_hours,
        )

        is_path_different = (
            selected_candidate is not None
            and selected_candidate.path != current_path
        )
        
        # Current path ETA
        curr_ctx = self.extract_path_context(current_path, base_context)
        try:
            curr_eta_res = predict_hybrid_eta(curr_ctx)
            current_eta = curr_eta_res["predicted_eta_minutes"]
        except Exception:
            current_eta = round(self.graph.compute_path_distance(current_path) / 25.0 * 60.0, 2)

        new_eta = selected_candidate.predicted_eta_minutes if selected_candidate else current_eta
        time_saved = round(max(0.0, current_eta - new_eta), 2)
        dist_diff = round(
            (selected_candidate.total_distance_km if selected_candidate else 0.0)
            - self.graph.compute_path_distance(current_path),
            2,
        )

        should_reroute = False
        decision_rationale = "Current route remains optimal."

        if not current_safe:
            should_reroute = True
            decision_rationale = (
                f"Reroute mandated by safety violation on current route: {'; '.join(current_violations)}. "
                f"Switched to {selected_candidate.strategy}."
            )
        elif is_path_different and time_saved >= 3.0:
            should_reroute = True
            decision_rationale = (
                f"Dynamic rerouting to {selected_candidate.strategy} reduces predicted travel time by {time_saved:.1f} min "
                f"({((time_saved / max(current_eta, 1.0)) * 100):.1f}% time savings)."
            )
        elif trigger_type in ["ROAD_CLOSURE", "ROAD_BLOCKAGE", "INJECTED_DISRUPTION"]:
            should_reroute = True
            decision_rationale = (
                f"Rerouted to {selected_candidate.strategy} in response to detected environmental disruption "
                f"({trigger_type})."
            )
        elif trigger_type == "MANUAL" and is_path_different:
            should_reroute = True
            decision_rationale = f"Manual reroute executed to {selected_candidate.strategy} strategy."

        return {
            "reroute_executed": should_reroute,
            "trigger_type": trigger_type,
            "decision_rationale": decision_rationale,
            "previous_path": current_path,
            "new_path": selected_candidate.path if selected_candidate else current_path,
            "previous_eta_minutes": current_eta,
            "new_eta_minutes": new_eta,
            "time_saved_minutes": time_saved if should_reroute else 0.0,
            "distance_difference_km": dist_diff if should_reroute else 0.0,
            "selected_candidate": selected_candidate.to_dict() if selected_candidate else None,
            "all_candidates": [c.to_dict() for c in scored_candidates],
        }
