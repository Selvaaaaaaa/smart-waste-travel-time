"""Multi-Depot Management Service for Municipal Scalability.

Supports single-depot backward compatibility and multi-depot fleet partitioning.
"""
from typing import Dict, List, Optional
from app.schemas.telemetry import DepotInfo
from app.telemetry.generator import haversine_distance_meters


class MultiDepotService:
    """Manages municipal fleet dispatch depots and regional vehicle allocations."""

    def __init__(self):
        self._depots: Dict[str, DepotInfo] = {
            "DEPOT_CENTRAL": DepotInfo(
                depot_id="DEPOT_CENTRAL",
                name="Central Municipal Fleet Depot",
                latitude=40.7128,
                longitude=-74.0060,
                node_id="DEPOT_CENTRAL",
                active=True,
                assigned_vehicles_count=4,
                capacity_vehicles=25,
            ),
            "DEPOT_NORTH": DepotInfo(
                depot_id="DEPOT_NORTH",
                name="North Metro Transfer Depot",
                latitude=40.7750,
                longitude=-73.9550,
                node_id="TRANSFER_STATION_NORTH",
                active=True,
                assigned_vehicles_count=1,
                capacity_vehicles=15,
            ),
            "DEPOT_SOUTH": DepotInfo(
                depot_id="DEPOT_SOUTH",
                name="South Harbor Fleet Terminal",
                latitude=40.7000,
                longitude=-74.0150,
                node_id="TRANSFER_STATION_SOUTH",
                active=True,
                assigned_vehicles_count=1,
                capacity_vehicles=15,
            ),
        }

        # Vehicle to depot mapping: vehicle_id -> depot_id
        self._vehicle_depot_assignments: Dict[str, str] = {
            "V-01": "DEPOT_CENTRAL",
            "V-02": "DEPOT_CENTRAL",
            "V-03": "DEPOT_CENTRAL",
            "V-04": "DEPOT_CENTRAL",
            "V-05": "DEPOT_NORTH",
            "V-06": "DEPOT_SOUTH",
        }

    def get_all_depots(self) -> List[DepotInfo]:
        """Return list of all registered municipal depots."""
        # Refresh dynamic counts
        counts: Dict[str, int] = {}
        for d_id in self._vehicle_depot_assignments.values():
            counts[d_id] = counts.get(d_id, 0) + 1

        for d_id, dep in self._depots.items():
            dep.assigned_vehicles_count = counts.get(d_id, 0)

        return list(self._depots.values())

    def get_depot(self, depot_id: str) -> Optional[DepotInfo]:
        return self._depots.get(depot_id)

    def assign_vehicle_to_depot(self, vehicle_id: str, depot_id: str) -> bool:
        if depot_id not in self._depots:
            return False
        self._vehicle_depot_assignments[vehicle_id] = depot_id
        return True

    def get_vehicle_depot(self, vehicle_id: str) -> str:
        return self._vehicle_depot_assignments.get(vehicle_id, "DEPOT_CENTRAL")

    def find_nearest_depot(self, lat: float, lng: float) -> DepotInfo:
        """Find the geographically closest active depot to a given coordinate."""
        closest_depot = self._depots["DEPOT_CENTRAL"]
        min_dist = float("inf")

        for dep in self._depots.values():
            if not dep.active:
                continue
            dist = haversine_distance_meters(lat, lng, dep.latitude, dep.longitude)
            if dist < min_dist:
                min_dist = dist
                closest_depot = dep

        return closest_depot


# Global singleton instance
depot_service = MultiDepotService()
