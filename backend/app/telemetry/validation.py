"""Validation and quality evaluation service for simulated vehicle GPS and smart waste bin telemetry."""
import math
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
from app.schemas.telemetry import VehicleGPSTelemetry, BinSensorTelemetry


class BinThresholdConfig:
    """Configurable thresholds for smart waste bin classification."""
    NORMAL_MAX: float = 49.99
    MEDIUM_MAX: float = 74.99
    HIGH_MAX: float = 89.99
    CRITICAL_MIN: float = 90.0


def classify_bin_fill_level(fill_percent: float, config: BinThresholdConfig = BinThresholdConfig()) -> str:
    """Classify bin fill level percent into operational category using configurable thresholds."""
    if fill_percent < 0.0:
        return "NORMAL"
    if fill_percent <= config.NORMAL_MAX:
        return "NORMAL"
    elif fill_percent <= config.MEDIUM_MAX:
        return "MEDIUM"
    elif fill_percent <= config.HIGH_MAX:
        return "HIGH"
    else:
        return "CRITICAL"


class TelemetryQualityValidator:
    """Validates raw incoming telemetry payloads against domain safety and physical bounds."""

    # Default configurable threshold
    STALE_TIMEOUT_SECONDS: float = 30.0
    MAX_REASONABLE_SPEED_KMH: float = 140.0

    @classmethod
    def validate_gps_telemetry(cls, payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[VehicleGPSTelemetry]]:
        """Validate vehicle GPS telemetry against physical limits.
        
        Returns:
            (is_valid, rejection_reason, validated_model)
        """
        try:
            veh_id = str(payload.get("vehicle_id", "")).strip()
            if not veh_id:
                return False, "VEHICLE_ID_MISSING", None

            lat = float(payload.get("latitude", 0.0))
            if lat < -90.0 or lat > 90.0 or math.isnan(lat):
                return False, "GPS_OUT_OF_RANGE: Latitude must be between -90 and 90", None

            lng = float(payload.get("longitude", 0.0))
            if lng < -180.0 or lng > 180.0 or math.isnan(lng):
                return False, "GPS_OUT_OF_RANGE: Longitude must be between -180 and 180", None

            speed = float(payload.get("speed_kmh", 0.0))
            if speed < 0.0:
                return False, "TELEMETRY_INVALID: Speed cannot be negative", None
            if speed > cls.MAX_REASONABLE_SPEED_KMH:
                return False, f"TELEMETRY_INVALID: Impossible speed {speed} km/h exceeds ceiling {cls.MAX_REASONABLE_SPEED_KMH} km/h", None

            heading = float(payload.get("heading", 0.0)) % 360.0
            seq = int(payload.get("telemetry_sequence", 1))
            if seq < 1:
                return False, "TELEMETRY_INVALID: Sequence number must be positive", None

            raw_ts = payload.get("timestamp")
            if isinstance(raw_ts, str):
                try:
                    ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except ValueError:
                    ts = datetime.utcnow()
            elif isinstance(raw_ts, datetime):
                ts = raw_ts
            else:
                ts = datetime.utcnow()

            validated = VehicleGPSTelemetry(
                vehicle_id=veh_id,
                timestamp=ts,
                latitude=round(lat, 6),
                longitude=round(lng, 6),
                speed_kmh=round(speed, 2),
                heading=round(heading, 1),
                current_route_id=payload.get("current_route_id"),
                current_task_id=payload.get("current_task_id"),
                engine_status=payload.get("engine_status", "RUNNING"),
                telemetry_sequence=seq,
                health_status="TELEMETRY_HEALTHY",
                source=payload.get("source", "SIMULATED_GPS"),
            )
            return True, None, validated

        except Exception as e:
            return False, f"TELEMETRY_INVALID: Malformed payload ({str(e)})", None

    @classmethod
    def validate_bin_telemetry(cls, payload: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[BinSensorTelemetry]]:
        """Validate smart waste-bin sensor telemetry against sensor physical bounds.
        
        Returns:
            (is_valid, rejection_reason, validated_model)
        """
        try:
            bin_id = str(payload.get("bin_id", "")).strip()
            if not bin_id:
                return False, "BIN_ID_MISSING", None

            node = str(payload.get("location_node", "COLLECTION_ZONE_A")).strip()

            fill = float(payload.get("fill_level_percent", 0.0))
            if fill < 0.0 or fill > 100.0 or math.isnan(fill):
                return False, f"BIN_SENSOR_INVALID: Fill level {fill}% out of bounds [0, 100]", None

            waste_kg = float(payload.get("estimated_waste_kg", 0.0))
            if waste_kg < 0.0 or math.isnan(waste_kg):
                return False, "BIN_SENSOR_INVALID: Estimated waste kg cannot be negative", None

            battery = float(payload.get("sensor_battery_percent", 100.0))
            if battery < 0.0 or battery > 100.0 or math.isnan(battery):
                return False, f"BIN_SENSOR_INVALID: Battery {battery}% out of bounds [0, 100]", None

            temp = float(payload.get("temperature_c", 20.0))
            seq = int(payload.get("sequence_number", 1))

            raw_ts = payload.get("timestamp")
            if isinstance(raw_ts, str):
                try:
                    ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                except ValueError:
                    ts = datetime.utcnow()
            elif isinstance(raw_ts, datetime):
                ts = raw_ts
            else:
                ts = datetime.utcnow()

            classification = classify_bin_fill_level(fill)

            validated = BinSensorTelemetry(
                bin_id=bin_id,
                location_node=node,
                timestamp=ts,
                fill_level_percent=round(fill, 1),
                estimated_waste_kg=round(waste_kg, 1),
                temperature_c=round(temp, 1),
                sensor_battery_percent=round(battery, 1),
                sensor_status="CRITICAL" if fill >= 90.0 else "NORMAL",
                status_classification=classification,
                sequence_number=seq,
                health_status="TELEMETRY_HEALTHY",
                source=payload.get("source", "SIMULATED_BIN_SENSOR"),
            )
            return True, None, validated

        except Exception as e:
            return False, f"BIN_SENSOR_INVALID: Malformed payload ({str(e)})", None

    @classmethod
    def is_telemetry_stale(
        cls,
        last_timestamp: datetime,
        current_time: Optional[datetime] = None,
        timeout_seconds: Optional[float] = None,
    ) -> bool:
        """Check if telemetry timestamp exceeds the configurable staleness threshold."""
        timeout = timeout_seconds if timeout_seconds is not None else cls.STALE_TIMEOUT_SECONDS
        curr = current_time or datetime.utcnow()
        # Ensure timezone-naive UTC comparison
        if last_timestamp.tzinfo is not None:
            last_timestamp = last_timestamp.replace(tzinfo=None)
        if curr.tzinfo is not None:
            curr = curr.replace(tzinfo=None)
        delta_sec = abs((curr - last_timestamp).total_seconds())
        return delta_sec > timeout
