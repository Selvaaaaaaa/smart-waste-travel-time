from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON, Integer, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class ActiveTrip(Base):
    __tablename__ = "active_trips"
    __table_args__ = (
        CheckConstraint("current_payload_kg >= 0", name="check_active_trip_payload"),
        CheckConstraint("elapsed_time_minutes >= 0", name="check_active_trip_elapsed"),
    )

    id = Column(String(64), primary_key=True, index=True)
    vehicle_id = Column(String(64), nullable=False)
    driver_id = Column(String(64), nullable=False)
    origin_node = Column(String(64), default="DEPOT_CENTRAL", nullable=False)
    destination_node = Column(String(64), default="LANDFILL_MAIN", nullable=False)
    current_node = Column(String(64), default="DEPOT_CENTRAL", nullable=False)
    
    visited_nodes = Column(JSON, default=list, nullable=False)
    remaining_stops = Column(JSON, default=list, nullable=False)
    current_path = Column(JSON, default=list, nullable=False)
    
    current_payload_kg = Column(Float, default=0.0, nullable=False)
    vehicle_capacity_kg = Column(Float, default=8000.0, nullable=False)
    elapsed_time_minutes = Column(Float, default=0.0, nullable=False)
    max_shift_hours = Column(Float, default=8.0, nullable=False)
    distance_traveled_km = Column(Float, default=0.0, nullable=False)
    
    current_eta_minutes = Column(Float, default=45.0, nullable=False)
    baseline_eta_minutes = Column(Float, default=45.0, nullable=False)
    hybrid_eta_minutes = Column(Float, default=45.0, nullable=False)
    eta_uncertainty_minutes = Column(Float, default=2.0, nullable=False)
    
    status = Column(String(30), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, COMPLETED, PAUSED
    active_disruptions = Column(JSON, default=list, nullable=False)
    reroute_count = Column(Integer, default=0, nullable=False)
    notes = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    candidates = relationship("RouteCandidate", back_populates="active_trip", cascade="all, delete-orphan")
    events = relationship("ReroutingEvent", back_populates="active_trip", cascade="all, delete-orphan")


class RouteCandidate(Base):
    __tablename__ = "route_candidates"

    id = Column(String(64), primary_key=True, index=True)
    trip_id = Column(String(64), ForeignKey("active_trips.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy = Column(String(64), nullable=False)  # SHORTEST_PATH, AVOID_TRAFFIC, AVOID_CLOSURE, AVOID_WEATHER, BALANCED
    
    path = Column(JSON, default=list, nullable=False)
    path_coordinates = Column(JSON, default=list, nullable=False)
    total_distance_km = Column(Float, nullable=False)
    predicted_eta_minutes = Column(Float, nullable=False)
    baseline_eta_minutes = Column(Float, nullable=False)
    hybrid_eta_minutes = Column(Float, nullable=False)
    eta_uncertainty_minutes = Column(Float, default=2.0, nullable=False)
    
    safety_valid = Column(Boolean, default=True, nullable=False)
    safety_violations = Column(JSON, default=list, nullable=False)
    optimization_score = Column(Float, default=0.0, nullable=False)
    is_selected = Column(Boolean, default=False, nullable=False)
    rejection_reason = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    active_trip = relationship("ActiveTrip", back_populates="candidates")


class ReroutingEvent(Base):
    __tablename__ = "rerouting_events"

    id = Column(String(64), primary_key=True, index=True)
    trip_id = Column(String(64), ForeignKey("active_trips.id", ondelete="CASCADE"), nullable=False, index=True)
    
    trigger_type = Column(String(64), nullable=False)  # ROAD_CLOSURE, TRAFFIC_SPIKE, MAJOR_EVENT, HEAVY_RAIN, etc.
    trigger_details = Column(JSON, default=dict, nullable=False)
    previous_path = Column(JSON, default=list, nullable=False)
    new_path = Column(JSON, default=list, nullable=False)
    
    previous_eta_minutes = Column(Float, nullable=False)
    new_eta_minutes = Column(Float, nullable=False)
    time_saved_minutes = Column(Float, default=0.0, nullable=False)
    distance_difference_km = Column(Float, default=0.0, nullable=False)
    
    selected_candidate_id = Column(String(64), nullable=True)
    candidate_count = Column(Integer, default=0, nullable=False)
    decision_rationale = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    active_trip = relationship("ActiveTrip", back_populates="events")
