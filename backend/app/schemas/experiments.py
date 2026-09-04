from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.schemas.ml import EvaluationMetricsSchema


class ExperimentRunRequest(BaseModel):
    scenario_key: str = Field(default="ALL", description="Scenario key: 'NORMAL', 'HEAVY_RAIN', 'MAJOR_EVENT', 'ROAD_CLOSURE', 'HIGH_WASTE', 'COMBINED_STRESS', or 'ALL' for full suite benchmark")
    repetitions: int = Field(default=5, ge=1, le=50, description="Number of deterministic repetitions with controlled seeds")


class ExperimentRunItem(BaseModel):
    scenario_key: str
    scenario_name: str
    seed: int
    route_id: str
    distance_km: float
    is_safe: bool
    status: str
    baseline_eta_minutes: Optional[float] = None
    context_aware_eta_minutes: Optional[float] = None
    actual_travel_minutes: Optional[float] = None
    baseline_error_minutes: Optional[float] = None
    context_aware_error_minutes: Optional[float] = None
    improvement_pct: Optional[float] = None
    safety_message: Optional[str] = None


class ScenarioExperimentSummary(BaseModel):
    experiment_id: Optional[int] = None
    scenario_key: str
    scenario_name: str
    repetitions: int
    total_runs: int
    safe_runs: int
    unsafe_runs: int
    winner: str  # BASELINE, CONTEXT_AWARE, TIE, UNSAFE
    metrics: Dict[str, Any]
    safety_summary: Dict[str, Any]


class FailureCaseItem(BaseModel):
    scenario_key: str
    scenario_name: str
    route_id: str
    seed: int
    baseline_eta_minutes: Optional[float] = None
    context_aware_eta_minutes: Optional[float] = None
    actual_travel_minutes: Optional[float] = None
    baseline_error_minutes: Optional[float] = None
    context_aware_error_minutes: Optional[float] = None
    error_delta_minutes: Optional[float] = None
    failure_reason: str
    is_safe: bool
    safety_message: Optional[str] = None


class FailureAnalysisResponse(BaseModel):
    total_runs: int
    total_failures: int
    failure_rate_pct: float
    category_breakdown: Dict[str, int]
    failure_cases: List[FailureCaseItem]


class WorstErrorItem(BaseModel):
    rank: int
    route: str
    scenario: str
    seed: int
    predicted_eta: float
    actual_eta: float
    absolute_error: float
    signed_error: float
    reason: str


class TopWorstErrorsResponse(BaseModel):
    baseline_worst: List[WorstErrorItem]
    context_aware_worst: List[WorstErrorItem]


class ExperimentBenchmarkResponse(BaseModel):
    total_scenarios: int
    total_experiment_runs: int
    safe_runs_count: int
    unsafe_runs_count: int
    global_metrics: Dict[str, Any]
    scenario_breakdown: List[ScenarioExperimentSummary]
    failure_analysis: FailureAnalysisResponse
    top_worst_errors: TopWorstErrorsResponse
    synthetic_disclaimer: str = "Synthetic Dataset — Research Prototype"
