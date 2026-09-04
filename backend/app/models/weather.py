from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base


class WeatherCondition(Base):
    __tablename__ = "weather_conditions"

    id = Column(Integer, primary_key=True, index=True)
    observation_time = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    condition = Column(String(50), default="CLEAR", nullable=False)  # CLEAR, CLOUDY, LIGHT_RAIN, HEAVY_RAIN, STORM
    temperature_c = Column(Float, nullable=False)
    rainfall_mm = Column(Float, default=0.0, nullable=False)
    visibility_km = Column(Float, default=10.0, nullable=False)
    severity = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
