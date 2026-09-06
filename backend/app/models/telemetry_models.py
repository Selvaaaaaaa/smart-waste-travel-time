"""SQLAlchemy domain models for Phase 9: Real-Time IoT Telemetry, Sensor Fusion & Audit Logging."""
from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, JSON
from app.core.database import Base


class VehicleTelemetryLog(Base):
    __tablename__ = "vehicle_telemetry_logs"

    id = Column(String(64), primary_key=True, index=True)
    vehicle_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=0.0, nullable=False)
    heading = Column(Float, default=0.0, nullable=False)
    current_route_id = Column(String(64), nullable=True)
    current_task_id = Column(String(64), nullable=True)
    engine_status = Column(String(30), default="RUNNING", nullable=False)
    telemetry_sequence = Column(Integer, default=1, nullable=False)
    health_status = Column(String(30), default="TELEMETRY_HEALTHY", nullable=False)
    source = Column(String(50), default="SIMULATED_GPS", nullable=False)


class BinTelemetryLog(Base):
    __tablename__ = "bin_telemetry_logs"

    id = Column(String(64), primary_key=True, index=True)
    bin_id = Column(String(64), nullable=False, index=True)
    location_node = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    fill_level_percent = Column(Float, default=0.0, nullable=False)
    estimated_waste_kg = Column(Float, default=0.0, nullable=False)
    temperature_c = Column(Float, default=20.0, nullable=False)
    sensor_battery_percent = Column(Float, default=100.0, nullable=False)
    sensor_status = Column(String(30), default="NORMAL", nullable=False)
    status_classification = Column(String(30), default="NORMAL", nullable=False)  # NORMAL, MEDIUM, HIGH, CRITICAL
    sequence_number = Column(Integer, default=1, nullable=False)
    health_status = Column(String(30), default="TELEMETRY_HEALTHY", nullable=False)
    source = Column(String(50), default="SIMULATED_BIN_SENSOR", nullable=False)


class TelemetryAlertLog(Base):
    __tablename__ = "telemetry_alert_logs"

    id = Column(String(64), primary_key=True, index=True)
    alert_type = Column(String(64), nullable=False, index=True)  # CRITICAL_BIN, ROUTE_DEVIATION, TELEMETRY_STALE, etc.
    severity = Column(String(30), default="WARNING", nullable=False)  # INFO, WARNING, CRITICAL
    entity_id = Column(String(64), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    recovery_action = Column(String(255), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)


class AuditLog(Base):
    __tablename__ = "operational_audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)  # LOGIN, TASK_ASSIGNED, EMERGENCY_REQUEST, etc.
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(64), nullable=True)
    reason = Column(String(500), nullable=True)
    result = Column(String(50), default="SUCCESS", nullable=False)
    details = Column(JSON, default=dict, nullable=False)


class Depot(Base):
    __tablename__ = "depots"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    node_id = Column(String(64), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    capacity_vehicles = Column(Integer, default=20, nullable=False)
