import logging
from typing import Dict, Any, Union
import pandas as pd
import numpy as np

from app.ml.features import (
    ALL_FEATURE_COLUMNS,
    engineer_features,
    extract_feature_matrix,
)
from app.ml.baseline import predict_baseline_eta
from app.ml.model_registry import load_model

logger = logging.getLogger(__name__)


def predict_eta_single(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict travel time for a single route instance using both the baseline
    and the trained context-aware machine learning model.
    
    Expected context keys:
    - distance_km (required, float > 0)
    - waste_volume_tons (float, default: 0.0)
    - weather_condition (str, default: 'CLEAR')
    - rainfall_mm (float, default: 0.0)
    - visibility_km (float, default: 10.0)
    - traffic_level (str, default: 'LOW')
    - congestion_index (float, default: 15.0)
    - average_speed_kmh (float, default: 45.0)
    - event_level (str, default: 'NONE')
    - event_radius (float, default: 0.0)
    - road_restriction_type (str, default: 'NONE')
    - road_restriction_severity (str, default: 'NONE')
    - hour_of_day (int, default: 9)
    - day_of_week (int, default: 1)
    """
    distance_km = float(context.get("distance_km", 0.0))
    if distance_km <= 0:
        raise ValueError("distance_km must be strictly positive.")

    # 1. Deterministic baseline prediction
    baseline_eta = predict_baseline_eta(distance_km=distance_km)

    # 2. Build single-row DataFrame for pipeline inference
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

    # 3. Load model and predict
    model = load_model()
    pred_array = model.predict(X)
    context_aware_eta = float(pred_array[0])

    # ETA cannot be physically non-positive
    context_aware_eta = max(context_aware_eta, 1.0)
    difference_minutes = round(context_aware_eta - baseline_eta, 2)

    return {
        "distance_km": distance_km,
        "baseline_eta_minutes": round(baseline_eta, 2),
        "context_aware_eta_minutes": round(context_aware_eta, 2),
        "difference_minutes": difference_minutes,
        "context_applied": {
            "weather": row["weather_condition"],
            "traffic": row["traffic_level"],
            "event": row["event_level"],
            "road_restriction": row["road_restriction_type"],
            "waste_volume_tons": row["waste_volume_tons"],
        },
    }


def predict_eta_batch(df: pd.DataFrame) -> np.ndarray:
    """Predict travel times for a batch DataFrame of observations."""
    model = load_model()
    X = extract_feature_matrix(df)
    preds = model.predict(X)
    return np.maximum(preds, 1.0)
