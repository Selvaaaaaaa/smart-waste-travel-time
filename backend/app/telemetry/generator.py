"""Deterministic Simulated IoT Telemetry Generator for Vehicles and Smart Waste Bins.

Generates realistic GPS movement along network graph edges and smart bin fill progression.
"""
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.routing.graph import RoadNetworkGraph, get_default_network_graph
from app.schemas.telemetry import VehicleGPSTelemetry, BinSensorTelemetry
from app.telemetry.validation import classify_bin_fill_level


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate compass bearing (heading in degrees 0-360) from point 1 to point 2."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


class TelemetryGenerator:
    """Generates deterministic simulated telemetry streams for fleet vehicles and smart waste bins."""

    def __init__(self, graph: Optional[RoadNetworkGraph] = None, seed: int = 42):
        self.seed = seed
        self.rng = random.Random(seed)
        self.graph = graph or get_default_network_graph()

        # Vehicle tracking states: vehicle_id -> state dict
        self._vehicle_states: Dict[str, Dict[str, Any]] = {}
        # Smart bins states: bin_id -> BinSensorTelemetry
        self._bin_states: Dict[str, BinSensorTelemetry] = {}
        # Sequence trackers
        self._vehicle_seq: Dict[str, int] = {}
        self._bin_seq: Dict[str, int] = {}

        self._initialize_bins()

    def _initialize_bins(self):
        """Initialize smart bins across municipal collection zones and transfer hubs."""
        nodes = [
            ("BIN-ZONE-A-01", "COLLECTION_ZONE_A", 45.0, 450.0),
            ("BIN-ZONE-A-02", "COLLECTION_ZONE_A", 72.0, 720.0),
            ("BIN-ZONE-B-01", "COLLECTION_ZONE_B", 30.0, 300.0),
            ("BIN-ZONE-B-02", "COLLECTION_ZONE_B", 82.0, 820.0),
            ("BIN-ZONE-C-01", "COLLECTION_ZONE_C", 55.0, 550.0),
            ("BIN-ZONE-C-02", "COLLECTION_ZONE_C", 91.0, 910.0),  # Critical candidate
            ("BIN-ZONE-D-01", "COLLECTION_ZONE_D", 25.0, 250.0),
            ("BIN-ZONE-D-02", "COLLECTION_ZONE_D", 68.0, 680.0),
            ("BIN-ZONE-E-01", "COLLECTION_ZONE_E", 40.0, 400.0),
            ("BIN-ZONE-F-01", "COLLECTION_ZONE_F", 78.0, 780.0),
            ("BIN-HUB-N-01", "TRANSFER_STATION_NORTH", 35.0, 700.0),
            ("BIN-HUB-S-01", "TRANSFER_STATION_SOUTH", 50.0, 1000.0),
        ]
        now = datetime.utcnow()
        for bin_id, node_id, fill, waste_kg in nodes:
            self._bin_states[bin_id] = BinSensorTelemetry(
                bin_id=bin_id,
                location_node=node_id,
                timestamp=now,
                fill_level_percent=fill,
                estimated_waste_kg=waste_kg,
                temperature_c=20.0 + self.rng.uniform(-2.0, 3.0),
                sensor_battery_percent=95.0,
                sensor_status="CRITICAL" if fill >= 90.0 else "NORMAL",
                status_classification=classify_bin_fill_level(fill),
                sequence_number=1,
                health_status="TELEMETRY_HEALTHY",
                source="SIMULATED_BIN_SENSOR",
            )
            self._bin_seq[bin_id] = 1

    def register_vehicle(self, vehicle_id: str, current_node: str, route: Optional[List[str]] = None, task_id: Optional[str] = None):
        """Register or update an active vehicle's tracking trajectory."""
        node_info = self.graph.nodes.get(current_node, self.graph.nodes["DEPOT_CENTRAL"])
        self._vehicle_states[vehicle_id] = {
            "current_node": current_node,
            "target_node": route[1] if route and len(route) > 1 else current_node,
            "route": list(route or [current_node]),
            "route_step_index": 0,
            "fraction_along_edge": 0.0,
            "current_lat": node_info["lat"],
            "current_lng": node_info["lng"],
            "speed_kmh": 35.0,
            "heading": 0.0,
            "engine_status": "RUNNING",
            "task_id": task_id,
            "route_id": f"RT-{vehicle_id}",
            "is_deviated": False,
            "is_stale": False,
        }
        if vehicle_id not in self._vehicle_seq:
            self._vehicle_seq[vehicle_id] = 1

    def step_vehicle_gps(self, vehicle_id: str, elapsed_seconds: float = 5.0) -> VehicleGPSTelemetry:
        """Simulate continuous movement of a vehicle along its planned road segments."""
        if vehicle_id not in self._vehicle_states:
            self.register_vehicle(vehicle_id, "DEPOT_CENTRAL")

        st = self._vehicle_states[vehicle_id]
        now = datetime.utcnow()

        if st.get("is_stale"):
            # Stale injection: timestamp stays back in time
            now = now - timedelta(seconds=60.0)

        route = st.get("route", [])
        idx = st.get("route_step_index", 0)

        # If vehicle has a route with multiple nodes, progress along the current edge
        if route and len(route) > 1 and idx < len(route) - 1:
            u = route[idx]
            v = route[idx + 1]
            u_node = self.graph.nodes.get(u, self.graph.nodes["DEPOT_CENTRAL"])
            v_node = self.graph.nodes.get(v, self.graph.nodes["DEPOT_CENTRAL"])

            # Compute edge distance
            edge_dist_km = self.graph.compute_path_distance([u, v])
            if edge_dist_km <= 0.0:
                edge_dist_km = 1.0

            # Calculate distance traveled in elapsed time
            speed_kmh = st["speed_kmh"]
            dist_traveled_km = (speed_kmh / 3600.0) * elapsed_seconds
            frac_increment = dist_traveled_km / edge_dist_km

            new_frac = st["fraction_along_edge"] + frac_increment
            if new_frac >= 1.0:
                # Transitioned to next node
                idx += 1
                st["route_step_index"] = idx
                st["fraction_along_edge"] = 0.0
                st["current_node"] = v
                st["current_lat"] = v_node["lat"]
                st["current_lng"] = v_node["lng"]
            else:
                st["fraction_along_edge"] = new_frac
                # Interpolate coordinate
                lat = u_node["lat"] + new_frac * (v_node["lat"] - u_node["lat"])
                lng = u_node["lng"] + new_frac * (v_node["lng"] - u_node["lng"])
                st["current_lat"] = lat
                st["current_lng"] = lng

            # Compute heading
            st["heading"] = calculate_bearing(u_node["lat"], u_node["lng"], v_node["lat"], v_node["lng"])
        else:
            # Stationary at current node
            node_info = self.graph.nodes.get(st["current_node"], self.graph.nodes["DEPOT_CENTRAL"])
            st["current_lat"] = node_info["lat"]
            st["current_lng"] = node_info["lng"]
            st["speed_kmh"] = 0.0

        # Route deviation injection if flagged
        lat = st["current_lat"]
        lng = st["current_lng"]
        if st.get("is_deviated"):
            # Deviate by ~250 meters northward
            lat += 0.00225

        seq = self._vehicle_seq[vehicle_id]
        self._vehicle_seq[vehicle_id] = seq + 1

        telemetry = VehicleGPSTelemetry(
            vehicle_id=vehicle_id,
            timestamp=now,
            latitude=round(lat, 6),
            longitude=round(lng, 6),
            speed_kmh=round(st["speed_kmh"], 2),
            heading=round(st["heading"], 1),
            current_route_id=st.get("route_id"),
            current_task_id=st.get("task_id"),
            engine_status=st.get("engine_status", "RUNNING"),
            telemetry_sequence=seq,
            health_status="TELEMETRY_HEALTHY",
            source="SIMULATED_GPS",
        )
        return telemetry

    def step_bin_sensor(self, bin_id: str, fill_increment: float = 0.5) -> BinSensorTelemetry:
        """Simulate stochastic fill level progression and sensor telemetry generation."""
        if bin_id not in self._bin_states:
            self._initialize_bins()

        bin_obj = self._bin_states[bin_id]
        now = datetime.utcnow()
        new_fill = min(100.0, bin_obj.fill_level_percent + fill_increment)
        # Approximate waste kg
        new_waste = round(new_fill * 10.0, 1)
        # Slight battery drain (0.01%)
        new_battery = max(10.0, bin_obj.sensor_battery_percent - 0.01)

        seq = self._bin_seq.get(bin_id, 1) + 1
        self._bin_seq[bin_id] = seq

        classification = classify_bin_fill_level(new_fill)

        updated_bin = BinSensorTelemetry(
            bin_id=bin_id,
            location_node=bin_obj.location_node,
            timestamp=now,
            fill_level_percent=round(new_fill, 1),
            estimated_waste_kg=new_waste,
            temperature_c=round(bin_obj.temperature_c + self.rng.uniform(-0.2, 0.2), 1),
            sensor_battery_percent=round(new_battery, 1),
            sensor_status="CRITICAL" if new_fill >= 90.0 else "NORMAL",
            status_classification=classification,
            sequence_number=seq,
            health_status="TELEMETRY_HEALTHY",
            source="SIMULATED_BIN_SENSOR",
        )
        self._bin_states[bin_id] = updated_bin
        return updated_bin

    def get_all_bins(self) -> List[BinSensorTelemetry]:
        """Return the current states of all managed smart waste bins."""
        return list(self._bin_states.values())

    # Anomaly injection helpers for testing & benchmark scenarios
    def set_vehicle_deviation(self, vehicle_id: str, is_deviated: bool = True):
        if vehicle_id in self._vehicle_states:
            self._vehicle_states[vehicle_id]["is_deviated"] = is_deviated

    def set_vehicle_stale(self, vehicle_id: str, is_stale: bool = True):
        if vehicle_id in self._vehicle_states:
            self._vehicle_states[vehicle_id]["is_stale"] = is_stale

    def set_bin_fill_level(self, bin_id: str, fill_percent: float):
        if bin_id in self._bin_states:
            b = self._bin_states[bin_id]
            self._bin_states[bin_id] = BinSensorTelemetry(
                bin_id=bin_id,
                location_node=b.location_node,
                timestamp=datetime.utcnow(),
                fill_level_percent=round(fill_percent, 1),
                estimated_waste_kg=round(fill_percent * 10.0, 1),
                temperature_c=b.temperature_c,
                sensor_battery_percent=b.sensor_battery_percent,
                sensor_status="CRITICAL" if fill_percent >= 90.0 else "NORMAL",
                status_classification=classify_bin_fill_level(fill_percent),
                sequence_number=self._bin_seq.get(bin_id, 1) + 1,
                health_status="TELEMETRY_HEALTHY",
                source="SIMULATED_BIN_SENSOR",
            )
