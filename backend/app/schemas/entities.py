from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# Pagination Schema
class PaginatedResponse(BaseModel):
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Items per page")
    total: int = Field(..., description="Total items matching query")
    total_pages: int = Field(..., description="Total available pages")
    is_demo: bool = Field(default=True, description="Indicates synthetic research dataset")


# 1. Vehicle Schemas
class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_code: str
    vehicle_type: str
    capacity_tons: float
    status: str
    active: bool
    created_at: datetime


class VehicleListResponse(PaginatedResponse):
    items: List[VehicleResponse]


# 2. Driver Schemas
class DriverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_code: str
    name: str
    max_work_minutes_per_shift: int
    current_work_minutes: int
    status: str
    active: bool
    created_at: datetime


class DriverListResponse(PaginatedResponse):
    items: List[DriverResponse]


# 3. Route & Stop Schemas
class RouteStopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: int
    stop_sequence: int
    latitude: float
    longitude: float
    waste_tons: float
    service_minutes: float
    completed: bool
    created_at: datetime


class RouteDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_code: str
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    vehicle_code: Optional[str] = None
    driver_name: Optional[str] = None
    route_date: date
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_distance_km: float
    total_waste_tons: float
    baseline_eta_minutes: float
    actual_duration_minutes: Optional[float] = None
    status: str
    stops: List[RouteStopResponse] = []
    created_at: datetime


# 4. Weather Schemas
class WeatherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    observation_time: datetime
    condition: str
    temperature_c: float
    rainfall_mm: float
    visibility_km: float
    severity: str
    created_at: datetime


class WeatherListResponse(PaginatedResponse):
    items: List[WeatherResponse]


# 5. Traffic Schemas
class TrafficResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    observation_time: datetime
    traffic_level: str
    congestion_index: float
    average_speed_kmh: float
    created_at: datetime


class TrafficListResponse(PaginatedResponse):
    items: List[TrafficResponse]


# 6. Event Schemas
class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_name: str
    event_type: str
    start_time: datetime
    end_time: datetime
    latitude: float
    longitude: float
    impact_radius_km: float
    impact_level: str
    created_at: datetime


class EventListResponse(PaginatedResponse):
    items: List[EventResponse]


# 7. Road Restriction Schemas
class RoadRestrictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    restriction_type: str
    description: str
    start_time: datetime
    end_time: datetime
    latitude: float
    longitude: float
    affected_radius_km: float
    severity: str
    active: bool
    created_at: datetime


class RoadRestrictionListResponse(PaginatedResponse):
    items: List[RoadRestrictionResponse]


# 8. Travel Time Observation Schemas
class ObservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    route_id: int
    observation_date: date
    distance_km: float
    baseline_travel_minutes: float
    actual_travel_minutes: float
    weather_id: Optional[int] = None
    traffic_id: Optional[int] = None
    event_id: Optional[int] = None
    road_restriction_id: Optional[int] = None
    waste_volume_tons: float
    hour_of_day: int
    day_of_week: int
    created_at: datetime


class ObservationListResponse(PaginatedResponse):
    items: List[ObservationResponse]


# 9. Scenario Schemas
class ScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scenario_name: str
    weather_condition: str
    traffic_level: str
    event_level: str
    road_restriction_level: str
    waste_volume_level: str
    time_of_day: str
    description: Optional[str] = None
    created_at: datetime


class ScenarioListResponse(PaginatedResponse):
    items: List[ScenarioResponse]


# 10. Experiment & Results Schemas
class ExperimentResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    model_type: str
    mae: float
    rmse: float
    mean_error: float
    median_error: float
    within_tolerance_percent: float
    route_completion_minutes: float
    created_at: datetime


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_name: str
    description: Optional[str] = None
    scenario_id: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    results: List[ExperimentResultResponse] = []
    created_at: datetime


class ExperimentListResponse(PaginatedResponse):
    items: List[ExperimentResponse]


# 11. Safety Check Request / Response
class SafetyCheckResponse(BaseModel):
    is_valid: bool
    message: str
    violation_type: Optional[str] = None
