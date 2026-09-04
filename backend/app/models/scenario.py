from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    scenario_name = Column(String(100), unique=True, index=True, nullable=False)
    weather_condition = Column(String(50), default="Clear", nullable=False)
    traffic_level = Column(String(50), default="Low", nullable=False)
    event_level = Column(String(50), default="None", nullable=False)
    road_restriction_level = Column(String(50), default="None", nullable=False)
    waste_volume_level = Column(String(50), default="Normal", nullable=False)
    time_of_day = Column(String(50), default="Morning", nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    experiments = relationship("Experiment", back_populates="scenario")
