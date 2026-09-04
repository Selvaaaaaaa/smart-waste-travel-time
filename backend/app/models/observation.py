from datetime import datetime, date
from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class TravelTimeObservation(Base):
    __tablename__ = "travel_time_observations"
    __table_args__ = (
        CheckConstraint("distance_km >= 0", name="check_obs_distance_non_negative"),
        CheckConstraint("baseline_travel_minutes >= 0", name="check_obs_baseline_non_negative"),
        CheckConstraint("actual_travel_minutes >= 0", name="check_obs_actual_non_negative"),
        CheckConstraint("hour_of_day >= 0 AND hour_of_day <= 23", name="check_valid_hour"),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="check_valid_day_of_week"),
    )

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_date = Column(Date, default=date.today, index=True, nullable=False)
    distance_km = Column(Float, nullable=False)
    baseline_travel_minutes = Column(Float, nullable=False)
    actual_travel_minutes = Column(Float, nullable=False)
    weather_id = Column(Integer, ForeignKey("weather_conditions.id", ondelete="SET NULL"), nullable=True)
    traffic_id = Column(Integer, ForeignKey("traffic_conditions.id", ondelete="SET NULL"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="SET NULL"), nullable=True)
    road_restriction_id = Column(Integer, ForeignKey("road_restrictions.id", ondelete="SET NULL"), nullable=True)
    waste_volume_tons = Column(Float, default=0.0, nullable=False)
    hour_of_day = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    route = relationship("Route", back_populates="observations")
    weather = relationship("WeatherCondition")
    traffic = relationship("TrafficCondition")
    event = relationship("Event")
    road_restriction = relationship("RoadRestriction")
