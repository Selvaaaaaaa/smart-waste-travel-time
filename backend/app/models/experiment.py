from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_name = Column(String(150), nullable=False)
    description = Column(String(255), nullable=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="CREATED", nullable=False)  # CREATED, RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    scenario = relationship("Scenario", back_populates="experiments")
    results = relationship("ExperimentResult", back_populates="experiment", cascade="all, delete-orphan")
