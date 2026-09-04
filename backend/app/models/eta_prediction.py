from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ETAPrediction(Base):
    __tablename__ = "eta_predictions"
    __table_args__ = (
        CheckConstraint("predicted_eta_minutes >= 0", name="check_predicted_eta_non_negative"),
    )

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_time = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    model_type = Column(String(50), default="BASELINE", index=True, nullable=False)  # BASELINE, CONTEXT_AWARE
    predicted_eta_minutes = Column(Float, nullable=False)
    actual_eta_minutes = Column(Float, nullable=True)
    absolute_error_minutes = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    route = relationship("Route", back_populates="eta_predictions")
