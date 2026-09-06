"""Sensor Fusion Layer combining GPS telemetry, vehicle state, bin fill levels, traffic, and weather.

Implements route deviation detection, critical bin emergency generation, and real-time ETA updates.
"""
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from app.routing.graph import RoadNetworkGraph, get_default_network_graph
from app.fleet.fleet_state import FleetStateManager
from app.ml.hybrid import predict_hybrid_eta
from app.telemetry.ingestion import TelemetryIngestionService
from app.telemetry.generator import haversine_distance_meters
from app.schemas.telemetry import (
    RealtimeOperationalState,
    RealtimeVehicleState,
    TelemetryAlert,
    BinSensorTelemetry,
)


def point_to_segment_distance_meters(
    p_lat: float, p_lng: float,
    a_lat: float, a_lng: float,
    b_lat: float, b_lng: float
) -> float:
    """Calculate perpendicular distance in meters from point P to line segment AB."""
    # Convert lat/lng to approximate Cartesian plane coordinates (in meters) around point A
    deg_lat_meters = 111139.0
    deg_lng_meters = 111139.0 * math.cos(math.radians(a_lat))

    px = (p_lng - a_lng) * deg_lng_meters
    py = (p_lat - a_lat) * deg_lat_meters
    bx = (b_lng - a_lng) * deg_lng_meters
    by = (b_lat - a_lat) * deg_lat_meters

    segment_len_sq = bx * bx + by * by
    if segment_len_sq <= 0.0:
        return math.hypot(px, py)

    # Project point onto segment, clamp t between [0, 1]
    t = max(0.0, min(1.0, (px * bx + py * by) / segment_len_sq))
    proj_x = t * bx
    proj_y = t * by

    return math.hypot(px - proj_x, py - proj_y)


class SensorFusionService:
    """Combines streaming GPS, vehicle status, bin telemetry, and environmental factors into a unified state."""

    ROUTE_DEVIATION_THRESHOLD_METERS: float = 100.0

    def __init__(
        self,
        graph: Optional[RoadNetworkGraph] = None,
        fleet_manager: Optional[FleetStateManager] = None,
        ingestion_service: Optional[TelemetryIngestionService] = None,
    ):
        self.graph = graph or get_default_network_graph()
        self.fleet_manager = fleet_manager or FleetStateManager()
        self.ingestion = ingestion_service or TelemetryIngestionService()

        # Track already generated emergency collection requests for critical bins
        self._critical_bin_emergency_generated: Dict[str, datetime] = {}
        self._active_emergency_requests: List[Dict[str, Any]] = []
        # Track active route deviation alerts
        self._active_deviations: Dict[str, float] = {}

    def calculate_route_deviation(
        self,
        current_lat: float,
        current_lng: float,
        route_nodes: List[str],
    ) -> Tuple[bool, float]:
        """Check if vehicle location has deviated more than 100 meters from scheduled route."""
        if not route_nodes or len(route_nodes) < 2:
            return False, 0.0

        min_dist = float("inf")
        for i in range(len(route_nodes) - 1):
            u = route_nodes[i]
            v = route_nodes[i + 1]
            if u in self.graph.nodes and v in self.graph.nodes:
                node_a = self.graph.nodes[u]
                node_b = self.graph.nodes[v]
                d = point_to_segment_distance_meters(
                    current_lat, current_lng,
                    node_a["lat"], node_a["lng"],
                    node_b["lat"], node_b["lng"],
                )
                if d < min_dist:
                    min_dist = d

        if min_dist == float("inf"):
            min_dist = 0.0

        is_deviated = min_dist > self.ROUTE_DEVIATION_THRESHOLD_METERS
        return is_deviated, round(min_dist, 1)

    def get_active_emergency_requests(self) -> List[Dict[str, Any]]:
        """Return all recorded emergency requests from critical bins."""
        return list(self._active_emergency_requests)

    def evaluate_critical_bins_and_generate_requests(self, ignore_cooldown: bool = False) -> List[Dict[str, Any]]:
        """Inspect all smart bin telemetry and generate EMERGENCY_COLLECTION_REQUEST for critical bins."""
        critical_requests = []
        bins = self.ingestion.get_all_latest_bins()
        now = datetime.utcnow()

        for b in bins:
            if b.status_classification == "CRITICAL" or b.fill_level_percent >= 90.0:
                # Check if emergency request was already emitted recently (cooldown 120s)
                last_gen = self._critical_bin_emergency_generated.get(b.bin_id)
                if ignore_cooldown or (not last_gen or (now - last_gen).total_seconds() > 120.0):
                    self._critical_bin_emergency_generated[b.bin_id] = now
                    req = {
                        "id": f"EMG-BIN-{b.bin_id}",
                        "bin_id": b.bin_id,
                        "location_node": b.location_node,
                        "estimated_waste_kg": b.estimated_waste_kg or (b.fill_level_percent * 10.0),
                        "priority": "URGENT",
                        "request_type": "EMERGENCY_REQUEST",
                        "created_at": now.isoformat(),
                        "reason": f"CRITICAL_BIN_FILL_LEVEL: Smart bin {b.bin_id} fill level at {b.fill_level_percent}%",
                        "source": "SIMULATED_BIN_SENSOR",
                    }
                    critical_requests.append(req)
                    self._active_emergency_requests.append(req)

                    # Also add a telemetry alert
                    self.ingestion.add_alert(TelemetryAlert(
                        alert_id=f"ALT-CRIT-{b.bin_id}",
                        alert_type="CRITICAL_BIN",
                        severity="CRITICAL",
                        entity_id=b.bin_id,
                        message=f"Smart bin {b.bin_id} reached CRITICAL fill level ({b.fill_level_percent}%). Emergency collection triggered.",
                        timestamp=now,
                        recovery_action="TRIGGER_EMERGENCY_TASK_ALLOCATION",
                        resolved=False,
                    ))

        return critical_requests

    def recalculate_realtime_eta(
        self,
        vehicle_id: str,
        current_lat: float,
        current_lng: float,
        remaining_route: List[str],
        weather: str = "CLEAR",
        traffic: str = "NORMAL",
    ) -> float:
        """Dynamically compute pre-trip / in-transit Adaptive Hybrid ETA without future outcome leakage."""
        if not remaining_route or len(remaining_route) < 2:
            return 0.0

        # Calculate remaining route distance in km
        remaining_dist_km = self.graph.compute_path_distance(remaining_route)
        speed_kmh = 35.0
        if traffic == "HEAVY" or traffic == "CONGESTED":
            speed_kmh = 18.0
        elif weather == "HEAVY_RAIN":
            speed_kmh = 24.0

        baseline_eta = (remaining_dist_km / speed_kmh) * 60.0

        # Pre-trip feature vector for Hybrid ETA without post-trip leakage
        features = {
            "route_distance_km": remaining_dist_km,
            "waste_volume_tons": 2.5,
            "collection_stops_count": max(1, len(remaining_route) - 1),
            "vehicle_capacity_tons": 12.0,
            "weather_condition": weather,
            "traffic_level": traffic,
            "rainfall_mm": 35.0 if weather == "HEAVY_RAIN" else 0.0,
            "visibility_km": 4.0 if weather == "HEAVY_RAIN" else 10.0,
            "congestion_index": 75.0 if traffic == "HEAVY" else 20.0,
            "temperature_c": 22.0,
            "time_of_day": "AFTERNOON",
            "day_of_week": "WEDNESDAY",
            "is_weekend": False,
            "is_rush_hour": traffic in ["HEAVY", "CONGESTED"],
            "event_impact": "NONE",
            "road_restriction_type": "NONE",
        }

        try:
            features["distance_km"] = remaining_dist_km
            pred = predict_hybrid_eta(features)
            return round(pred["predicted_eta_minutes"], 1)
        except Exception:
            return round(baseline_eta, 1)

    def get_fused_operational_state(
        self,
        weather: str = "CLEAR",
        traffic: str = "NORMAL",
    ) -> RealtimeOperationalState:
        """Synthesize telemetry, vehicle states, route tracking, and environment into a unified state."""
        now = datetime.utcnow()
        fleet_vehicles = self.fleet_manager.get_all_vehicles()
        fused_vehicles: List[RealtimeVehicleState] = []

        # Check for critical bin emergency requests
        self.evaluate_critical_bins_and_generate_requests()

        total_eta = 0.0
        eta_count = 0

        for v in fleet_vehicles:
            v_id = v["vehicle_id"]
            telemetry = self.ingestion.get_latest_vehicle_telemetry(v_id)

            if telemetry:
                lat = telemetry.latitude
                lng = telemetry.longitude
                speed = telemetry.speed_kmh
                heading = telemetry.heading
                health = telemetry.health_status
                ts = telemetry.timestamp
            else:
                # Fallback to current node location
                curr_loc = v.get("current_location", "DEPOT_CENTRAL")
                node = self.graph.nodes.get(curr_loc, self.graph.nodes["DEPOT_CENTRAL"])
                lat = node["lat"]
                lng = node["lng"]
                speed = 0.0
                heading = 0.0
                health = "TELEMETRY_HEALTHY"
                ts = now

            # Route deviation evaluation
            v_route = v.get("current_route", [])
            is_deviated, dev_dist = self.calculate_route_deviation(lat, lng, v_route)
            route_status = "ON_TRACK"

            if is_deviated:
                route_status = "DEVIATED"
                self._active_deviations[v_id] = dev_dist
                # Emit alert if not already logged
                self.ingestion.add_alert(TelemetryAlert(
                    alert_id=f"ALT-DEV-{v_id}",
                    alert_type="ROUTE_DEVIATION",
                    severity="WARNING",
                    entity_id=v_id,
                    message=f"Vehicle {v_id} deviated from planned route by {dev_dist}m (threshold {self.ROUTE_DEVIATION_THRESHOLD_METERS}m).",
                    timestamp=now,
                    recovery_action="EVALUATE_DYNAMIC_REROUTING",
                    resolved=False,
                ))
            else:
                self._active_deviations.pop(v_id, None)

            # In-transit ETA calculation
            est_eta = self.recalculate_realtime_eta(v_id, lat, lng, v_route, weather=weather, traffic=traffic)
            if est_eta > 0.0:
                total_eta += est_eta
                eta_count += 1

            fused_v = RealtimeVehicleState(
                vehicle_id=v_id,
                vehicle_code=v["vehicle_code"],
                status=v["status"],
                latitude=lat,
                longitude=lng,
                speed_kmh=speed,
                heading=heading,
                current_payload_kg=v["current_payload_kg"],
                capacity_kg=v["capacity_kg"],
                utilization_pct=v["utilization_pct"],
                current_task_id=v.get("current_task_id"),
                current_route=v_route,
                route_status=route_status,
                deviation_distance_m=dev_dist,
                estimated_eta_min=est_eta,
                telemetry_health=health,
                last_telemetry_timestamp=ts,
                depot_id="DEPOT_CENTRAL",
                safety_status=v.get("safety_status", "SAFE"),
            )
            fused_vehicles.append(fused_v)

        bins = self.ingestion.get_all_latest_bins()
        crit_count = sum(1 for b in bins if b.status_classification == "CRITICAL")
        avg_eta = round(total_eta / max(1, eta_count), 1) if eta_count > 0 else 24.5

        return RealtimeOperationalState(
            timestamp=now,
            vehicles=fused_vehicles,
            bins=bins,
            critical_bins_count=crit_count,
            active_alerts=self.ingestion.get_alerts(20),
            traffic_condition=traffic,
            weather_condition=weather,
            fleet_workload_balance=round(self.fleet_manager.get_fleet_load_balance_score(), 2),
            average_eta_minutes=avg_eta,
            disclaimer="Simulated Real-Time IoT Telemetry Layer",
        )
