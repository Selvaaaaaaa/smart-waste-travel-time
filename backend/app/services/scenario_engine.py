import logging
import random
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.ml.baseline import predict_baseline_eta
from app.ml.predict import predict_eta_single
from app.ml.model_registry import is_model_available
from app.models.eta_prediction import ETAPrediction
from app.models.route import Route
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.services.safety_service import SafetyService, SafetyValidationResult

logger = logging.getLogger(__name__)

# Predefined standard operational research scenario configurations
STANDARD_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "NORMAL": {
        "name": "Normal Conditions",
        "description": "Nominal operational environment with clear weather, smooth traffic, and standard municipal waste tonnage.",
        "weather_condition": "CLEAR",
        "rainfall_mm": 0.0,
        "visibility_km": 10.0,
        "traffic_level": "LOW",
        "congestion_index": 15.0,
        "average_speed_kmh": 42.0,
        "event_level": "NONE",
        "event_radius": 0.0,
        "road_restriction_type": "NONE",
        "road_restriction_severity": "NONE",
        "waste_volume_tons": 5.5,
        "hour_of_day": 9,
        "day_of_week": 1,
    },
    "HEAVY_RAIN": {
        "name": "Heavy Rain",
        "description": "Adverse meteorological conditions causing reduced driver visibility, slippery roads, and citywide speed reductions.",
        "weather_condition": "HEAVY_RAIN",
        "rainfall_mm": 38.0,
        "visibility_km": 3.0,
        "traffic_level": "HIGH",
        "congestion_index": 68.0,
        "average_speed_kmh": 22.0,
        "event_level": "NONE",
        "event_radius": 0.0,
        "road_restriction_type": "NONE",
        "road_restriction_severity": "NONE",
        "waste_volume_tons": 5.8,
        "hour_of_day": 8,
        "day_of_week": 2,
    },
    "MAJOR_EVENT": {
        "name": "Major Event",
        "description": "Large public gathering, marathon, or festival causing intense localized congestion and partial lane closures.",
        "weather_condition": "CLEAR",
        "rainfall_mm": 0.0,
        "visibility_km": 10.0,
        "traffic_level": "SEVERE",
        "congestion_index": 86.0,
        "average_speed_kmh": 14.0,
        "event_level": "HIGH",
        "event_radius": 4.5,
        "road_restriction_type": "PARTIAL_CLOSURE",
        "road_restriction_severity": "MEDIUM",
        "waste_volume_tons": 7.2,
        "hour_of_day": 14,
        "day_of_week": 5,
    },
    "ROAD_CLOSURE": {
        "name": "Road Closure",
        "description": "Critical arterial road closed for emergency utility maintenance, forcing substantial heavy-vehicle rerouting.",
        "weather_condition": "CLOUDY",
        "rainfall_mm": 2.5,
        "visibility_km": 8.0,
        "traffic_level": "HIGH",
        "congestion_index": 74.0,
        "average_speed_kmh": 18.0,
        "event_level": "NONE",
        "event_radius": 0.0,
        "road_restriction_type": "ROAD_CLOSURE",
        "road_restriction_severity": "HIGH",
        "waste_volume_tons": 5.5,
        "hour_of_day": 10,
        "day_of_week": 3,
    },
    "HIGH_WASTE": {
        "name": "High Waste Volume",
        "description": "Post-holiday or peak collection surge generating heavy bin loads, extended stop dwell times, and vehicle weight penalties.",
        "weather_condition": "CLEAR",
        "rainfall_mm": 0.0,
        "visibility_km": 10.0,
        "traffic_level": "MEDIUM",
        "congestion_index": 42.0,
        "average_speed_kmh": 32.0,
        "event_level": "NONE",
        "event_radius": 0.0,
        "road_restriction_type": "NONE",
        "road_restriction_severity": "NONE",
        "waste_volume_tons": 11.2,
        "hour_of_day": 9,
        "day_of_week": 1,
    },
    "COMBINED_STRESS": {
        "name": "Combined Stress",
        "description": "Extreme compound stress testing simultaneous storm rainfall, rush-hour severe congestion, active events, and road closures.",
        "weather_condition": "STORM",
        "rainfall_mm": 55.0,
        "visibility_km": 2.0,
        "traffic_level": "SEVERE",
        "congestion_index": 94.0,
        "average_speed_kmh": 9.5,
        "event_level": "HIGH",
        "event_radius": 5.0,
        "road_restriction_type": "ROAD_CLOSURE",
        "road_restriction_severity": "HIGH",
        "waste_volume_tons": 12.5,
        "hour_of_day": 17,
        "day_of_week": 4,
    },
}


class ScenarioEngine:
    """
    Simulation engine for operational scenarios and model comparison.
    Simulates physical travel time under defined contextual variables,
    evaluates baseline vs context-aware predictions, and enforces safety constraints.
    """

    def __init__(self, random_seed: int = 42):
        self.random_seed = random_seed
        self._rng = random.Random(random_seed)

    def simulate_actual_travel_minutes(self, context: Dict[str, Any]) -> float:
        """
        Simulate realistic ground-truth actual travel time under contextual environmental stressors.
        Physical model breakdown:
        1. Base travel time = (distance / average_speed) * 60
        2. Weather delay: +0.3 min per mm rainfall, +15% if visibility < 4km
        3. Event delay: +5 to +20 min depending on event severity
        4. Road restriction delay: +10 to +30 min for closures/detours
        5. Waste loading dwell delay: +3 min per ton over nominal 4 tons
        6. Reproducible stochastic fluctuation (+/- 5%)
        """
        distance_km = float(context.get("distance_km", 20.0))
        avg_speed = max(float(context.get("average_speed_kmh", 30.0)), 5.0)
        base_time = (distance_km / avg_speed) * 60.0

        # Weather delay
        rainfall = float(context.get("rainfall_mm", 0.0))
        visibility = float(context.get("visibility_km", 10.0))
        weather_delay = rainfall * 0.25
        if visibility < 4.0:
            weather_delay += base_time * 0.15

        # Event delay
        event_level = str(context.get("event_level", "NONE")).upper()
        event_delays = {"LOW": 4.0, "MEDIUM": 10.0, "HIGH": 22.0}
        event_delay = event_delays.get(event_level, 0.0)

        # Road restriction delay
        restriction_type = str(context.get("road_restriction_type", "NONE")).upper()
        restriction_delays = {
            "LANE_RESTRICTION": 6.0,
            "CONSTRUCTION": 12.0,
            "PARTIAL_CLOSURE": 16.0,
            "ROAD_CLOSURE": 26.0,
        }
        restriction_delay = restriction_delays.get(restriction_type, 0.0)

        # Waste volume handling & collection stop dwell delay
        waste_tons = float(context.get("waste_volume_tons", 4.0))
        waste_delay = max(0.0, (waste_tons - 4.0) * 2.8)

        # Stochastic variation (reproducible with self._rng)
        noise_factor = 1.0 + self._rng.uniform(-0.04, 0.04)

        simulated_time = (base_time + weather_delay + event_delay + restriction_delay + waste_delay) * noise_factor
        return round(max(simulated_time, 5.0), 2)

    def run_scenario(
        self,
        scenario_key_or_params: Dict[str, Any],
        db: Session,
        route_id: Optional[int] = None,
        vehicle_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        persist_predictions: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute full scenario simulation:
        1. Merge parameters from predefined scenario if requested.
        2. Perform safety validation for vehicle capacity and driver shift bounds.
        3. If unsafe -> Reject and return UNSAFE_ASSIGNMENT status.
        4. Predict Baseline ETA.
        5. Predict Context-Aware ETA (if model available).
        6. Calculate Simulated Actual Travel Time.
        7. Compute Absolute Errors and Relative Improvement.
        8. Persist predictions to database if requested.
        """
        # 1. Resolve parameters
        params = dict(scenario_key_or_params)
        scenario_key = params.get("scenario_key", "CUSTOM").upper()
        
        if scenario_key in STANDARD_SCENARIOS:
            base_config = dict(STANDARD_SCENARIOS[scenario_key])
            base_config.update({k: v for k, v in params.items() if v is not None})
            params = base_config

        # Derive route info if route_id provided
        distance_km = float(params.get("distance_km", 0.0))
        if route_id:
            route = db.query(Route).filter(Route.id == route_id).first()
            if route:
                if distance_km <= 0:
                    distance_km = float(route.total_distance_km)
                if "waste_volume_tons" not in params:
                    params["waste_volume_tons"] = float(route.total_waste_tons)
                if not vehicle_id and route.assigned_vehicle_id:
                    vehicle_id = route.assigned_vehicle_id
                if not driver_id and route.assigned_driver_id:
                    driver_id = route.assigned_driver_id

        if distance_km <= 0:
            distance_km = 22.5  # Realistic standard urban route distance default

        params["distance_km"] = distance_km
        waste_tons = float(params.get("waste_volume_tons", 5.0))

        # 2. Safety Validation
        safety_status = "SAFE"
        safety_message = "All operational and labor safety constraints satisfied."
        violation_type = None

        # Resolve fallback vehicle & driver if not explicitly passed
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

        # 3. Handle unsafe scenario early if physical constraints breached
        if safety_status == "UNSAFE_ASSIGNMENT":
            logger.warning("Scenario halted: %s (%s)", safety_message, violation_type)
            return {
                "scenario_name": params.get("name", scenario_key),
                "scenario_key": scenario_key,
                "status": "UNSAFE_ASSIGNMENT",
                "is_safe": False,
                "constraint_violation": {
                    "type": violation_type,
                    "message": safety_message,
                },
                "parameters": params,
                "baseline_eta_minutes": None,
                "context_aware_eta_minutes": None,
                "simulated_actual_minutes": None,
                "baseline_error_minutes": None,
                "context_aware_error_minutes": None,
                "improvement_pct": None,
            }

        # 4. Compute Baseline ETA
        baseline_eta = predict_baseline_eta(distance_km=distance_km)

        # 5. Compute Context-Aware ETA
        if not is_model_available():
            raise RuntimeError("Context-Aware model is not trained yet. Please train model first.")

        pred_result = predict_eta_single(params)
        context_aware_eta = pred_result["context_aware_eta_minutes"]

        # Check driver workload safety with projected context-aware ETA
        if driver_id:
            driver_check = SafetyService.validate_driver_workload(driver_id, int(context_aware_eta), db)
            if not driver_check.is_valid:
                logger.warning("Scenario halted due to driver workload: %s", driver_check.message)
                return {
                    "scenario_name": params.get("name", scenario_key),
                    "scenario_key": scenario_key,
                    "status": "UNSAFE_ASSIGNMENT",
                    "is_safe": False,
                    "constraint_violation": {
                        "type": driver_check.violation_type,
                        "message": driver_check.message,
                    },
                    "parameters": params,
                    "baseline_eta_minutes": round(baseline_eta, 2),
                    "context_aware_eta_minutes": round(context_aware_eta, 2),
                    "simulated_actual_minutes": None,
                    "baseline_error_minutes": None,
                    "context_aware_error_minutes": None,
                    "improvement_pct": None,
                }

        # 6. Simulate Ground-Truth Actual Travel Time
        simulated_actual = self.simulate_actual_travel_minutes(params)

        # 7. Compute Errors and Improvement
        baseline_error = round(abs(baseline_eta - simulated_actual), 2)
        context_error = round(abs(context_aware_eta - simulated_actual), 2)

        improvement_pct = 0.0
        if baseline_error > 0:
            improvement_pct = round(((baseline_error - context_error) / baseline_error) * 100.0, 2)

        # 8. Persist predictions to Database if requested
        if persist_predictions and route_id:
            try:
                p_baseline = ETAPrediction(
                    route_id=route_id,
                    model_type="BASELINE",
                    predicted_eta_minutes=baseline_eta,
                    actual_eta_minutes=simulated_actual,
                    absolute_error_minutes=baseline_error,
                )
                p_context = ETAPrediction(
                    route_id=route_id,
                    model_type="CONTEXT_AWARE",
                    predicted_eta_minutes=context_aware_eta,
                    actual_eta_minutes=simulated_actual,
                    absolute_error_minutes=context_error,
                )
                db.add(p_baseline)
                db.add(p_context)
                db.commit()
            except Exception as e:
                logger.error("Failed to persist scenario ETA predictions: %s", e)
                db.rollback()

        return {
            "scenario_name": params.get("name", scenario_key),
            "scenario_key": scenario_key,
            "status": "COMPLETED",
            "is_safe": True,
            "distance_km": round(distance_km, 2),
            "waste_volume_tons": round(waste_tons, 2),
            "parameters": params,
            "baseline_eta_minutes": round(baseline_eta, 2),
            "context_aware_eta_minutes": round(context_aware_eta, 2),
            "simulated_actual_minutes": round(simulated_actual, 2),
            "baseline_error_minutes": baseline_error,
            "context_aware_error_minutes": context_error,
            "improvement_pct": improvement_pct,
            "safety_status": safety_status,
            "safety_message": safety_message,
        }
