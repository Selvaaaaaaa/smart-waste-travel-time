import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.ml.hybrid import predict_hybrid_eta
from app.models.route import Route
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.eta_prediction import ETAPrediction
from app.services.safety_service import SafetyService, SafetyValidationResult

logger = logging.getLogger(__name__)


class HybridETAService:
    """
    High-level orchestration service for Adaptive Hybrid ETA prediction.
    Enforces Safety Validation -> Pre-Trip Model Selection -> Prediction -> DB Logging.
    """

    @staticmethod
    def predict_hybrid(
        params: Dict[str, Any],
        db: Session,
        route_id: Optional[int] = None,
        vehicle_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        persist: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute Adaptive Hybrid prediction with strict safety enforcement.
        """
        distance_km = float(params.get("distance_km", 0.0))
        waste_tons = float(params.get("waste_volume_tons", 5.0))

        # Resolve route details if provided
        if route_id:
            route = db.query(Route).filter(Route.id == route_id).first()
            if route:
                if distance_km <= 0:
                    distance_km = float(route.total_distance_km)
                    params["distance_km"] = distance_km
                if "waste_volume_tons" not in params:
                    waste_tons = float(route.total_waste_tons)
                    params["waste_volume_tons"] = waste_tons
                if not vehicle_id and route.vehicle_id:
                    vehicle_id = route.vehicle_id
                if not driver_id and route.driver_id:
                    driver_id = route.driver_id

        if distance_km <= 0:
            raise ValueError("distance_km must be strictly positive (> 0).")

        # 1. SAFETY VALIDATION (Must be evaluated before model recommendation)
        safety_status = "SAFE"
        safety_message = "All operational and labor safety constraints satisfied."
        violation_type = None

        if not vehicle_id:
            first_v = db.query(Vehicle).filter(Vehicle.active == True).first()
            if first_v:
                vehicle_id = first_v.id

        if not driver_id:
            first_d = db.query(Driver).filter(Driver.active == True).first()
            if first_d:
                driver_id = first_d.id

        if vehicle_id:
            cap_check = SafetyService.validate_vehicle_capacity(vehicle_id, waste_tons, db)
            if not cap_check.is_valid:
                safety_status = "UNSAFE_ASSIGNMENT"
                safety_message = cap_check.message
                violation_type = cap_check.violation_type

        # If unsafe, reject immediately and do NOT return an efficiency prediction
        if safety_status == "UNSAFE_ASSIGNMENT":
            logger.warning("Hybrid prediction halted: %s (%s)", safety_message, violation_type)
            return {
                "selected_model": "UNSAFE",
                "predicted_eta_minutes": None,
                "selection_reason": f"REJECTED_SAFETY_CONSTRAINT_{violation_type}",
                "prediction_spread_minutes": None,
                "safety_status": "UNSAFE_ASSIGNMENT",
                "is_safe": False,
                "constraint_violation": {
                    "type": violation_type,
                    "message": safety_message,
                },
                "policy_version": params.get("policy_version", "hybrid-v1"),
            }

        # 2. HYBRID PREDICTION
        hybrid_res = predict_hybrid_eta(params)

        # Validate driver workload with predicted duration
        if driver_id:
            est_minutes = int(hybrid_res["predicted_eta_minutes"])
            driver_check = SafetyService.validate_driver_workload(driver_id, est_minutes, db)
            if not driver_check.is_valid:
                logger.warning("Hybrid prediction halted due to driver workload: %s", driver_check.message)
                return {
                    "selected_model": "UNSAFE",
                    "predicted_eta_minutes": None,
                    "selection_reason": f"REJECTED_SAFETY_CONSTRAINT_{driver_check.violation_type}",
                    "prediction_spread_minutes": None,
                    "safety_status": "UNSAFE_ASSIGNMENT",
                    "is_safe": False,
                    "constraint_violation": {
                        "type": driver_check.violation_type,
                        "message": driver_check.message,
                    },
                    "policy_version": hybrid_res.get("policy_version", "hybrid-v1"),
                }

        # 3. OPTIONAL DATABASE LOGGING
        if persist and route_id:
            try:
                p_hybrid = ETAPrediction(
                    route_id=route_id,
                    model_type="HYBRID",
                    predicted_eta_minutes=hybrid_res["predicted_eta_minutes"],
                )
                db.add(p_hybrid)
                db.commit()
            except Exception as e:
                logger.error("Failed to persist hybrid ETA prediction: %s", e)
                db.rollback()

        return {
            "selected_model": hybrid_res["selected_model"],
            "predicted_eta_minutes": hybrid_res["predicted_eta_minutes"],
            "selection_reason": hybrid_res["selection_reason"],
            "prediction_spread_minutes": hybrid_res["prediction_spread_minutes"],
            "baseline_eta_minutes": hybrid_res["baseline_eta_minutes"],
            "context_aware_eta_minutes": hybrid_res["context_aware_eta_minutes"],
            "safety_status": "SAFE",
            "is_safe": True,
            "policy_version": hybrid_res["policy_version"],
            "context_applied": hybrid_res.get("context_applied", {}),
        }
