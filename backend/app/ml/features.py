import logging
from typing import List, Dict, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Primary target variable for travel-time prediction
TARGET_COLUMN: str = "actual_travel_minutes"

# Numerical features representing continuous physical and operational factors
NUMERICAL_FEATURES: List[str] = [
    "distance_km",
    "waste_volume_tons",
    "rainfall_mm",
    "visibility_km",
    "congestion_index",
    "average_speed_kmh",
    "event_radius",
    "hour_of_day",
    "day_of_week",
    "is_peak_hour",
]

# Categorical features representing discrete environmental and operational conditions
CATEGORICAL_FEATURES: List[str] = [
    "weather_condition",
    "traffic_level",
    "event_level",
    "road_restriction_type",
    "road_restriction_severity",
]

# Complete list of feature columns required for model training and inference
ALL_FEATURE_COLUMNS: List[str] = NUMERICAL_FEATURES + CATEGORICAL_FEATURES


def is_urban_peak_hour(hour: int, day_of_week: int) -> int:
    """
    Determine if a given hour falls during typical municipal urban peak traffic hours.
    Peak hours defined as:
    - Morning peak: 07:00 - 09:00 (weekday)
    - Evening peak: 16:00 - 18:00 (weekday)
    - Weekend Saturday mid-day: 11:00 - 14:00 (day_of_week == 5)
    """
    if day_of_week in [0, 1, 2, 3, 4]:  # Monday to Friday
        if 7 <= hour <= 9 or 16 <= hour <= 18:
            return 1
    elif day_of_week == 5:  # Saturday
        if 11 <= hour <= 14:
            return 1
    return 0


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Augment raw observation dataframe with engineered features:
    - is_peak_hour: binary flag derived from hour_of_day and day_of_week.
    Ensures correct types and fills missing values.
    """
    df_out = df.copy()

    # Engineer peak hour indicator if not already present
    if "is_peak_hour" not in df_out.columns:
        if "hour_of_day" in df_out.columns and "day_of_week" in df_out.columns:
            df_out["is_peak_hour"] = [
                is_urban_peak_hour(int(h), int(d))
                for h, d in zip(df_out["hour_of_day"], df_out["day_of_week"])
            ]
        else:
            df_out["is_peak_hour"] = 0

    # Ensure numeric columns are strictly float/int
    for col in NUMERICAL_FEATURES:
        if col in df_out.columns:
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce").fillna(0.0)

    # Ensure categorical columns are strings
    for col in CATEGORICAL_FEATURES:
        if col in df_out.columns:
            df_out[col] = df_out[col].astype(str).fillna("NONE")

    return df_out


def extract_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare and slice DataFrame containing only the required model feature columns."""
    engineered = engineer_features(df)
    missing = [c for c in ALL_FEATURE_COLUMNS if c not in engineered.columns]
    if missing:
        raise ValueError(f"Missing required feature columns in input dataframe: {missing}")
    return engineered[ALL_FEATURE_COLUMNS]
