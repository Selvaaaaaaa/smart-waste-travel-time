from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, CheckConstraint
from app.core.database import Base


class RoadRestriction(Base):
    __tablename__ = "road_restrictions"
    __table_args__ = (
        CheckConstraint("affected_radius_km >= 0", name="check_non_negative_restriction_radius"),
    )

    id = Column(Integer, primary_key=True, index=True)
    restriction_type = Column(String(50), nullable=False)  # ROAD_CLOSURE, PARTIAL_CLOSURE, CONSTRUCTION, LANE_RESTRICTION
    description = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    affected_radius_km = Column(Float, default=0.5, nullable=False)
    severity = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
