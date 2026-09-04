from typing import List
from pydantic import BaseModel, Field


class ScenarioOptionsResponse(BaseModel):
    weather_options: List[str] = Field(default=["Clear", "Light Rain", "Heavy Rain"])
    traffic_options: List[str] = Field(default=["Low", "Medium", "High"])
    event_options: List[str] = Field(default=["None", "Small Event", "Major Event"])
    road_restriction_options: List[str] = Field(default=["None", "Partial Closure", "Full Closure"])
    waste_volume_options: List[str] = Field(default=["Low", "Normal", "High", "Extreme"])
    time_of_day_options: List[str] = Field(default=["Morning", "Afternoon", "Evening", "Night"])
    is_demo: bool = Field(default=True, description="Indicates placeholder scenario options for Phase 1")
