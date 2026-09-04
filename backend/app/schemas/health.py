from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status", json_schema_extra={"example": "ok"})
    service: str = Field(..., description="Service identifier", json_schema_extra={"example": "smart-waste-travel-time-api"})
    phase: int = Field(..., description="Project phase number", json_schema_extra={"example": 1})
