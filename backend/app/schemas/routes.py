from typing import List
from pydantic import BaseModel, Field


class RouteStop(BaseModel):
    stop_id: str = Field(..., description="Unique stop identifier")
    name: str = Field(..., description="Synthetic stop landmark name")
    lat: float = Field(..., description="Latitude coordinate")
    lng: float = Field(..., description="Longitude coordinate")
    waste_volume_kg: float = Field(..., description="Waste accumulated at stop")
    sequence: int = Field(..., description="Stop sequence in route")


class RouteItem(BaseModel):
    route_id: str = Field(..., description="Route unique code")
    vehicle_id: str = Field(..., description="Assigned vehicle ID")
    driver_name: str = Field(..., description="Assigned driver name (synthetic)")
    waste_volume_tons: float = Field(..., description="Total collected waste in metric tons")
    distance_km: float = Field(..., description="Total route distance in kilometers")
    baseline_eta_min: float = Field(..., description="Baseline travel time in minutes")
    context_eta_min: float = Field(..., description="Context-aware estimated travel time in minutes")
    status: str = Field(..., description="Operational status: On Schedule, Delayed, At Risk")
    collection_stops_count: int = Field(..., description="Total number of stops")
    stops: List[RouteStop] = Field(default_factory=list, description="Synthetic collection stop points")


class RouteListResponse(BaseModel):
    routes: List[RouteItem]
    total: int
    is_demo: bool = Field(default=True, description="Indicates synthetic demo data for Phase 1")
