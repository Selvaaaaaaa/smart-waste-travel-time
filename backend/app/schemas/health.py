from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status", json_schema_extra={"example": "ok"})
    service: str = Field(..., description="Service identifier", json_schema_extra={"example": "smart-waste-travel-time-api"})
    phase: int = Field(..., description="Project phase number", json_schema_extra={"example": 2})
    database: Optional[str] = Field("HEALTHY", description="Database connection health")
    telemetry: Optional[str] = Field("HEALTHY", description="Telemetry pipeline health")
    websocket: Optional[str] = Field("HEALTHY", description="WebSocket broadcaster health")
    simulation: Optional[str] = Field("HEALTHY", description="Simulation engine health")
    timestamp: Optional[str] = Field(None, description="Current UTC timestamp")
