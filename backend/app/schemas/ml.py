from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MLTrainRequest(BaseModel):
    model_type: str = Field(default="random_forest", description="Tree-based model type: 'random_forest' or 'gradient_boosting'")
    random_state: int = Field(default=42, description="Random seed for reproducible train/test splits and estimator initialization")
    n_estimators: int = Field(default=100, ge=10, le=500, description="Number of trees in ensemble")


class EvaluationMetricsSchema(BaseModel):
    mae: float
    rmse: float
    mean_error: float
    median_absolute_error: float
    within_tolerance_pct: float
    tolerance_minutes: float
    sample_count: int


class ModelMetricsComparison(BaseModel):
    baseline: EvaluationMetricsSchema
    context_aware: EvaluationMetricsSchema
    mae_improvement_pct: float
    rmse_improvement_pct: float
    is_improved: bool


class FeatureImportanceItem(BaseModel):
    feature: str
    importance: float


class MLStatusResponse(BaseModel):
    is_trained: bool
    model_name: Optional[str] = None
    model_type: Optional[str] = None
    model_version: Optional[str] = None
    training_date: Optional[str] = None
    training_row_count: Optional[int] = None
    testing_row_count: Optional[int] = None
    total_dataset_rows: Optional[int] = None
    metrics: Optional[ModelMetricsComparison] = None
    feature_importances: Optional[List[FeatureImportanceItem]] = None
    split_method: Optional[str] = None
    synthetic_disclaimer: str = "Synthetic Dataset — Research Prototype"


class MLTrainResponse(BaseModel):
    status: str
    message: str
    metadata: MLStatusResponse


class ETAPredictRequest(BaseModel):
    distance_km: float = Field(..., gt=0, description="Route distance in kilometers (must be > 0)")
    waste_volume_tons: float = Field(default=5.0, ge=0, description="Total waste volume in metric tons")
    weather_condition: str = Field(default="CLEAR", description="Weather condition (e.g. CLEAR, RAIN, HEAVY_RAIN, STORM)")
    rainfall_mm: float = Field(default=0.0, ge=0, description="Precipitation in millimeters")
    visibility_km: float = Field(default=10.0, ge=0, description="Atmospheric visibility in kilometers")
    traffic_level: str = Field(default="LOW", description="Traffic density level (e.g. LOW, MEDIUM, HIGH, SEVERE)")
    congestion_index: float = Field(default=15.0, ge=0, le=100, description="Congestion index percentage (0 - 100)")
    average_speed_kmh: float = Field(default=40.0, gt=0, description="Estimated average road network speed")
    event_level: str = Field(default="NONE", description="Special event impact level (NONE, LOW, MEDIUM, HIGH)")
    event_radius: float = Field(default=0.0, ge=0, description="Event impact radius in km")
    road_restriction_type: str = Field(default="NONE", description="Active road restriction or closure")
    road_restriction_severity: str = Field(default="NONE", description="Restriction severity level")
    hour_of_day: int = Field(default=9, ge=0, le=23, description="Hour of dispatch (0 - 23)")
    day_of_week: int = Field(default=1, ge=0, le=6, description="Day of week (0 = Monday, 6 = Sunday)")
    route_id: Optional[int] = Field(default=None, description="Optional associated route ID")
    persist: bool = Field(default=False, description="Persist prediction record to database")


class ETAPredictResponse(BaseModel):
    distance_km: float
    baseline_eta_minutes: float
    context_aware_eta_minutes: float
    difference_minutes: float
    baseline_speed_kmh: float
    context_applied: Dict[str, Any]
    hybrid_eta_minutes: Optional[float] = None
    selected_model: Optional[str] = None
    selection_reason: Optional[str] = None
    prediction_spread_minutes: Optional[float] = None
    safety_status: Optional[str] = "SAFE"


class HybridPredictRequest(BaseModel):
    distance_km: float = Field(..., gt=0, description="Route distance in kilometers")
    waste_volume_tons: float = Field(default=5.0, ge=0, description="Total waste volume in metric tons")
    weather_condition: str = Field(default="CLEAR", description="Weather condition (e.g. CLEAR, RAIN, HEAVY_RAIN, STORM)")
    rainfall_mm: float = Field(default=0.0, ge=0, description="Precipitation in millimeters")
    visibility_km: float = Field(default=10.0, ge=0, description="Atmospheric visibility in kilometers")
    traffic_level: str = Field(default="LOW", description="Traffic density level (e.g. LOW, MEDIUM, HIGH, SEVERE)")
    congestion_index: float = Field(default=15.0, ge=0, le=100, description="Congestion index percentage (0 - 100)")
    average_speed_kmh: float = Field(default=40.0, gt=0, description="Estimated average road network speed")
    event_level: str = Field(default="NONE", description="Special event impact level (NONE, LOW, MEDIUM, HIGH)")
    event_radius: float = Field(default=0.0, ge=0, description="Event impact radius in km")
    road_restriction_type: str = Field(default="NONE", description="Active road restriction or closure")
    road_restriction_severity: str = Field(default="NONE", description="Restriction severity level")
    hour_of_day: int = Field(default=9, ge=0, le=23, description="Hour of dispatch (0 - 23)")
    day_of_week: int = Field(default=1, ge=0, le=6, description="Day of week (0 = Monday, 6 = Sunday)")
    route_id: Optional[int] = Field(default=None, description="Optional associated route ID")
    vehicle_id: Optional[int] = Field(default=None, description="Optional vehicle ID for capacity safety check")
    driver_id: Optional[int] = Field(default=None, description="Optional driver ID for workload safety check")
    persist: bool = Field(default=False, description="Persist prediction record to database")


class HybridPredictResponse(BaseModel):
    selected_model: str
    predicted_eta_minutes: Optional[float] = None
    selection_reason: str
    prediction_spread_minutes: Optional[float] = None
    safety_status: str
    is_safe: bool
    baseline_eta_minutes: Optional[float] = None
    context_aware_eta_minutes: Optional[float] = None
    constraint_violation: Optional[Dict[str, Any]] = None
    policy_version: str = "hybrid-v1"


class ScenarioRunRequest(BaseModel):
    scenario_key: Optional[str] = Field(default="CUSTOM", description="Predefined scenario key (e.g. NORMAL, HEAVY_RAIN, MAJOR_EVENT, ROAD_CLOSURE, HIGH_WASTE, COMBINED_STRESS) or CUSTOM")
    route_id: Optional[int] = Field(default=None, description="Optional specific route ID to evaluate")
    vehicle_id: Optional[int] = Field(default=None, description="Optional specific vehicle ID for capacity safety validation")
    driver_id: Optional[int] = Field(default=None, description="Optional specific driver ID for shift workload safety validation")
    distance_km: Optional[float] = Field(default=None, gt=0, description="Route distance in km")
    waste_volume_tons: Optional[float] = Field(default=None, ge=0, description="Waste payload in tons")
    weather_condition: Optional[str] = Field(default=None, description="Weather condition")
    rainfall_mm: Optional[float] = Field(default=None, ge=0, description="Rainfall in mm")
    visibility_km: Optional[float] = Field(default=None, ge=0, description="Visibility in km")
    traffic_level: Optional[str] = Field(default=None, description="Traffic congestion level")
    congestion_index: Optional[float] = Field(default=None, ge=0, le=100, description="Congestion index (0 - 100)")
    average_speed_kmh: Optional[float] = Field(default=None, gt=0, description="Average speed km/h")
    event_level: Optional[str] = Field(default=None, description="Event impact level")
    event_radius: Optional[float] = Field(default=None, ge=0, description="Event radius in km")
    road_restriction_type: Optional[str] = Field(default=None, description="Road restriction type")
    road_restriction_severity: Optional[str] = Field(default=None, description="Road restriction severity")
    hour_of_day: Optional[int] = Field(default=None, ge=0, le=23, description="Hour of day (0-23)")
    day_of_week: Optional[int] = Field(default=None, ge=0, le=6, description="Day of week (0-6)")


class ConstraintViolationInfo(BaseModel):
    type: Optional[str]
    message: str


class ScenarioRunResponse(BaseModel):
    scenario_name: str
    scenario_key: str
    status: str  # "COMPLETED" or "UNSAFE_ASSIGNMENT"
    is_safe: bool
    constraint_violation: Optional[ConstraintViolationInfo] = None
    parameters: Dict[str, Any]
    baseline_eta_minutes: Optional[float] = None
    context_aware_eta_minutes: Optional[float] = None
    simulated_actual_minutes: Optional[float] = None
    baseline_error_minutes: Optional[float] = None
    context_aware_error_minutes: Optional[float] = None
    improvement_pct: Optional[float] = None
    safety_status: Optional[str] = None
    safety_message: Optional[str] = None
