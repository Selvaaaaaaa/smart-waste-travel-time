from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Route(Base):
    __tablename__ = "routes"
    __table_args__ = (
        CheckConstraint("total_distance_km >= 0", name="check_non_negative_route_distance"),
        CheckConstraint("total_waste_tons >= 0", name="check_non_negative_route_waste"),
        CheckConstraint("baseline_eta_minutes >= 0", name="check_non_negative_baseline_eta"),
    )

    id = Column(Integer, primary_key=True, index=True)
    route_code = Column(String(50), unique=True, index=True, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True)
    route_date = Column(Date, default=date.today, index=True, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    total_distance_km = Column(Float, default=0.0, nullable=False)
    total_waste_tons = Column(Float, default=0.0, nullable=False)
    baseline_eta_minutes = Column(Float, default=0.0, nullable=False)
    actual_duration_minutes = Column(Float, nullable=True)
    status = Column(String(30), default="SCHEDULED", nullable=False)  # SCHEDULED, IN_PROGRESS, COMPLETED, DELAYED, AT_RISK
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    vehicle = relationship("Vehicle", back_populates="routes")
    driver = relationship("Driver", back_populates="routes")
    stops = relationship("RouteStop", back_populates="route", cascade="all, delete-orphan", order_by="RouteStop.stop_sequence")
    waste_collections = relationship("WasteCollection", back_populates="route", cascade="all, delete-orphan")
    observations = relationship("TravelTimeObservation", back_populates="route", cascade="all, delete-orphan")
    eta_predictions = relationship("ETAPrediction", back_populates="route", cascade="all, delete-orphan")
