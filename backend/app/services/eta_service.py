import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.ml.baseline import predict_baseline_eta, DEFAULT_BASELINE_SPEED_KMH
from app.ml.predict import predict_eta_single
from app.ml.model_registry import is_model_available, get_model_metadata
from app.models.eta_prediction import ETAPrediction
from app.models.route import Route
from app.services.safety_service import SafetyService

logger = logging.getLogger(__name__)


class ETAService:
    """
    High-level ETA prediction and evaluation service.
    Orchestrates baseline and context-aware predictions with database persistence.
    """

    @staticmethod
    def predict_both(
        params: Dict[str, Any],
        db: Optional[Session] = None,
        route_id: Optional[int] = None,
        persist: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate both baseline and context-aware ETA predictions for given parameters.
        Optionally persists the prediction records to PostgreSQL / DB.
        """
        distance_km = float(params.get("distance_km", 0.0))
        if distance_km <= 0 and route_id and db:
            route = db.query(Route).filter(Route.id == route_id).first()
            if route:
                distance_km = float(route.total_distance_km)
                params["distance_km"] = distance_km

        if distance_km <= 0:
            raise ValueError("distance_km must be > 0.")

        # Baseline prediction
        baseline_eta = predict_baseline_eta(distance_km)

        # Context-aware prediction
        if not is_model_available():
            raise RuntimeError("Context-aware ML model is not trained yet. Please train the model first.")

        pred_res = predict_eta_single(params)
        context_eta = pred_res["context_aware_eta_minutes"]
        diff = round(context_eta - baseline_eta, 2)

        # Hybrid model evaluation
        from app.services.hybrid_eta_service import HybridETAService
        hybrid_res = HybridETAService.predict_hybrid(params, db=db, route_id=route_id, persist=False)

        result = {
            "distance_km": round(distance_km, 2),
            "baseline_eta_minutes": round(baseline_eta, 2),
            "context_aware_eta_minutes": round(context_eta, 2),
            "difference_minutes": diff,
            "baseline_speed_kmh": DEFAULT_BASELINE_SPEED_KMH,
            "context_applied": pred_res.get("context_applied", {}),
            "hybrid_eta_minutes": hybrid_res.get("predicted_eta_minutes"),
            "selected_model": hybrid_res.get("selected_model"),
            "selection_reason": hybrid_res.get("selection_reason"),
            "prediction_spread_minutes": hybrid_res.get("prediction_spread_minutes"),
            "safety_status": hybrid_res.get("safety_status", "SAFE"),
        }

        # Optional persistence
        if persist and db and route_id:
            try:
                p_b = ETAPrediction(
                    route_id=route_id,
                    model_type="BASELINE",
                    predicted_eta_minutes=baseline_eta,
                )
                p_c = ETAPrediction(
                    route_id=route_id,
                    model_type="CONTEXT_AWARE",
                    predicted_eta_minutes=context_eta,
                )
                db.add(p_b)
                db.add(p_c)
                db.commit()
            except Exception as e:
                logger.error("Failed to persist ETA predictions: %s", e)
                db.rollback()

        return result
