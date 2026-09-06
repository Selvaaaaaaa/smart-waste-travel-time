"""Pydantic v2 schemas for Phase 9: Real-Time IoT Telemetry, Sensor Fusion & Production Deployment."""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------
# Telemetry Core Schemas
# ---------------------------------------------------------

class VehicleGPSTelemetry(BaseModel):
    model_config = ConfigDict(extra="allow")

    vehicle_id: str = Field(..., description="Unique vehicle identifier, e.g. V-01")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed_kmh: float = Field(default=0.0, ge=0.0)
    heading: float = Field(default=0.0, ge=0.0, le=360.0)
    current_route_id: Optional[str] = None
    current_task_id: Optional[str] = None
    engine_status: str = Field(default="RUNNING")  # RUNNING, IDLE, OFF, BREAKDOWN
    telemetry_sequence: int = Field(default=1, ge=1)
    health_status: str = Field(default="TELEMETRY_HEALTHY")
    source: str = Field(default="SIMULATED_GPS")


class BinSensorTelemetry(BaseModel):
    model_config = ConfigDict(extra="allow")

    bin_id: str = Field(..., description="Unique smart bin identifier, e.g. BIN-ZONE-A-01")
    location_node: str = Field(..., description="Node where bin is located, e.g. COLLECTION_ZONE_A")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    fill_level_percent: float = Field(..., ge=0.0, le=100.0)
    estimated_waste_kg: float = Field(default=0.0, ge=0.0)
    temperature_c: float = Field(default=21.0)
    sensor_battery_percent: float = Field(default=100.0, ge=0.0, le=100.0)
    sensor_status: str = Field(default="NORMAL")  # NORMAL, WARNING, FAULT
    status_classification: str = Field(default="NORMAL")  # NORMAL, MEDIUM, HIGH, CRITICAL
    sequence_number: int = Field(default=1, ge=1)
    health_status: str = Field(default="TELEMETRY_HEALTHY")
    source: str = Field(default="SIMULATED_BIN_SENSOR")


class TelemetryAlert(BaseModel):
    model_config = ConfigDict(extra="allow")

    alert_id: str
    alert_type: str  # CRITICAL_BIN, ROUTE_DEVIATION, TELEMETRY_STALE, BREAKDOWN, DISRUPTION
    severity: str  # INFO, WARNING, CRITICAL
    entity_id: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    recovery_action: Optional[str] = None
    resolved: bool = False


# ---------------------------------------------------------
# Fused Operational State & Health
# ---------------------------------------------------------

class RealtimeVehicleState(BaseModel):
    vehicle_id: str
    vehicle_code: str
    status: str  # AVAILABLE, ASSIGNED, EN_ROUTE, BREAKDOWN
    latitude: float
    longitude: float
    speed_kmh: float
    heading: float
    current_payload_kg: float
    capacity_kg: float
    utilization_pct: float
    current_task_id: Optional[str] = None
    current_route: List[str] = Field(default_factory=list)
    route_status: str = Field(default="ON_TRACK")  # ON_TRACK, DEVIATED, REROUTED
    deviation_distance_m: float = 0.0
    estimated_eta_min: float = 0.0
    telemetry_health: str = Field(default="TELEMETRY_HEALTHY")
    last_telemetry_timestamp: datetime
    depot_id: str = "DEPOT_CENTRAL"
    safety_status: str = "SAFE"


class RealtimeOperationalState(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    vehicles: List[RealtimeVehicleState] = Field(default_factory=list)
    bins: List[BinSensorTelemetry] = Field(default_factory=list)
    critical_bins_count: int = 0
    active_alerts: List[TelemetryAlert] = Field(default_factory=list)
    traffic_condition: str = "NORMAL"
    weather_condition: str = "CLEAR"
    fleet_workload_balance: float = 0.85
    average_eta_minutes: float = 24.5
    disclaimer: str = "Simulated Real-Time IoT Telemetry Layer"


class TelemetryHealthSummary(BaseModel):
    total_messages_received: int = 0
    valid_messages_count: int = 0
    invalid_messages_count: int = 0
    duplicate_messages_count: int = 0
    stale_vehicles_count: int = 0
    telemetry_health_rate_pct: float = 100.0
    vehicle_health: Dict[str, str] = Field(default_factory=dict)
    bin_health: Dict[str, str] = Field(default_factory=dict)
    active_alerts_count: int = 0
    websocket_clients_connected: int = 0
    disclaimer: str = "Deterministic Simulated Telemetry Health Metrics"


# ---------------------------------------------------------
# Multi-Depot Schemas
# ---------------------------------------------------------

class DepotInfo(BaseModel):
    depot_id: str
    name: str
    latitude: float
    longitude: float
    node_id: str
    active: bool = True
    assigned_vehicles_count: int = 0
    capacity_vehicles: int = 20


# ---------------------------------------------------------
# Authentication & RBAC Schemas
# ---------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


class AuthUser(BaseModel):
    username: str
    email: str
    role: str  # DISPATCHER, DRIVER, MUNICIPAL_SUPERVISOR
    assigned_vehicle_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int = 3600
    user: AuthUser


class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str
    role: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    reason: Optional[str] = None
    result: str = "SUCCESS"
    details: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------
# Experiment & Scalability Schemas
# ---------------------------------------------------------

class ScalabilityBenchmarkItem(BaseModel):
    vehicle_count: int
    depot_count: int
    telemetry_messages_processed: int
    average_processing_latency_ms: float
    peak_processing_latency_ms: float
    telemetry_throughput_msg_per_sec: float
    optimization_execution_time_ms: float
    memory_rss_mb: float
    status: str = "PASS"


class ScalabilityBenchmarkResult(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    benchmarks: List[ScalabilityBenchmarkItem] = Field(default_factory=list)
    scalability_verdict: str
    disclaimer: str = "Measured Empirical Scalability Benchmark"


class Phase9ScenarioStat(BaseModel):
    scenario: str
    runs_count: int
    telemetry_health_rate_pct: float
    route_deviations_detected: int
    critical_bins_detected: int
    emergency_requests_generated: int
    average_eta_recalculation_ms: float
    mean_eta_minutes: float
    rerouting_success_rate_pct: float
    failure_counts: Dict[str, int] = Field(default_factory=dict)


class Phase9BenchmarkSummary(BaseModel):
    total_runs: int = 40
    scenarios_evaluated: List[str] = Field(default_factory=list)
    seeds_evaluated: List[int] = Field(default_factory=list)
    overall_telemetry_health_rate_pct: float = 100.0
    total_telemetry_messages_generated: int = 0
    total_route_deviations_detected: int = 0
    total_critical_bins_detected: int = 0
    total_emergency_requests_generated: int = 0
    emergency_fulfillment_rate_pct: float = 100.0
    average_eta_recalculation_time_ms: float = 0.0
    scenario_stats: Dict[str, Phase9ScenarioStat] = Field(default_factory=dict)
    failure_counts_by_category: Dict[str, int] = Field(default_factory=dict)
    disclaimer: str = "Phase 9 Empirical 40-Run Benchmark Execution"
