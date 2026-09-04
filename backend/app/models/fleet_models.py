"""SQLAlchemy domain models for Phase 7: Multi-Vehicle Fleet Coordination & Dynamic Task Allocation."""
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON, Integer, CheckConstraint
from app.core.database import Base


class CollectionTask(Base):
    __tablename__ = "collection_tasks"
    __table_args__ = (
        CheckConstraint("estimated_waste_kg >= 0", name="check_positive_task_waste"),
    )

    id = Column(String(64), primary_key=True, index=True)
    location_node = Column(String(64), nullable=False, index=True)
    estimated_waste_kg = Column(Float, default=1000.0, nullable=False)
    priority = Column(String(30), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH, URGENT
    request_type = Column(String(50), default="SCHEDULED_COLLECTION", nullable=False)  # SCHEDULED_COLLECTION, EMERGENCY_REQUEST
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, DEFERRED
    
    assigned_vehicle_id = Column(String(64), nullable=True, index=True)
    assigned_driver_id = Column(String(64), nullable=True, index=True)
    deadline_minutes = Column(Float, nullable=True)
    notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class FleetAuditEvent(Base):
    __tablename__ = "fleet_audit_events"

    id = Column(String(64), primary_key=True, index=True)
    event_type = Column(String(64), nullable=False)  # TASK_ASSIGNED, EMERGENCY_INSERTED, BREAKDOWN_TRIGGERED, REBALANCED, TASK_DEFERRED
    task_id = Column(String(64), nullable=True, index=True)
    
    previous_vehicle_id = Column(String(64), nullable=True)
    new_vehicle_id = Column(String(64), nullable=True)
    previous_route = Column(JSON, default=list, nullable=False)
    new_route = Column(JSON, default=list, nullable=False)
    
    predicted_eta_before = Column(Float, nullable=True)
    predicted_eta_after = Column(Float, nullable=True)
    distance_difference_km = Column(Float, default=0.0, nullable=False)
    
    safety_result = Column(String(30), default="SAFE", nullable=False)
    selected_eta_model = Column(String(50), default="ADAPTIVE_HYBRID", nullable=False)
    reason = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
