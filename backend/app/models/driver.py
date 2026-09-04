from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class Driver(Base):
    __tablename__ = "drivers"
    __table_args__ = (
        CheckConstraint("max_work_minutes_per_shift > 0", name="check_positive_max_work_shift"),
        CheckConstraint("current_work_minutes >= 0", name="check_non_negative_current_work"),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    max_work_minutes_per_shift = Column(Integer, default=480, nullable=False)  # 8 hours max standard
    current_work_minutes = Column(Integer, default=0, nullable=False)
    status = Column(String(30), default="AVAILABLE", nullable=False)  # AVAILABLE, ON_DUTY, ON_BREAK, OFF_DUTY
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    routes = relationship("Route", back_populates="driver")
