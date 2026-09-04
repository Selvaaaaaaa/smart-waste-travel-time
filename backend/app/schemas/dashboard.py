from typing import List
from pydantic import BaseModel, Field


class OperatingConditions(BaseModel):
    weather: str = Field(default="Clear", description="Current weather condition")
    traffic: str = Field(default="Moderate", description="Current traffic level")
    event_impact: str = Field(default="Low", description="Impact of current local events")
    road_restrictions: str = Field(default="None", description="Active road restrictions or closures")
    waste_volume: str = Field(default="Normal", description="Current city-wide waste volume category")


class WasteVolumeDay(BaseModel):
    day: str = Field(..., description="Day of the week")
    volume_tons: float = Field(..., description="Waste volume in metric tons")


class ETAComparisonItem(BaseModel):
    route_id: str = Field(..., description="Unique route identifier")
    baseline_eta_min: float = Field(..., description="Baseline estimated travel time in minutes")
    context_eta_min: float = Field(..., description="Context-aware placeholder travel time in minutes")
    actual_eta_min: float = Field(..., description="Actual recorded travel time in minutes")


class ETAErrorItem(BaseModel):
    route_id: str = Field(..., description="Route identifier")
    baseline_error_min: float = Field(..., description="Baseline prediction absolute error in minutes")
    context_error_min: float = Field(..., description="Context-aware placeholder absolute error in minutes")


class VehicleUtilizationItem(BaseModel):
    vehicle_id: str = Field(..., description="Vehicle fleet ID")
    utilization_pct: float = Field(..., description="Capacity utilization percentage")
    capacity_tons: float = Field(..., description="Maximum vehicle tonnage capacity")
    current_load_tons: float = Field(..., description="Current loaded tonnage")


class DashboardSummary(BaseModel):
    waste_volume: float = Field(default=8.4, description="Today's total collected waste volume")
    waste_volume_unit: str = Field(default="tons", description="Measurement unit")
    active_routes: int = Field(default=12, description="Currently active waste collection routes")
    average_eta_min: float = Field(default=42.0, description="Average estimated travel time across routes")
    eta_accuracy_pct: float = Field(default=91.0, description="Overall ETA prediction accuracy percentage")
    available_vehicles: str = Field(default="8 / 10", description="Available vs total fleet ratio")
    workload_status: str = Field(default="Within Limits", description="Driver and worker workload status")
    operating_conditions: OperatingConditions
    waste_volume_trends: List[WasteVolumeDay]
    eta_comparisons: List[ETAComparisonItem]
    eta_errors: List[ETAErrorItem]
    vehicle_utilization: List[VehicleUtilizationItem]
    is_demo: bool = Field(default=True, description="Flag indicating synthetic Phase 1 demo data")
    phase: int = Field(default=1, description="Current system phase")
