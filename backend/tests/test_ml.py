import numpy as np
import pandas as pd
import pytest

from app.ml.baseline import BaselineETAModel, predict_baseline_eta, DEFAULT_BASELINE_SPEED_KMH
from app.ml.features import is_urban_peak_hour, engineer_features, extract_feature_matrix
from app.ml.preprocessing import build_model_pipeline
from app.ml.evaluate import calculate_metrics, compare_models
from app.ml.dataset import load_dataset_from_db


def test_baseline_eta_calculation():
    # At 25 km/h: 25 km should take 60 minutes
    eta = predict_baseline_eta(25.0, speed_kmh=25.0)
    assert pytest.approx(eta, 0.01) == 60.0

    # 12.5 km should take 30 minutes
    eta_half = predict_baseline_eta(12.5, speed_kmh=25.0)
    assert pytest.approx(eta_half, 0.01) == 30.0

    # Invalid negative distance
    with pytest.raises(ValueError):
        predict_baseline_eta(-5.0)


def test_baseline_model_batch():
    model = BaselineETAModel(nominal_speed_kmh=DEFAULT_BASELINE_SPEED_KMH)
    df = pd.DataFrame({"distance_km": [25.0, 50.0, 10.0]})
    preds = model.predict(df)
    assert len(preds) == 3
    assert pytest.approx(preds[0], 0.01) == 60.0
    assert pytest.approx(preds[1], 0.01) == 120.0
    assert pytest.approx(preds[2], 0.01) == 24.0


def test_peak_hour_indicator():
    # Monday 08:00 (peak)
    assert is_urban_peak_hour(8, 0) == 1
    # Monday 14:00 (non-peak)
    assert is_urban_peak_hour(14, 0) == 0
    # Monday 17:00 (peak)
    assert is_urban_peak_hour(17, 0) == 1
    # Sunday 08:00 (non-peak weekend)
    assert is_urban_peak_hour(8, 6) == 0


def test_feature_engineering_pipeline():
    raw_data = pd.DataFrame(
        [
            {
                "distance_km": 15.0,
                "waste_volume_tons": 6.0,
                "rainfall_mm": 10.0,
                "visibility_km": 5.0,
                "congestion_index": 50.0,
                "average_speed_kmh": 25.0,
                "event_radius": 0.0,
                "hour_of_day": 8,
                "day_of_week": 1,
                "weather_condition": "RAIN",
                "traffic_level": "HIGH",
                "event_level": "NONE",
                "road_restriction_type": "NONE",
                "road_restriction_severity": "NONE",
            }
        ]
    )
    engineered = engineer_features(raw_data)
    assert engineered["is_peak_hour"].iloc[0] == 1
    matrix = extract_feature_matrix(engineered)
    assert "distance_km" in matrix.columns
    assert "weather_condition" in matrix.columns


def test_evaluation_metrics_and_comparison():
    y_true = [50.0, 60.0, 70.0, 80.0]
    y_pred_bad = [20.0, 30.0, 40.0, 50.0]  # Off by 30 min each
    y_pred_good = [52.0, 59.0, 71.0, 78.0]  # Off by 1-2 min each

    bad_metrics = calculate_metrics(y_true, y_pred_bad, tolerance_minutes=10.0)
    good_metrics = calculate_metrics(y_true, y_pred_good, tolerance_minutes=10.0)

    assert bad_metrics["mae"] == 30.0
    assert bad_metrics["within_tolerance_pct"] == 0.0

    assert good_metrics["mae"] == 1.5
    assert good_metrics["within_tolerance_pct"] == 100.0

    comparison = compare_models(bad_metrics, good_metrics)
    assert comparison["is_improved"] is True
    assert comparison["mae_improvement_pct"] == 95.0


def test_dataset_loader(db_session):
    df, report = load_dataset_from_db(db_session)
    assert len(df) > 0
    assert report.total_records == len(df)
    assert "actual_travel_minutes" in df.columns
    assert "distance_km" in df.columns
