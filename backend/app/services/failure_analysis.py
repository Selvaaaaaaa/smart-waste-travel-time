import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Standard Failure Categories defined for research evaluation (Context-Aware and Hybrid)
FAILURE_CATEGORIES = [
    "UNDER_PREDICTION",
    "OVER_PREDICTION",
    "CONTEXT_MISMATCH",
    "RARE_CONDITION",
    "ROAD_RESTRICTION_MISMATCH",
    "EVENT_IMPACT_MISMATCH",
    "WEATHER_IMPACT_MISMATCH",
    "HIGH_WASTE_EFFECT",
    "SAFETY_CONSTRAINT",
    "MODEL_UNCERTAINTY",
    "HYBRID_SELECTION_ERROR",
    "HYBRID_BASELINE_SELECTION",
    "HYBRID_CONTEXT_SELECTION",
    "MODEL_ERROR",
]


def classify_failure_case(run: Dict[str, Any], model_type: str = "CONTEXT_AWARE") -> str:
    """
    Explainable, rule-based classification of travel-time prediction and operational failure cases.
    Supports Context-Aware and Adaptive Hybrid model evaluation.
    """
    # 1. Safety violation
    if not run.get("is_safe", True) or run.get("status") == "UNSAFE_ASSIGNMENT":
        return "SAFETY_CONSTRAINT"

    params = run.get("parameters", {})
    context_eta = run.get("context_aware_eta_minutes")
    baseline_eta = run.get("baseline_eta_minutes")
    hybrid_eta = run.get("hybrid_eta_minutes") or run.get("predicted_eta_minutes")
    actual_eta = run.get("actual_travel_minutes") or run.get("simulated_actual_minutes")
    
    context_error = run.get("context_aware_error_minutes", 0.0)
    baseline_error = run.get("baseline_error_minutes", 0.0)
    hybrid_error = run.get("hybrid_error_minutes", 0.0)

    if actual_eta is None:
        return "MODEL_UNCERTAINTY"

    # Hybrid-specific classification
    if model_type == "HYBRID":
        selected_model = run.get("selected_model", "BASELINE")
        # Check if hybrid made a sub-optimal selection (worse than alternative by > 5 min)
        if selected_model == "BASELINE" and context_error is not None:
            if context_error < baseline_error and (baseline_error - context_error) > 5.0:
                return "HYBRID_SELECTION_ERROR"
            elif baseline_error > 10.0:
                return "HYBRID_BASELINE_SELECTION"
        elif selected_model == "CONTEXT_AWARE" and baseline_error is not None:
            if baseline_error < context_error and (context_error - baseline_error) > 5.0:
                return "HYBRID_SELECTION_ERROR"
            elif context_error > 10.0:
                return "HYBRID_CONTEXT_SELECTION"

    if context_eta is None:
        return "MODEL_UNCERTAINTY"

    signed_error = context_eta - actual_eta

    # 2. Extreme / Rare Compound Condition
    rainfall = float(params.get("rainfall_mm", 0.0))
    congestion = float(params.get("congestion_index", 0.0))
    if rainfall >= 45.0 and congestion >= 85.0:
        return "RARE_CONDITION"

    # 3. Domain-specific contextual stress mismatches
    if str(params.get("road_restriction_type", "NONE")).upper() in ["ROAD_CLOSURE", "PARTIAL_CLOSURE"] and context_error > 10.0:
        return "ROAD_RESTRICTION_MISMATCH"

    if str(params.get("event_level", "NONE")).upper() in ["HIGH", "MEDIUM"] and context_error > 10.0:
        return "EVENT_IMPACT_MISMATCH"

    if rainfall >= 25.0 and context_error > 10.0:
        return "WEATHER_IMPACT_MISMATCH"

    waste_tons = float(params.get("waste_volume_tons", 0.0))
    if waste_tons >= 10.0 and context_error > 10.0:
        return "HIGH_WASTE_EFFECT"

    # 4. Context Mismatch (baseline outperformed context-aware model significantly)
    if baseline_error < context_error and (context_error - baseline_error) > 5.0:
        return "CONTEXT_MISMATCH"

    # 5. Directional bias errors
    if signed_error < -10.0:
        return "UNDER_PREDICTION"
    elif signed_error > 10.0:
        return "OVER_PREDICTION"

    return "MODEL_UNCERTAINTY"


def is_failure_case(run: Dict[str, Any], tolerance_minutes: float = 10.0, model_type: str = "CONTEXT_AWARE") -> bool:
    """
    A run is flagged as a failure case if:
    1. Operational safety constraint violated, OR
    2. Selected model absolute error > alternative model absolute error, OR
    3. Prediction absolute error > tolerance_minutes (default 10 min).
    """
    if not run.get("is_safe", True) or run.get("status") == "UNSAFE_ASSIGNMENT":
        return True

    if model_type == "HYBRID":
        err = run.get("hybrid_error_minutes")
        if err is None:
            return True
        return err > tolerance_minutes
    else:
        context_err = run.get("context_aware_error_minutes")
        baseline_err = run.get("baseline_error_minutes")

        if context_err is None or baseline_err is None:
            return True

        if context_err > baseline_err:
            return True

        if context_err > tolerance_minutes:
            return True

    return False


def analyze_failures(runs: List[Dict[str, Any]], tolerance_minutes: float = 10.0) -> Dict[str, Any]:
    """
    Process a list of experiment run records and produce failure breakdown and metrics.
    """
    failure_cases = []
    category_counts: Dict[str, int] = {cat: 0 for cat in FAILURE_CATEGORIES}

    for run in runs:
        if is_failure_case(run, tolerance_minutes=tolerance_minutes):
            cat = classify_failure_case(run, model_type=run.get("selected_model", "CONTEXT_AWARE"))
            category_counts[cat] = category_counts.get(cat, 0) + 1

            baseline_eta = run.get("baseline_eta_minutes")
            context_eta = run.get("context_aware_eta_minutes")
            hybrid_eta = run.get("hybrid_eta_minutes")
            actual_eta = run.get("actual_travel_minutes") or run.get("simulated_actual_minutes")
            baseline_err = run.get("baseline_error_minutes")
            context_err = run.get("context_aware_error_minutes")
            hybrid_err = run.get("hybrid_error_minutes")

            failure_cases.append({
                "scenario_key": run.get("scenario_key", "UNKNOWN"),
                "scenario_name": run.get("scenario_name", "Unknown Scenario"),
                "route_id": run.get("route_id", "R-101"),
                "seed": run.get("seed", 42),
                "baseline_eta_minutes": baseline_eta,
                "context_aware_eta_minutes": context_eta,
                "hybrid_eta_minutes": hybrid_eta,
                "selected_model": run.get("selected_model", "BASELINE"),
                "actual_eta_minutes": actual_eta,
                "baseline_error_minutes": baseline_err,
                "context_aware_error_minutes": context_err,
                "hybrid_error_minutes": hybrid_err,
                "error_delta_minutes": round((context_err - baseline_err), 2) if (context_err is not None and baseline_err is not None) else None,
                "failure_reason": cat,
                "is_safe": run.get("is_safe", True),
                "safety_message": run.get("safety_message") or (run.get("constraint_violation", {}).get("message") if run.get("constraint_violation") else None),
            })

    # Sort failure cases by largest error descending
    failure_cases.sort(
        key=lambda x: (x["hybrid_error_minutes"] if x.get("hybrid_error_minutes") is not None else (x["context_aware_error_minutes"] if x.get("context_aware_error_minutes") is not None else 9999.0)),
        reverse=True,
    )

    return {
        "total_runs": len(runs),
        "total_failures": len(failure_cases),
        "failure_rate_pct": round((len(failure_cases) / len(runs) * 100.0), 2) if runs else 0.0,
        "category_breakdown": category_counts,
        "failure_cases": failure_cases,
    }


def get_top_worst_errors(runs: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract top N largest absolute prediction errors for Baseline, Context-Aware, and Adaptive Hybrid models.
    """
    baseline_ranked = []
    context_ranked = []
    hybrid_ranked = []

    for r in runs:
        if not r.get("is_safe", True):
            continue

        b_err = r.get("baseline_error_minutes")
        c_err = r.get("context_aware_error_minutes")
        h_err = r.get("hybrid_error_minutes")
        actual = r.get("actual_travel_minutes") or r.get("simulated_actual_minutes")
        reason = classify_failure_case(r)
        h_reason = classify_failure_case(r, model_type="HYBRID")

        if b_err is not None and actual is not None:
            baseline_ranked.append({
                "route": r.get("route_id", "R-101"),
                "scenario": r.get("scenario_name", r.get("scenario_key", "UNKNOWN")),
                "seed": r.get("seed", 42),
                "predicted_eta": r.get("baseline_eta_minutes"),
                "actual_eta": actual,
                "absolute_error": b_err,
                "signed_error": round(float(r.get("baseline_eta_minutes", 0.0)) - float(actual), 2),
                "reason": "KINEMATIC_NON_CONTEXTUAL_OVERSIMPLIFICATION" if b_err > 10 else "NORMAL_SPEED_APPROXIMATION",
            })

        if c_err is not None and actual is not None:
            context_ranked.append({
                "route": r.get("route_id", "R-101"),
                "scenario": r.get("scenario_name", r.get("scenario_key", "UNKNOWN")),
                "seed": r.get("seed", 42),
                "predicted_eta": r.get("context_aware_eta_minutes"),
                "actual_eta": actual,
                "absolute_error": c_err,
                "signed_error": round(float(r.get("context_aware_eta_minutes", 0.0)) - float(actual), 2),
                "reason": reason,
            })

        if h_err is not None and actual is not None:
            hybrid_ranked.append({
                "route": r.get("route_id", "R-101"),
                "scenario": r.get("scenario_name", r.get("scenario_key", "UNKNOWN")),
                "seed": r.get("seed", 42),
                "predicted_eta": r.get("hybrid_eta_minutes"),
                "actual_eta": actual,
                "absolute_error": h_err,
                "signed_error": round(float(r.get("hybrid_eta_minutes", 0.0)) - float(actual), 2),
                "reason": h_reason,
            })

    baseline_ranked.sort(key=lambda x: x["absolute_error"], reverse=True)
    context_ranked.sort(key=lambda x: x["absolute_error"], reverse=True)
    hybrid_ranked.sort(key=lambda x: x["absolute_error"], reverse=True)

    # Add Rank
    for i, item in enumerate(baseline_ranked[:top_n], 1):
        item["rank"] = i
    for i, item in enumerate(context_ranked[:top_n], 1):
        item["rank"] = i
    for i, item in enumerate(hybrid_ranked[:top_n], 1):
        item["rank"] = i

    return {
        "baseline_worst": baseline_ranked[:top_n],
        "context_aware_worst": context_ranked[:top_n],
        "hybrid_worst": hybrid_ranked[:top_n],
    }
