from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, CheckConstraint
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("impact_radius_km >= 0", name="check_non_negative_event_radius"),
    )

    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(150), nullable=False)
    event_type = Column(String(50), default="COMMUNITY", nullable=False)  # SPORTS, CONCERT, FESTIVAL, PARADE, CIVIC
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    impact_radius_km = Column(Float, default=1.0, nullable=False)
    impact_level = Column(String(20), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
