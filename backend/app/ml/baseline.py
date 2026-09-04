import logging
from typing import Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Configurable global standard baseline speed for urban waste collection fleets (km/h)
DEFAULT_BASELINE_SPEED_KMH: float = 25.0


class BaselineETAModel:
    """
    Deterministic Baseline Travel-Time Model.
    
    Principles:
    - Strictly non-contextual (does NOT use weather, traffic, events, road restrictions, or waste volume).
    - Standard speed-distance kinematic calculation: ETA (minutes) = (distance_km / nominal_speed_kmh) * 60.
    - Deterministic, fast, and transparent benchmark for academic comparison.
    """

    def __init__(self, nominal_speed_kmh: float = DEFAULT_BASELINE_SPEED_KMH):
        if nominal_speed_kmh <= 0:
            raise ValueError("nominal_speed_kmh must be strictly positive.")
        self.nominal_speed_kmh = float(nominal_speed_kmh)

    def predict_single(self, distance_km: float) -> float:
        """Calculate predicted baseline ETA in minutes for a single distance."""
        if distance_km <= 0:
            raise ValueError(f"distance_km must be > 0. Received: {distance_km}")
        return float((distance_km / self.nominal_speed_kmh) * 60.0)

    def predict(self, data: Union[pd.DataFrame, np.ndarray, list]) -> np.ndarray:
        """
        Calculate baseline ETA predictions in minutes for an array/series/DataFrame of distances.
        If DataFrame is passed, looks for 'distance_km' column.
        """
        if isinstance(data, pd.DataFrame):
            if "distance_km" not in data.columns:
                raise KeyError("DataFrame must contain 'distance_km' column.")
            distances = data["distance_km"].values
        elif isinstance(data, (list, tuple)):
            distances = np.array(data, dtype=float)
        else:
            distances = np.asarray(data, dtype=float)

        if np.any(distances <= 0):
            logger.warning("Baseline prediction input contains distances <= 0. Values clamped to minimal 0.01 km.")
            distances = np.maximum(distances, 0.01)

        return (distances / self.nominal_speed_kmh) * 60.0


def predict_baseline_eta(distance_km: float, speed_kmh: float = DEFAULT_BASELINE_SPEED_KMH) -> float:
    """Helper functional wrapper for baseline ETA computation."""
    model = BaselineETAModel(nominal_speed_kmh=speed_kmh)
    return model.predict_single(distance_km)
