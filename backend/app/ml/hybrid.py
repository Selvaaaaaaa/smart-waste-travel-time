import logging
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

from app.ml.baseline import predict_baseline_eta
from app.ml.features import extract_feature_matrix
from app.ml.model_registry import load_model, is_model_available
from app.ml.hybrid_policy import (
    POLICY_VERSION,
    HYBRID_THRESHOLDS,
    DISRUPTIVE_WEATHER_CONDITIONS,
    DISRUPTIVE_TRAFFIC_LEVELS,
    DISRUPTIVE_EVENT_LEVELS,
    DISRUPTIVE_ROAD_RESTRICTIONS,
)

logger = logging.getLogger(__name__)


def compute_prediction_spread(pipeline_or_params: Any, X: Optional[pd.DataFrame] = None) -> Optional[float]:
    """
    Calculate the empirical standard deviation across individual tree estimators
    in the Random Forest regressor ensemble to estimate model prediction spread / disagreement.
    
    Disclaimer: This is an empirical spread metric and not a formal statistical confidence interval.
    """
    try:
        if X is None and isinstance(pipeline_or_params, dict):
            if not is_model_available():
                return None
            pipeline = load_model()
            row = {
                "distance_km": float(pipeline_or_params.get("distance_km", 20.0)),
                "waste_volume_tons": float(pipeline_or_params.get("waste_volume_tons", 0.0)),
                "weather_condition": str(pipeline_or_params.get("weather_condition", "CLEAR")),
                "rainfall_mm": float(pipeline_or_params.get("rainfall_mm", 0.0)),
                "visibility_km": float(pipeline_or_params.get("visibility_km", 10.0)),
                "traffic_level": str(pipeline_or_params.get("traffic_level", "LOW")),
                "congestion_index": float(pipeline_or_params.get("congestion_index", 15.0)),
                "average_speed_kmh": float(pipeline_or_params.get("average_speed_kmh", 45.0)),
                "event_level": str(pipeline_or_params.get("event_level", "NONE")),
                "event_radius": float(pipeline_or_params.get("event_radius", 0.0)),
                "road_restriction_type": str(pipeline_or_params.get("road_restriction_type", "NONE")),
                "road_restriction_severity": str(pipeline_or_params.get("road_restriction_severity", "NONE")),
                "hour_of_day": int(pipeline_or_params.get("hour_of_day", 9)),
                "day_of_week": int(pipeline_or_params.get("day_of_week", 1)),
            }
            df = pd.DataFrame([row])
            X = extract_feature_matrix(df)
        else:
            pipeline = pipeline_or_params

        regressor = pipeline.named_steps.get("regressor")
        preprocessor = pipeline.named_steps.get("preprocessor")

        if hasattr(regressor, "estimators_") and len(regressor.estimators_) > 0:
            X_trans = preprocessor.transform(X)
            # Gather individual estimator predictions
            tree_preds = [tree.predict(X_trans)[0] for tree in regressor.estimators_]
            spread = float(np.std(tree_preds))
            return round(spread, 2)
    except Exception as e:
        logger.debug("Could not calculate prediction spread: %s", e)

    return None


def select_model_pre_trip(
    context: Dict[str, Any],
    prediction_spread_minutes: Optional[float] = None,
) -> Tuple[str, str]:
    """
    Intelligent pre-trip model selector.
    
    CRITICAL RESEARCH INTEGRITY GUARANTEE:
    This function evaluates ONLY pre-trip environmental and operational inputs.
    It has ZERO access to actual duration, actual arrival timestamps, or post-trip errors.
    
    Returns:
        Tuple of (selected_model: 'BASELINE' | 'CONTEXT_AWARE', selection_reason: str)
    """
    event_level = str(context.get("event_level", "NONE")).upper()
    road_restriction = str(context.get("road_restriction_type", "NONE")).upper()
    traffic_level = str(context.get("traffic_level", "LOW")).upper()
    congestion_index = float(context.get("congestion_index", 15.0))
    weather_condition = str(context.get("weather_condition", "CLEAR")).upper()
    rainfall_mm = float(context.get("rainfall_mm", 0.0))
    visibility_km = float(context.get("visibility_km", 10.0))

    # Rule 1: Active major public events induce substantial localized delays that kinematic models cannot foresee
    if event_level in DISRUPTIVE_EVENT_LEVELS:
        return "CONTEXT_AWARE", "MAJOR_EVENT_ACTIVE"

    # Rule 2: Active road restrictions and closures require contextual detour compensation
    if road_restriction in DISRUPTIVE_ROAD_RESTRICTIONS:
        return "CONTEXT_AWARE", "ROAD_RESTRICTION_ACTIVE"

    # Rule 3: High or severe congestion index significantly deviates from standard 25 km/h speeds
    if (
        traffic_level in DISRUPTIVE_TRAFFIC_LEVELS
        or congestion_index >= HYBRID_THRESHOLDS["congestion_index_threshold"]
    ):
        return "CONTEXT_AWARE", "HIGH_TRAFFIC_CONGESTION"

    # Rule 4: Storms or extreme precipitation > threshold cause significant roadway deceleration
    if (
        weather_condition in DISRUPTIVE_WEATHER_CONDITIONS
        or rainfall_mm >= HYBRID_THRESHOLDS["rainfall_mm_threshold"]
        or visibility_km <= HYBRID_THRESHOLDS["visibility_km_threshold"]
    ):
        return "CONTEXT_AWARE", "SEVERE_WEATHER_DISRUPTION"

    # Rule 5: For nominal conditions (clear/cloudy weather, low/moderate traffic, no events),
    # Phase 4 empirical findings prove the deterministic baseline speed heuristic provides superior accuracy.
    return "BASELINE", "NOMINAL_ENVIRONMENTAL_CONDITIONS"


def predict_hybrid_eta(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute Adaptive Hybrid ETA prediction:
    1. Compute deterministic Baseline ETA.
    2. Compute Context-Aware ML ETA and tree ensemble Prediction Spread.
    3. Run pre-trip rule-based selector to choose optimal model strategy.
    4. Return selected prediction, reason code, and alternative model outputs for full transparency.
    """
    distance_km = float(context.get("distance_km", 0.0))
    if distance_km <= 0:
        raise ValueError("distance_km must be strictly positive (> 0).")

    # 1. Baseline prediction
    baseline_eta = predict_baseline_eta(distance_km)

    # 2. Context-Aware ML prediction & uncertainty
    context_aware_eta = None
    prediction_spread = None

    if is_model_available():
        model = load_model()
        row = {
            "distance_km": distance_km,
            "waste_volume_tons": float(context.get("waste_volume_tons", 0.0)),
            "weather_condition": str(context.get("weather_condition", "CLEAR")),
            "rainfall_mm": float(context.get("rainfall_mm", 0.0)),
            "visibility_km": float(context.get("visibility_km", 10.0)),
            "traffic_level": str(context.get("traffic_level", "LOW")),
            "congestion_index": float(context.get("congestion_index", 15.0)),
            "average_speed_kmh": float(context.get("average_speed_kmh", 45.0)),
            "event_level": str(context.get("event_level", "NONE")),
            "event_radius": float(context.get("event_radius", 0.0)),
            "road_restriction_type": str(context.get("road_restriction_type", "NONE")),
            "road_restriction_severity": str(context.get("road_restriction_severity", "NONE")),
            "hour_of_day": int(context.get("hour_of_day", 9)),
            "day_of_week": int(context.get("day_of_week", 1)),
        }
        df = pd.DataFrame([row])
        X = extract_feature_matrix(df)
        pred_val = float(model.predict(X)[0])
        context_aware_eta = round(max(pred_val, 1.0), 2)
        prediction_spread = compute_prediction_spread(model, X)

    # 3. Pre-Trip Model Selection
    selected_model, selection_reason = select_model_pre_trip(
        context=context,
        prediction_spread_minutes=prediction_spread,
    )

    # Fallback to baseline if context-aware model is chosen but not trained
    if selected_model == "CONTEXT_AWARE" and context_aware_eta is None:
        selected_model = "BASELINE"
        selection_reason = "FALLBACK_MODEL_NOT_TRAINED"

    # 4. Resolve Hybrid ETA
    if selected_model == "CONTEXT_AWARE" and context_aware_eta is not None:
        hybrid_eta = context_aware_eta
    else:
        hybrid_eta = baseline_eta

    return {
        "selected_model": selected_model,
        "predicted_eta_minutes": round(hybrid_eta, 2),
        "selection_reason": selection_reason,
        "prediction_spread_minutes": prediction_spread,
        "baseline_eta_minutes": round(baseline_eta, 2),
        "context_aware_eta_minutes": context_aware_eta,
        "policy_version": POLICY_VERSION,
        "context_applied": {
            "weather": context.get("weather_condition", "CLEAR"),
            "traffic": context.get("traffic_level", "LOW"),
            "event": context.get("event_level", "NONE"),
            "road_restriction": context.get("road_restriction_type", "NONE"),
            "waste_volume_tons": context.get("waste_volume_tons", 0.0),
        },
    }
