"""Route Safety and Multi-Objective Scoring Engine.

Safety-First Constraint Engine:
- Capacity hard gate (payload <= vehicle_capacity)
- Driver shift hard gate (elapsed + predicted <= max_shift_hours * 60)
- Road impassability gate (no traversing closed segments)

Multi-Objective Scoring Formula:
Score = w_eta * (ETA / max_eta) + w_dist * (Dist / max_dist) + w_disr * disruption_penalty
Lower score is superior. Unsafe routes are permanently disqualified.
"""
from typing import List, Dict, Any, Optional, Tuple
from app.routing.graph import RoadNetworkGraph


class EvaluatedCandidate:
    def __init__(
        self,
        strategy: str,
        path: List[str],
        path_coordinates: List[Dict[str, float]],
        total_distance_km: float,
        predicted_eta_minutes: float,
        baseline_eta_minutes: float,
        hybrid_eta_minutes: float,
        eta_uncertainty_minutes: float,
        safety_valid: bool,
        safety_violations: List[str],
        optimization_score: float,
        is_selected: bool = False,
        rejection_reason: Optional[str] = None,
    ):
        self.strategy = strategy
        self.path = path
        self.path_coordinates = path_coordinates
        self.total_distance_km = total_distance_km
        self.predicted_eta_minutes = predicted_eta_minutes
        self.baseline_eta_minutes = baseline_eta_minutes
        self.hybrid_eta_minutes = hybrid_eta_minutes
        self.eta_uncertainty_minutes = eta_uncertainty_minutes
        self.safety_valid = safety_valid
        self.safety_violations = safety_violations
        self.optimization_score = optimization_score
        self.is_selected = is_selected
        self.rejection_reason = rejection_reason

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy,
            "path": self.path,
            "path_coordinates": self.path_coordinates,
            "total_distance_km": round(self.total_distance_km, 2),
            "predicted_eta_minutes": round(self.predicted_eta_minutes, 2),
            "baseline_eta_minutes": round(self.baseline_eta_minutes, 2),
            "hybrid_eta_minutes": round(self.hybrid_eta_minutes, 2),
            "eta_uncertainty_minutes": round(self.eta_uncertainty_minutes, 2),
            "safety_valid": self.safety_valid,
            "safety_violations": self.safety_violations,
            "optimization_score": round(self.optimization_score, 4),
            "is_selected": self.is_selected,
            "rejection_reason": self.rejection_reason,
        }


class RouteSafetyAndScoringEngine:
    """Evaluates candidate routes against hard safety constraints and computes multi-objective scores."""

    def __init__(
        self,
        graph: RoadNetworkGraph,
        w_eta: float = 0.50,
        w_dist: float = 0.30,
        w_disruption: float = 0.20,
    ):
        self.graph = graph
        self.w_eta = w_eta
        self.w_dist = w_dist
        self.w_disruption = w_disruption

    def evaluate_safety(
        self,
        candidate_path: List[str],
        current_payload_kg: float,
        vehicle_capacity_kg: float,
        expected_waste_kg: float,
        elapsed_time_minutes: float,
        predicted_trip_minutes: float,
        max_shift_hours: float,
    ) -> Tuple[bool, List[str]]:
        """Validate candidate path against hard safety rules."""
        violations = []

        # 1. Payload capacity check
        total_projected_waste = current_payload_kg + expected_waste_kg
        if total_projected_waste > vehicle_capacity_kg:
            overload = round(total_projected_waste - vehicle_capacity_kg, 1)
            violations.append(
                f"Payload capacity exceeded by {overload} kg (projected {total_projected_waste} kg > max {vehicle_capacity_kg} kg)"
            )

        # 2. Driver shift hours fatigue check
        max_shift_minutes = max_shift_hours * 60.0
        projected_total_time = elapsed_time_minutes + predicted_trip_minutes
        if projected_total_time > max_shift_minutes:
            overtime = round(projected_total_time - max_shift_minutes, 1)
            violations.append(
                f"Driver maximum shift time exceeded by {overtime} min (projected {projected_total_time:.1f} min > limit {max_shift_minutes:.1f} min)"
            )

        # 3. Impassable road segment check
        for i in range(len(candidate_path) - 1):
            edge = self.graph.get_edge(candidate_path[i], candidate_path[i + 1])
            if edge and edge.get("is_blocked", False):
                violations.append(
                    f"Path traverses impassable/blocked road segment ({candidate_path[i]} -> {candidate_path[i+1]})"
                )

        return (len(violations) == 0, violations)

    def calculate_disruption_penalty(self, candidate_path: List[str]) -> float:
        """Calculate penalty factor based on congestion and weather exposure along the path."""
        if not candidate_path or len(candidate_path) < 2:
            return 0.0

        congestion_sum = 0.0
        weather_sum = 0.0
        count = 0

        for i in range(len(candidate_path) - 1):
            edge = self.graph.get_edge(candidate_path[i], candidate_path[i + 1])
            if edge:
                congestion_sum += max(0.0, edge.get("congestion_factor", 1.0) - 1.0)
                weather_sum += max(0.0, edge.get("weather_penalty_factor", 1.0) - 1.0)
                count += 1

        if count == 0:
            return 0.0

        avg_congestion_excess = congestion_sum / count
        avg_weather_excess = weather_sum / count
        # Disruption penalty bounded between 0.0 and 2.0
        return min(2.0, avg_congestion_excess * 0.6 + avg_weather_excess * 0.4)

    def score_candidates(
        self,
        candidates_raw: List[Dict[str, Any]],
        current_payload_kg: float,
        vehicle_capacity_kg: float,
        expected_waste_kg: float,
        elapsed_time_minutes: float,
        max_shift_hours: float,
    ) -> List[EvaluatedCandidate]:
        """Score candidate paths and pick the best safe route."""
        if not candidates_raw:
            return []

        # Find max metrics for normalization
        max_eta = max([c["hybrid_eta_minutes"] for c in candidates_raw] + [1.0])
        max_dist = max([c["total_distance_km"] for c in candidates_raw] + [1.0])

        evaluated_list: List[EvaluatedCandidate] = []

        for cand in candidates_raw:
            path = cand["path"]
            dist_km = cand["total_distance_km"]
            predicted_eta = cand["hybrid_eta_minutes"]
            baseline_eta = cand.get("baseline_eta_minutes", predicted_eta)
            hybrid_eta = cand.get("hybrid_eta_minutes", predicted_eta)
            uncertainty = cand.get("eta_uncertainty_minutes", 0.0)

            # Check hard safety constraints
            is_safe, violations = self.evaluate_safety(
                candidate_path=path,
                current_payload_kg=current_payload_kg,
                vehicle_capacity_kg=vehicle_capacity_kg,
                expected_waste_kg=expected_waste_kg,
                elapsed_time_minutes=elapsed_time_minutes,
                predicted_trip_minutes=predicted_eta,
                max_shift_hours=max_shift_hours,
            )

            # Compute Disruption Penalty
            disruption_pen = self.calculate_disruption_penalty(path)

            # Multi-objective score
            if not is_safe:
                score = 999999.0
                rejection = "; ".join(violations)
            else:
                norm_eta = predicted_eta / max_eta
                norm_dist = dist_km / max_dist
                score = (self.w_eta * norm_eta) + (self.w_dist * norm_dist) + (self.w_disruption * disruption_pen)
                rejection = None

            evaluated_list.append(
                EvaluatedCandidate(
                    strategy=cand["strategy"],
                    path=path,
                    path_coordinates=cand.get("path_coordinates", []),
                    total_distance_km=dist_km,
                    predicted_eta_minutes=predicted_eta,
                    baseline_eta_minutes=baseline_eta,
                    hybrid_eta_minutes=hybrid_eta,
                    eta_uncertainty_minutes=uncertainty,
                    safety_valid=is_safe,
                    safety_violations=violations,
                    optimization_score=score,
                    is_selected=False,
                    rejection_reason=rejection,
                )
            )

        # Select candidate with lowest optimization score among safe candidates
        safe_candidates = [c for c in evaluated_list if c.safety_valid]
        if safe_candidates:
            best_cand = min(safe_candidates, key=lambda c: c.optimization_score)
            best_cand.is_selected = True
        elif evaluated_list:
            # If all are unsafe, mark earliest safe subset or none
            pass

        return evaluated_list
