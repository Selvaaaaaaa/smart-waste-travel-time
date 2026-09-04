"""
Centralized Hybrid Decision Policy Configuration.

Principles:
- Purely pre-trip decision rules based only on environmental and operational context.
- Zero data leakage (strictly independent of actual duration or post-trip errors).
- Centralized configuration with versioning and explainable reason codes.
"""

from typing import Dict, Any, List

POLICY_VERSION = "hybrid-v1"

# Thresholds for environmental and operational disruption
HYBRID_THRESHOLDS = {
    # Congestion index above which traffic is considered disruptive
    "congestion_index_threshold": 65.0,
    # Precipitation in mm above which rain is considered disruptive
    "rainfall_mm_threshold": 15.0,
    # Visibility in km below which weather is considered disruptive
    "visibility_km_threshold": 4.0,
    # Waste volume in tons above which collection stop dwell delays are substantial
    "high_waste_volume_tons_threshold": 9.5,
    # Prediction spread standard deviation in minutes above which tree ensemble exhibits high disagreement
    "prediction_spread_high_threshold": 18.0,
}

# Environmental category sets that warrant context-aware ML prediction
DISRUPTIVE_WEATHER_CONDITIONS: List[str] = ["HEAVY_RAIN", "STORM"]
DISRUPTIVE_TRAFFIC_LEVELS: List[str] = ["HIGH", "SEVERE"]
DISRUPTIVE_EVENT_LEVELS: List[str] = ["MEDIUM", "HIGH"]
DISRUPTIVE_ROAD_RESTRICTIONS: List[str] = [
    "LANE_RESTRICTION",
    "CONSTRUCTION",
    "PARTIAL_CLOSURE",
    "ROAD_CLOSURE",
]

HYBRID_POLICY: Dict[str, Any] = {
    "policy_version": POLICY_VERSION,
    "description": "Pre-trip rule-based model selection heuristic switching between Baseline Kinematic and Context-Aware Tree Regression.",
    "thresholds": HYBRID_THRESHOLDS,
    "disruptive_weather": DISRUPTIVE_WEATHER_CONDITIONS,
    "disruptive_traffic": DISRUPTIVE_TRAFFIC_LEVELS,
    "disruptive_events": DISRUPTIVE_EVENT_LEVELS,
    "disruptive_road_restrictions": DISRUPTIVE_ROAD_RESTRICTIONS,
}
