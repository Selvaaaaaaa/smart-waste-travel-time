from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ExperimentResult(Base):
    __tablename__ = "experiment_results"
    __table_args__ = (
        CheckConstraint("mae >= 0", name="check_mae_non_negative"),
        CheckConstraint("rmse >= 0", name="check_rmse_non_negative"),
        CheckConstraint("within_tolerance_percent >= 0 AND within_tolerance_percent <= 100", name="check_tolerance_range"),
    )

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    model_type = Column(String(50), default="BASELINE", nullable=False)  # BASELINE, CONTEXT_AWARE
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mean_error = Column(Float, nullable=False)
    median_error = Column(Float, nullable=False)
    within_tolerance_percent = Column(Float, nullable=False)
    route_completion_minutes = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    experiment = relationship("Experiment", back_populates="results")
