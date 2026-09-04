from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        CheckConstraint("capacity_tons > 0", name="check_positive_vehicle_capacity"),
    )

    id = Column(Integer, primary_key=True, index=True)
    vehicle_code = Column(String(50), unique=True, index=True, nullable=False)
    vehicle_type = Column(String(50), default="COMPACTOR_TRUCK", nullable=False)
    capacity_tons = Column(Float, nullable=False)
    status = Column(String(30), default="AVAILABLE", nullable=False)  # AVAILABLE, IN_SERVICE, MAINTENANCE, UNAVAILABLE
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    routes = relationship("Route", back_populates="vehicle")
