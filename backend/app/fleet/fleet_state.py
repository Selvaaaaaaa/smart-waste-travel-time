"""Fleet State Manager for multi-vehicle tracking, status transitions, and load balancing."""
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from app.schemas.fleet import VehicleFleetItem, FleetSummary, FleetStateResponse


DEFAULT_INITIAL_FLEET: List[Dict[str, Any]] = [
    {
        "vehicle_id": "V-01",
        "vehicle_code": "V-01",
        "vehicle_type": "COMPACTOR_HEAVY",
        "capacity_kg": 12000.0,
        "current_payload_kg": 2500.0,
        "current_location": "DEPOT_CENTRAL",
        "driver_id": "EMP-001",
        "driver_name": "Alex Mercer",
        "driver_shift_remaining_min": 270.0,
        "current_route": ["DEPOT_CENTRAL", "COLLECTION_ZONE_A", "COLLECTION_ZONE_B", "LANDFILL_MAIN"],
        "current_task_id": "TASK-INIT-01",
        "status": "ASSIGNED",
    },
    {
        "vehicle_id": "V-02",
        "vehicle_code": "V-02",
        "vehicle_type": "COMPACTOR_MEDIUM",
        "capacity_kg": 10000.0,
        "current_payload_kg": 1200.0,
        "current_location": "INTERSECTION_CENTRAL_1",
        "driver_id": "EMP-002",
        "driver_name": "Elena Vance",
        "driver_shift_remaining_min": 300.0,
        "current_route": ["INTERSECTION_CENTRAL_1", "COLLECTION_ZONE_E", "LANDFILL_MAIN"],
        "current_task_id": "TASK-INIT-02",
        "status": "EN_ROUTE",
    },
    {
        "vehicle_id": "V-03",
        "vehicle_code": "V-03",
        "vehicle_type": "COMPACTOR_HEAVY",
        "capacity_kg": 12000.0,
        "current_payload_kg": 0.0,
        "current_location": "DEPOT_CENTRAL",
        "driver_id": "EMP-004",
        "driver_name": "Sarah Chen",
        "driver_shift_remaining_min": 360.0,
        "current_route": [],
        "current_task_id": None,
        "status": "AVAILABLE",
    },
    {
        "vehicle_id": "V-04",
        "vehicle_code": "V-04",
        "vehicle_type": "COMPACTOR_LIGHT",
        "capacity_kg": 6000.0,
        "current_payload_kg": 500.0,
        "current_location": "DEPOT_CENTRAL",
        "driver_id": "EMP-007",
        "driver_name": "Priya Patel",
        "driver_shift_remaining_min": 340.0,
        "current_route": [],
        "current_task_id": None,
        "status": "AVAILABLE",
    },
    {
        "vehicle_id": "V-05",
        "vehicle_code": "V-05",
        "vehicle_type": "COMPACTOR_MEDIUM",
        "capacity_kg": 10000.0,
        "current_payload_kg": 0.0,
        "current_location": "TRANSFER_STATION_NORTH",
        "driver_id": "EMP-009",
        "driver_name": "Aisha Khan",
        "driver_shift_remaining_min": 390.0,
        "current_route": [],
        "current_task_id": None,
        "status": "AVAILABLE",
    },
    {
        "vehicle_id": "V-06",
        "vehicle_code": "V-06",
        "vehicle_type": "COMPACTOR_MEDIUM",
        "capacity_kg": 10000.0,
        "current_payload_kg": 8600.0,
        "current_location": "COLLECTION_ZONE_C",
        "driver_id": "EMP-008",
        "driver_name": "Liam Johnson",
        "driver_shift_remaining_min": 170.0,
        "current_route": ["COLLECTION_ZONE_C", "COLLECTION_ZONE_D", "LANDFILL_MAIN"],
        "current_task_id": "TASK-INIT-03",
        "status": "ASSIGNED",
    },
]


class FleetStateManager:
    """Manages operational multi-vehicle fleet state in memory with persistence capabilities."""

    def __init__(self, initial_vehicles: Optional[List[Dict[str, Any]]] = None):
        self.vehicles: Dict[str, Dict[str, Any]] = {}
        self.reset_fleet(initial_vehicles)

    def reset_fleet(self, custom_vehicles: Optional[List[Dict[str, Any]]] = None):
        """Reset fleet to known deterministic baseline."""
        fleet_data = custom_vehicles if custom_vehicles is not None else DEFAULT_INITIAL_FLEET
        self.vehicles.clear()
        for item in fleet_data:
            v_copy = dict(item)
            # Compute overload status
            v_copy["overload_status"] = self._compute_overload_status(
                v_copy["current_payload_kg"], v_copy["capacity_kg"]
            )
            v_copy["utilization_pct"] = round(
                (v_copy["current_payload_kg"] / max(1.0, v_copy["capacity_kg"])) * 100.0, 2
            )
            v_copy["estimated_available_time_min"] = (
                0.0 if v_copy["status"] == "AVAILABLE" else round(len(v_copy.get("current_route", [])) * 12.5, 1)
            )
            # Phase 8 workload tracking attributes
            v_copy.setdefault("assigned_tasks", [v_copy["current_task_id"]] if v_copy.get("current_task_id") else [])
            v_copy.setdefault("completed_tasks", [])
            v_copy.setdefault("estimated_workload_minutes", v_copy["estimated_available_time_min"])
            v_copy.setdefault("route_distance_km", round(len(v_copy.get("current_route", [])) * 3.8, 1))
            self.vehicles[v_copy["vehicle_id"]] = v_copy

    @staticmethod
    def _compute_overload_status(payload_kg: float, capacity_kg: float) -> str:
        ratio = payload_kg / max(1.0, capacity_kg)
        if ratio > 1.0:
            return "OVERLOADED"
        if ratio >= 0.95:
            return "CRITICAL"
        if ratio >= 0.80:
            return "WARNING"
        return "NORMAL"

    def get_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        return self.vehicles.get(vehicle_id)

    def get_all_vehicles(self) -> List[Dict[str, Any]]:
        return list(self.vehicles.values())

    def update_vehicle(self, vehicle_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        if vehicle_id not in self.vehicles:
            return None
        v = self.vehicles[vehicle_id]
        v.update(kwargs)
        # Recalculate derived attributes
        v["overload_status"] = self._compute_overload_status(v["current_payload_kg"], v["capacity_kg"])
        v["utilization_pct"] = round((v["current_payload_kg"] / max(1.0, v["capacity_kg"])) * 100.0, 2)
        if v["overload_status"] == "OVERLOADED" and v["status"] not in ["BREAKDOWN", "OFF_DUTY"]:
            v["status"] = "OVERLOADED"
        return v

    def trigger_breakdown(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        if vehicle_id not in self.vehicles:
            return None
        v = self.vehicles[vehicle_id]
        v["status"] = "BREAKDOWN"
        return v

    def recover_vehicle(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        if vehicle_id not in self.vehicles:
            return None
        v = self.vehicles[vehicle_id]
        v["status"] = "AVAILABLE"
        v["current_route"] = []
        v["current_task_id"] = None
        return v

    def get_workload_metrics(self) -> Dict[str, Any]:
        """Compute fleet workload average, per-vehicle deviations, and workload balance score."""
        vehicles_list = list(self.vehicles.values())
        if not vehicles_list:
            return {
                "mean_workload_min": 0.0,
                "workload_std_dev": 0.0,
                "workload_balance_score": 1.0,
                "vehicle_workloads": {},
                "vehicle_deviations": {},
            }

        workloads = {v["vehicle_id"]: float(v.get("estimated_workload_minutes", 0.0)) for v in vehicles_list}
        vals = list(workloads.values())
        mean_wl = float(np.mean(vals)) if vals else 0.0
        std_wl = float(np.std(vals)) if vals else 0.0
        # Workload balance metric: 1 - normalized_deviation_from_fleet_average
        norm_dev = min(1.0, max(0.0, std_wl / 240.0))
        balance_score = round(max(0.0, min(1.0, 1.0 - norm_dev)), 4)

        deviations = {v_id: round(wl - mean_wl, 2) for v_id, wl in workloads.items()}

        return {
            "mean_workload_min": round(mean_wl, 2),
            "workload_std_dev": round(std_wl, 2),
            "workload_balance_score": balance_score,
            "vehicle_workloads": workloads,
            "vehicle_deviations": deviations,
        }

    def get_fleet_load_balance_score(self) -> float:
        """Return the fleet-wide workload balance score (0.0 to 1.0)."""
        return self.get_workload_metrics()["workload_balance_score"]

    def get_fleet_summary(self) -> FleetSummary:
        vehicles_list = list(self.vehicles.values())
        total = len(vehicles_list)
        available = sum(1 for v in vehicles_list if v["status"] == "AVAILABLE")
        assigned = sum(1 for v in vehicles_list if v["status"] == "ASSIGNED")
        en_route = sum(1 for v in vehicles_list if v["status"] == "EN_ROUTE")
        overloaded = sum(1 for v in vehicles_list if v["overload_status"] == "OVERLOADED" or v["status"] == "OVERLOADED")
        breakdown = sum(1 for v in vehicles_list if v["status"] == "BREAKDOWN")
        off_duty = sum(1 for v in vehicles_list if v["status"] == "OFF_DUTY")

        utilizations = [v["utilization_pct"] for v in vehicles_list]
        mean_util = float(np.mean(utilizations)) if utilizations else 0.0
        util_var = float(np.var(utilizations)) if utilizations else 0.0

        wl_metrics = self.get_workload_metrics()

        return FleetSummary(
            total_vehicles=total,
            available=available,
            assigned=assigned,
            en_route=en_route,
            overloaded=overloaded,
            breakdown=breakdown,
            off_duty=off_duty,
            mean_utilization_pct=round(mean_util, 2),
            utilization_variance=round(util_var, 2),
            load_balance_score=wl_metrics["workload_balance_score"],
        )

    def get_fleet_state_response(self, active_tasks_count: int = 0, pending_tasks_count: int = 0) -> FleetStateResponse:
        summary = self.get_fleet_summary()
        wl_metrics = self.get_workload_metrics()
        vehicle_items: List[VehicleFleetItem] = []

        for v in self.vehicles.values():
            safety = "SAFE"
            if v["status"] == "BREAKDOWN":
                safety = "UNSAFE: BREAKDOWN"
            elif v["overload_status"] == "OVERLOADED":
                safety = "UNSAFE: OVERLOADED"
            elif v["driver_shift_remaining_min"] <= 30.0:
                safety = "WARNING: SHIFT FATIGUE"

            v_id = v["vehicle_id"]
            assigned_tsks = v.get("assigned_tasks", [v["current_task_id"]] if v.get("current_task_id") else [])
            completed_tsks = v.get("completed_tasks", [])
            pending_cnt = len(assigned_tsks)
            workload_min = float(v.get("estimated_workload_minutes", v.get("estimated_available_time_min", 0.0)))
            route_dist = float(v.get("route_distance_km", len(v.get("current_route", [])) * 3.8))
            dev_min = wl_metrics["vehicle_deviations"].get(v_id, 0.0)

            vehicle_items.append(
                VehicleFleetItem(
                    vehicle_id=v["vehicle_id"],
                    vehicle_code=v["vehicle_code"],
                    vehicle_type=v["vehicle_type"],
                    capacity_kg=v["capacity_kg"],
                    current_payload_kg=v["current_payload_kg"],
                    current_location=v["current_location"],
                    driver_id=v.get("driver_id"),
                    driver_name=v.get("driver_name"),
                    driver_shift_remaining_min=v["driver_shift_remaining_min"],
                    current_route=v.get("current_route", []),
                    current_task_id=v.get("current_task_id"),
                    status=v["status"],
                    overload_status=v["overload_status"],
                    utilization_pct=v["utilization_pct"],
                    safety_status=safety,
                    estimated_available_time_min=v["estimated_available_time_min"],
                    assigned_tasks_count=len(assigned_tsks) + len(completed_tsks),
                    completed_tasks_count=len(completed_tsks),
                    pending_tasks_count=pending_cnt,
                    estimated_workload_minutes=round(workload_min, 1),
                    route_distance_km=round(route_dist, 2),
                    workload_deviation_minutes=round(dev_min, 1),
                )
            )

        return FleetStateResponse(
            summary=summary,
            vehicles=vehicle_items,
            active_tasks_count=active_tasks_count,
            pending_tasks_count=pending_tasks_count,
            timestamp=datetime.utcnow(),
        )


# Singleton instance for consistent in-process application state
fleet_state_manager = FleetStateManager()
