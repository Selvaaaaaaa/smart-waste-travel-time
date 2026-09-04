from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class RouteStop(Base):
    __tablename__ = "route_stops"
    __table_args__ = (
        CheckConstraint("stop_sequence >= 1", name="check_positive_stop_sequence"),
        CheckConstraint("waste_tons >= 0", name="check_non_negative_stop_waste"),
        CheckConstraint("service_minutes >= 0", name="check_non_negative_service_minutes"),
        CheckConstraint("latitude >= -90 AND latitude <= 90", name="check_valid_latitude"),
        CheckConstraint("longitude >= -180 AND longitude <= 180", name="check_valid_longitude"),
    )

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    stop_sequence = Column(Integer, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    waste_tons = Column(Float, default=0.0, nullable=False)
    service_minutes = Column(Float, default=5.0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    route = relationship("Route", back_populates="stops")
    waste_collections = relationship("WasteCollection", back_populates="stop")
