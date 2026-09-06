"""Telemetry Ingestion Service with validation, sequence tracking, duplicate detection, and retention."""
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import deque

from app.schemas.telemetry import (
    VehicleGPSTelemetry,
    BinSensorTelemetry,
    TelemetryHealthSummary,
    TelemetryAlert,
)
from app.telemetry.validation import TelemetryQualityValidator


class TelemetryIngestionService:
    """Thread-safe telemetry ingestion pipeline with quality enforcement and retention management."""

    def __init__(self, max_retention_per_entity: int = 100):
        self._lock = threading.Lock()
        self.max_retention = max_retention_per_entity

        # Latest validated states
        self._latest_vehicles: Dict[str, VehicleGPSTelemetry] = {}
        self._latest_bins: Dict[str, BinSensorTelemetry] = {}

        # Historical circular buffer per entity
        self._vehicle_history: Dict[str, deque] = {}
        self._bin_history: Dict[str, deque] = {}

        # Sequence tracking: entity_id -> last_sequence
        self._vehicle_seq_tracker: Dict[str, int] = {}
        self._bin_seq_tracker: Dict[str, int] = {}

        # Health metrics counters
        self.total_received: int = 0
        self.valid_count: int = 0
        self.invalid_count: int = 0
        self.duplicate_count: int = 0
        self.stale_count: int = 0

        # Active telemetry alerts
        self._alerts: List[TelemetryAlert] = []

    def ingest_vehicle_gps(self, payload: Dict[str, Any]) -> Tuple[bool, str, Optional[VehicleGPSTelemetry]]:
        """Ingest, validate, and track a raw vehicle GPS message.
        
        Returns:
            (is_accepted, health_status, validated_model)
        """
        with self._lock:
            self.total_received += 1
            is_valid, reason, validated = TelemetryQualityValidator.validate_gps_telemetry(payload)

            if not is_valid or not validated:
                self.invalid_count += 1
                return False, "TELEMETRY_INVALID", None

            veh_id = validated.vehicle_id
            seq = validated.telemetry_sequence

            # 1. Duplicate & Out-of-order check
            last_seq = self._vehicle_seq_tracker.get(veh_id, 0)
            if seq <= last_seq:
                self.duplicate_count += 1
                validated.health_status = "TELEMETRY_DUPLICATE"
                return True, "TELEMETRY_DUPLICATE", validated

            self._vehicle_seq_tracker[veh_id] = seq

            # 2. Staleness check
            if TelemetryQualityValidator.is_telemetry_stale(validated.timestamp):
                self.stale_count += 1
                validated.health_status = "TELEMETRY_STALE"
                self._create_alert(
                    alert_type="TELEMETRY_STALE",
                    severity="WARNING",
                    entity_id=veh_id,
                    message=f"Vehicle {veh_id} telemetry timestamp is older than threshold (STALE).",
                    recovery_action="MAINTAIN_LAST_KNOWN_POSITION",
                )
            else:
                validated.health_status = "TELEMETRY_HEALTHY"

            # 3. Store latest & history
            self.valid_count += 1
            self._latest_vehicles[veh_id] = validated

            if veh_id not in self._vehicle_history:
                self._vehicle_history[veh_id] = deque(maxlen=self.max_retention)
            self._vehicle_history[veh_id].append(validated)

            return True, validated.health_status, validated

    def ingest_bin_sensor(self, payload: Dict[str, Any]) -> Tuple[bool, str, Optional[BinSensorTelemetry]]:
        """Ingest, validate, and track a smart waste bin sensor telemetry message."""
        with self._lock:
            self.total_received += 1
            is_valid, reason, validated = TelemetryQualityValidator.validate_bin_telemetry(payload)

            if not is_valid or not validated:
                self.invalid_count += 1
                return False, "BIN_SENSOR_INVALID", None

            bin_id = validated.bin_id
            seq = validated.sequence_number

            # Duplicate check
            last_seq = self._bin_seq_tracker.get(bin_id, 0)
            if seq <= last_seq:
                self.duplicate_count += 1
                validated.health_status = "TELEMETRY_DUPLICATE"
                return True, "TELEMETRY_DUPLICATE", validated

            self._bin_seq_tracker[bin_id] = seq

            if TelemetryQualityValidator.is_telemetry_stale(validated.timestamp):
                self.stale_count += 1
                validated.health_status = "TELEMETRY_STALE"
            else:
                validated.health_status = "TELEMETRY_HEALTHY"

            self.valid_count += 1
            self._latest_bins[bin_id] = validated

            if bin_id not in self._bin_history:
                self._bin_history[bin_id] = deque(maxlen=self.max_retention)
            self._bin_history[bin_id].append(validated)

            return True, validated.health_status, validated

    def get_latest_vehicle_telemetry(self, vehicle_id: str) -> Optional[VehicleGPSTelemetry]:
        with self._lock:
            return self._latest_vehicles.get(vehicle_id)

    def get_all_latest_vehicles(self) -> List[VehicleGPSTelemetry]:
        with self._lock:
            return list(self._latest_vehicles.values())

    def get_latest_bin_telemetry(self, bin_id: str) -> Optional[BinSensorTelemetry]:
        with self._lock:
            return self._latest_bins.get(bin_id)

    def get_all_latest_bins(self) -> List[BinSensorTelemetry]:
        with self._lock:
            return list(self._latest_bins.values())

    def get_alerts(self, limit: int = 50) -> List[TelemetryAlert]:
        with self._lock:
            return list(self._alerts[-limit:])

    def add_alert(self, alert: TelemetryAlert):
        with self._lock:
            self._alerts.append(alert)

    def _create_alert(self, alert_type: str, severity: str, entity_id: str, message: str, recovery_action: Optional[str] = None):
        alert = TelemetryAlert(
            alert_id=f"ALT-{len(self._alerts) + 1:04d}",
            alert_type=alert_type,
            severity=severity,
            entity_id=entity_id,
            message=message,
            timestamp=datetime.utcnow(),
            recovery_action=recovery_action,
            resolved=False,
        )
        self._alerts.append(alert)

    def get_health_summary(self) -> TelemetryHealthSummary:
        """Compute aggregated telemetry health statistics across fleet and sensor nodes."""
        with self._lock:
            total = max(1, self.total_received)
            health_rate = round((self.valid_count / total) * 100.0, 2)

            v_health = {v_id: v.health_status for v_id, v in self._latest_vehicles.items()}
            b_health = {b_id: b.health_status for b_id, b in self._latest_bins.items()}
            stale_vehicles = sum(1 for status in v_health.values() if status == "TELEMETRY_STALE")

            return TelemetryHealthSummary(
                total_messages_received=self.total_received,
                valid_messages_count=self.valid_count,
                invalid_messages_count=self.invalid_count,
                duplicate_messages_count=self.duplicate_count,
                stale_vehicles_count=stale_vehicles,
                telemetry_health_rate_pct=health_rate,
                vehicle_health=v_health,
                bin_health=b_health,
                active_alerts_count=len(self._alerts),
                websocket_clients_connected=0,
                disclaimer="Deterministic Simulated Telemetry Health Metrics",
            )
