import logging
from typing import Dict, Any, Union
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, median_absolute_error

logger = logging.getLogger(__name__)

# Default acceptable operational tolerance in minutes (e.g. within +/- 10 minutes of true ETA)
DEFAULT_TOLERANCE_MINUTES: float = 10.0


def calculate_metrics(
    y_true: Union[np.ndarray, list],
    y_pred: Union[np.ndarray, list],
    tolerance_minutes: float = DEFAULT_TOLERANCE_MINUTES,
) -> Dict[str, float]:
    """
    Calculate comprehensive evaluation metrics for travel-time prediction.
    
    Metrics:
    - MAE: Mean Absolute Error (minutes)
    - RMSE: Root Mean Squared Error (minutes)
    - Mean Error (Bias): Average signed difference (predicted - actual)
    - Median Absolute Error: Robust non-parametric central error
    - Within Tolerance Pct: Percentage of predictions within +/- tolerance_minutes of actual
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred, dtype=float)

    if len(y_true_arr) == 0 or len(y_pred_arr) == 0:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "mean_error": 0.0,
            "median_absolute_error": 0.0,
            "within_tolerance_pct": 0.0,
            "tolerance_minutes": tolerance_minutes,
            "sample_count": 0,
        }

    errors = y_pred_arr - y_true_arr
    abs_errors = np.abs(errors)

    mae = float(mean_absolute_error(y_true_arr, y_pred_arr))
    rmse = float(np.sqrt(mean_squared_error(y_true_arr, y_pred_arr)))
    mean_err = float(np.mean(errors))
    med_ae = float(median_absolute_error(y_true_arr, y_pred_arr))

    within_tol_count = np.sum(abs_errors <= tolerance_minutes)
    within_tol_pct = float((within_tol_count / len(y_true_arr)) * 100.0)

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mean_error": round(mean_err, 2),
        "median_absolute_error": round(med_ae, 2),
        "within_tolerance_pct": round(within_tol_pct, 2),
        "tolerance_minutes": round(tolerance_minutes, 2),
        "sample_count": int(len(y_true_arr)),
    }


def compare_models(
    baseline_metrics: Dict[str, float],
    context_metrics: Dict[str, float],
) -> Dict[str, Any]:
    """
    Compare baseline model against context-aware ML model.
    Computes percentage error reductions with safe division.
    """
    b_mae = baseline_metrics.get("mae", 0.0)
    c_mae = context_metrics.get("mae", 0.0)
    b_rmse = baseline_metrics.get("rmse", 0.0)
    c_rmse = context_metrics.get("rmse", 0.0)

    mae_improvement = 0.0
    if b_mae > 0:
        mae_improvement = round(((b_mae - c_mae) / b_mae) * 100.0, 2)

    rmse_improvement = 0.0
    if b_rmse > 0:
        rmse_improvement = round(((b_rmse - c_rmse) / b_rmse) * 100.0, 2)

    return {
        "baseline": baseline_metrics,
        "context_aware": context_metrics,
        "mae_improvement_pct": mae_improvement,
        "rmse_improvement_pct": rmse_improvement,
        "is_improved": mae_improvement > 0,
    }
