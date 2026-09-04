from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, CheckConstraint
from app.core.database import Base


class TrafficCondition(Base):
    __tablename__ = "traffic_conditions"
    __table_args__ = (
        CheckConstraint("congestion_index >= 0 AND congestion_index <= 100", name="check_congestion_index_range"),
        CheckConstraint("average_speed_kmh >= 0", name="check_non_negative_speed"),
    )

    id = Column(Integer, primary_key=True, index=True)
    observation_time = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    traffic_level = Column(String(50), default="LOW", nullable=False)  # LOW, MEDIUM, HIGH, SEVERE
    congestion_index = Column(Float, default=0.0, nullable=False)  # 0 to 100
    average_speed_kmh = Column(Float, default=40.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
