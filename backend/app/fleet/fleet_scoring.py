"""Multi-criteria transparent task allocation scoring, workload balancing, and strict safety filtering."""
import math
from typing import Dict, Any, Optional, Tuple


def normalize(value: float, min_val: float, max_val: float) -> float:
    """Clamp and normalize value into [0.0, 1.0]."""
    if max_val <= min_val:
        return 0.0
    return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


def calculate_allocation_score(
    predicted_eta_minutes: float,
    additional_distance_km: float,
    projected_payload_kg: float,
    vehicle_capacity_kg: float,
    projected_shift_minutes: float,
    max_shift_minutes: float,
    traffic_congestion_index: float = 15.0,
    weather_severity_index: float = 0.0,
    vehicle_workload_min: float = 0.0,
    fleet_mean_workload_min: float = 0.0,
    disruption_cost_factor: float = 1.0,
) -> float:
    """
    Calculate transparent Phase 8 multi-objective allocation score.
    LOWER SCORE = BETTER.

    TOTAL SCORE =
        0.30 * ETA_SCORE
      + 0.20 * DISTANCE_SCORE
      + 0.15 * PAYLOAD_SCORE
      + 0.10 * SHIFT_SCORE
      + 0.10 * TRAFFIC_SCORE
      + 0.05 * WEATHER_SCORE
      + 0.10 * WORKLOAD_BALANCE_SCORE (normalized deviation from fleet mean)
    """
    eta_score = normalize(predicted_eta_minutes, 0.0, 120.0)
    distance_score = normalize(additional_distance_km, 0.0, 50.0)
    payload_score = normalize(projected_payload_kg, 0.0, max(1.0, vehicle_capacity_kg))
    shift_score = normalize(projected_shift_minutes, 0.0, max(1.0, max_shift_minutes))
    traffic_score = normalize(traffic_congestion_index, 0.0, 100.0)
    weather_score = normalize(weather_severity_index, 0.0, 100.0)

    # Workload balance component: deviation of this vehicle from fleet average
    # If deviation is 0 (equal to mean), score is 0.0 (best). If far from mean, penalty approaches 1.0
    workload_deviation = abs(vehicle_workload_min - fleet_mean_workload_min)
    workload_balance_score = normalize(workload_deviation, 0.0, max_shift_minutes / 2.0)

    total_score = (
        0.30 * eta_score
        + 0.20 * distance_score
        + 0.15 * payload_score
        + 0.10 * shift_score
        + 0.10 * traffic_score
        + 0.05 * weather_score
        + 0.10 * workload_balance_score
    )
    return round(total_score, 4)


def calculate_baseline_score(
    additional_distance_km: float,
    predicted_eta_minutes: float,
) -> float:
    """
    Baseline scoring strategy: Nearest/first available vehicle without workload or environmental optimization.
    Evaluates purely distance and ETA.
    """
    dist_score = normalize(additional_distance_km, 0.0, 50.0)
    eta_score = normalize(predicted_eta_minutes, 0.0, 120.0)
    return round(0.60 * dist_score + 0.40 * eta_score, 4)


def calculate_workload_balance(
    vehicle_workload_minutes: Dict[str, float],
    max_shift_minutes: float = 480.0,
) -> Tuple[float, float, float]:
    """
    Calculate fleet-wide workload balance metric:
        WORKLOAD_BALANCE = 1 - normalized_deviation_from_fleet_average
    Higher = better balance (1.0 = perfect equality across all vehicles).
    Returns (fleet_mean, fleet_std_dev, workload_balance_metric).
    """
    if not vehicle_workload_minutes:
        return 0.0, 0.0, 1.0

    vals = list(vehicle_workload_minutes.values())
    n = len(vals)
    mean_val = sum(vals) / max(1, n)
    variance = sum((x - mean_val) ** 2 for x in vals) / max(1, n)
    std_dev = math.sqrt(variance)

    # Normalized deviation from fleet average
    norm_dev = normalize(std_dev, 0.0, max_shift_minutes / 2.0)
    workload_balance = round(max(0.0, min(1.0, 1.0 - norm_dev)), 4)

    return round(mean_val, 2), round(std_dev, 2), workload_balance


def evaluate_vehicle_safety_gate(
    vehicle_status: str,
    current_payload_kg: float,
    task_waste_kg: float,
    vehicle_capacity_kg: float,
    driver_status: str,
    current_driver_work_min: float,
    estimated_trip_min: float,
    max_driver_shift_min: float,
    route_is_blocked: bool = False,
    weather_condition: str = "CLEAR",
    has_valid_route: bool = True,
) -> Tuple[bool, Optional[str]]:
    """
    Strict safety gate validation evaluated BEFORE scoring.
    Safety is a HARD CONSTRAINT. Unsafe candidates are marked UNSAFE and rejected.
    Returns (is_safe, rejection_reason).
    """
    # 1. Operational status
    if vehicle_status == "BREAKDOWN":
        return False, "VEHICLE_BREAKDOWN"
    if vehicle_status in ["MAINTENANCE", "UNAVAILABLE", "OVERLOADED"]:
        return False, f"VEHICLE_{vehicle_status}"
    if vehicle_status == "OFF_DUTY":
        return False, "VEHICLE_UNAVAILABLE"

    # 2. Driver status
    if driver_status in ["OFF_DUTY", "UNAVAILABLE"]:
        return False, "DRIVER_SHIFT_EXCEEDED"

    # 3. Physical payload capacity
    projected_payload = current_payload_kg + task_waste_kg
    if projected_payload > vehicle_capacity_kg:
        return (
            False,
            f"PAYLOAD_CAPACITY_EXCEEDED: Projected {projected_payload:.1f}kg exceeds capacity {vehicle_capacity_kg:.1f}kg",
        )

    # 4. Driver fatigue and shift constraint
    projected_work = current_driver_work_min + estimated_trip_min
    if projected_work > max_driver_shift_min:
        return (
            False,
            f"DRIVER_SHIFT_EXCEEDED: Projected work {projected_work:.1f}m exceeds max shift {max_driver_shift_min:.1f}m",
        )

    # 5. Route connectivity and road closure
    if not has_valid_route:
        return False, "ROUTE_UNAVAILABLE: No traversable path exists to task location"

    if route_is_blocked:
        return False, "ROUTE_UNAVAILABLE: Unpassable road closure on route (ROAD_SEGMENT_IMPASSABLE)"


    # 6. Severe weather constraint
    if weather_condition in ["HURRICANE", "FLOOD", "SEVERE_STORM"]:
        return False, f"SEVERE_WEATHER_RESTRICTION: Hazardous weather conditions ({weather_condition})"

    return True, None

