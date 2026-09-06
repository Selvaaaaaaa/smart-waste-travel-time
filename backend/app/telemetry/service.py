"""Telemetry Coordinator Service unifying generator, ingestion, sensor fusion, and streaming."""
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from app.routing.graph import get_default_network_graph
from app.fleet.fleet_state import FleetStateManager
from app.telemetry.generator import TelemetryGenerator
from app.telemetry.ingestion import TelemetryIngestionService
from app.telemetry.fusion import SensorFusionService
from app.telemetry.depots import depot_service
from app.telemetry.stream import stream_manager
from app.telemetry.audit import audit_service
from app.schemas.telemetry import RealtimeOperationalState, TelemetryHealthSummary, TelemetryAlert


class TelemetryCoordinatorService:
    """Central coordinator for real-time telemetry generation, ingestion, sensor fusion, and live streaming."""

    def __init__(self):
        self.graph = get_default_network_graph()
        self.fleet_manager = FleetStateManager()
        self.generator = TelemetryGenerator(self.graph)
        self.ingestion = TelemetryIngestionService()
        self.fusion = SensorFusionService(self.graph, self.fleet_manager, self.ingestion)
        self.depots = depot_service
        self.stream = stream_manager
        self.audit = audit_service

        # Initialize fleet vehicle tracking in generator
        self._sync_fleet_with_generator()

    def _sync_fleet_with_generator(self):
        """Synchronize fleet manager vehicles into telemetry generator."""
        vehicles = self.fleet_manager.get_all_vehicles()
        for v in vehicles:
            self.generator.register_vehicle(
                vehicle_id=v["vehicle_id"],
                current_node=v.get("current_location", "DEPOT_CENTRAL"),
                route=v.get("current_route", []),
                task_id=v.get("current_task_id"),
            )

    def step_simulation(self, elapsed_seconds: float = 5.0) -> RealtimeOperationalState:
        """Step all vehicles along routes and progress bin fill levels, fusing state and triggering checks."""
        self._sync_fleet_with_generator()
        vehicles = self.fleet_manager.get_all_vehicles()

        # 1. Step vehicle GPS telemetry & ingest
        for v in vehicles:
            raw_gps = self.generator.step_vehicle_gps(v["vehicle_id"], elapsed_seconds=elapsed_seconds)
            self.ingestion.ingest_vehicle_gps(raw_gps.model_dump())

        # 2. Step smart bins & ingest
        bins = self.generator.get_all_bins()
        for b in bins:
            updated_bin = self.generator.step_bin_sensor(b.bin_id, fill_increment=0.4)
            self.ingestion.ingest_bin_sensor(updated_bin.model_dump())

        # 3. Sensor fusion & critical checks
        fused_state = self.fusion.get_fused_operational_state()

        # 4. Asynchronously broadcast state update to active WebSocket clients if event loop is running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.stream.broadcast_state(fused_state))
        except Exception:
            pass

        return fused_state

    def get_realtime_state(self) -> RealtimeOperationalState:
        """Fetch current fused operational state snapshot."""
        return self.fusion.get_fused_operational_state()

    def get_health_summary(self) -> TelemetryHealthSummary:
        """Fetch current telemetry and system health status."""
        health = self.ingestion.get_health_summary()
        health.websocket_clients_connected = self.stream.client_count
        return health

    def get_alerts(self, limit: int = 50) -> List[TelemetryAlert]:
        return self.ingestion.get_alerts(limit=limit)


# Global singleton coordinator instance
telemetry_service = TelemetryCoordinatorService()
