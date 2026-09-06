"""Phase 9 Real-Time IoT Telemetry & Sensor Fusion package."""
from app.telemetry.validation import TelemetryQualityValidator, classify_bin_fill_level
from app.telemetry.generator import TelemetryGenerator
from app.telemetry.ingestion import TelemetryIngestionService
from app.telemetry.fusion import SensorFusionService
from app.telemetry.depots import depot_service
from app.telemetry.stream import stream_manager
from app.telemetry.auth import AuthService, get_current_user, require_role
from app.telemetry.audit import audit_service
from app.telemetry.service import telemetry_service

__all__ = [
    "TelemetryQualityValidator",
    "classify_bin_fill_level",
    "TelemetryGenerator",
    "TelemetryIngestionService",
    "SensorFusionService",
    "depot_service",
    "stream_manager",
    "AuthService",
    "get_current_user",
    "require_role",
    "audit_service",
    "telemetry_service",
]
