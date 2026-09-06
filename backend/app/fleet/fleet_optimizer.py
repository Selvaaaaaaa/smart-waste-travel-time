"""Fleet optimization objectives and global multi-task scheduler."""
import logging
from typing import Dict, List, Any, Optional
from app.routing.graph import RoadNetworkGraph, get_default_network_graph
from app.fleet.fleet_state import FleetStateManager, fleet_state_manager
from app.fleet.task_allocator import TaskAllocator
from app.schemas.fleet import TaskAssignResponse

logger = logging.getLogger(__name__)


class FleetOptimizer:
    """
    Fleet-level optimization engine.
    
    Objective Function:
        Minimize:
            W1 * sum(Travel Time) +
            W2 * sum(Route Distance) +
            W3 * sum(Unassigned Waste Mass) +
            W4 * sum(Vehicle Utilization Imbalance Variance) +
            W5 * sum(Disruption Exposure)

        Subject to Hard Constraints:
            - Current Payload + Task Payload <= Rated Vehicle Gross Capacity
            - Current Driver Duration + Trip Duration <= Max Shift Minutes (480 min)
            - No vehicle may traverse closed/blocked road segments
            - Inactive / Broken vehicles receive zero assignments
    """

    def __init__(
        self,
        graph: Optional[RoadNetworkGraph] = None,
        state_mgr: Optional[FleetStateManager] = None,
    ):
        self.graph = graph or get_default_network_graph()
        self.state_mgr = state_mgr or fleet_state_manager
        self.allocator = TaskAllocator(self.graph, self.state_mgr)

    def optimize_fleet_batch(
        self,
        tasks: List[Dict[str, Any]],
        environmental_context: Optional[Dict[str, Any]] = None,
        strategy: str = "ADVANCED_OPTIMIZER",
    ) -> Dict[str, Any]:
        """
        Batch allocate tasks in order of priority (URGENT -> HIGH -> NORMAL -> LOW)
        to optimize total fleet efficiency and load distribution.
        """
        env_ctx = environmental_context or {}
        
        # Sort tasks by priority rank
        priority_weights = {"URGENT": 4, "HIGH": 3, "NORMAL": 2, "LOW": 1}
        sorted_tasks = sorted(
            tasks,
            key=lambda t: priority_weights.get(t.get("priority", "NORMAL"), 2),
            reverse=True,
        )

        results: List[TaskAssignResponse] = []
        assigned_count = 0
        deferred_count = 0
        total_eta = 0.0
        total_distance = 0.0
        total_waste_assigned = 0.0
        unsafe_prevented = 0

        for t in sorted_tasks:
            alloc_res = self.allocator.allocate_task(
                task_id=t["id"],
                location_node=t["location_node"],
                estimated_waste_kg=t["estimated_waste_kg"],
                priority=t.get("priority", "NORMAL"),
                request_type=t.get("request_type", "SCHEDULED_COLLECTION"),
                environmental_context=env_ctx,
                strategy=strategy,
            )
            results.append(alloc_res)
            for cand in alloc_res.candidate_evaluations:
                if not cand.is_safe:
                    unsafe_prevented += 1

            if alloc_res.status == "ASSIGNED":
                assigned_count += 1
                total_eta += alloc_res.predicted_eta_minutes or 0.0
                total_distance += self.graph.compute_path_distance(alloc_res.selected_route)
                total_waste_assigned += t["estimated_waste_kg"]
            else:
                deferred_count += 1

        summary = self.state_mgr.get_fleet_summary()
        wl_metrics = self.state_mgr.get_workload_metrics()

        return {
            "total_tasks": len(tasks),
            "assigned_count": assigned_count,
            "deferred_count": deferred_count,
            "assignment_success_rate": round(assigned_count / max(1, len(tasks)), 4),
            "total_waste_assigned_kg": total_waste_assigned,
            "avg_assigned_eta_min": round(total_eta / max(1, assigned_count), 2),
            "total_distance_km": round(total_distance, 2),
            "fleet_load_balance_score": wl_metrics["workload_balance_score"],
            "mean_utilization_pct": summary.mean_utilization_pct,
            "utilization_variance": summary.utilization_variance,
            "unsafe_assignments_prevented": unsafe_prevented,
            "strategy_used": strategy,
            "task_results": results,
        }

    def compare_allocation_strategies(
        self,
        tasks: List[Dict[str, Any]],
        environmental_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Compare BASELINE strategy against ADVANCED_OPTIMIZER across identical task sets.
        Baseline: Nearest/first feasible vehicle, no workload balancing or environmental scoring.
        Advanced Optimizer: Full 7-component multi-objective formulation with workload balance.
        """
        import copy
        from app.schemas.fleet import MetricComparison, AllocationComparisonResponse

        # Save current vehicles
        initial_state = [dict(v) for v in self.state_mgr.get_all_vehicles()]

        # 1. Run Baseline
        self.state_mgr.reset_fleet(copy.deepcopy(initial_state))
        baseline_res = self.optimize_fleet_batch(tasks, environmental_context, strategy="BASELINE")

        # 2. Run Advanced Optimizer
        self.state_mgr.reset_fleet(copy.deepcopy(initial_state))
        opt_res = self.optimize_fleet_batch(tasks, environmental_context, strategy="ADVANCED_OPTIMIZER")

        # Restore original fleet
        self.state_mgr.reset_fleet(initial_state)

        # Helper to compute metric comparison
        def make_comp(base_val: float, opt_val: float, unit: str, lower_is_better: bool = True) -> MetricComparison:
            diff = opt_val - base_val
            if base_val != 0.0:
                pct = ((base_val - opt_val) / abs(base_val) * 100.0) if lower_is_better else ((opt_val - base_val) / abs(base_val) * 100.0)
            else:
                pct = 0.0
            return MetricComparison(
                baseline_value=round(base_val, 2),
                optimized_value=round(opt_val, 2),
                absolute_difference=round(diff, 2),
                percentage_improvement=round(pct, 2),
                unit=unit,
            )

        eta_comp = make_comp(baseline_res["avg_assigned_eta_min"], opt_res["avg_assigned_eta_min"], "min", lower_is_better=True)
        dist_comp = make_comp(baseline_res["total_distance_km"], opt_res["total_distance_km"], "km", lower_is_better=True)
        util_comp = make_comp(baseline_res["mean_utilization_pct"], opt_res["mean_utilization_pct"], "%", lower_is_better=False)
        wl_comp = make_comp(baseline_res["fleet_load_balance_score"], opt_res["fleet_load_balance_score"], "score", lower_is_better=False)
        safety_comp = make_comp(baseline_res["unsafe_assignments_prevented"], opt_res["unsafe_assignments_prevented"], "prevented", lower_is_better=False)
        reassign_comp = make_comp(0.0, 0.0, "reassignments", lower_is_better=True)

        verdict = (
            f"ADVANCED_OPTIMIZER achieved a {wl_comp.percentage_improvement:.1f}% improvement in fleet workload balance "
            f"and {eta_comp.percentage_improvement:.1f}% improvement in average ETA compared to BASELINE allocator."
        )

        return AllocationComparisonResponse(
            strategy_evaluated="BASELINE_VS_ADVANCED_OPTIMIZER",
            task_count=len(tasks),
            eta_comparison=eta_comp,
            distance_comparison=dist_comp,
            utilization_comparison=util_comp,
            workload_balance_comparison=wl_comp,
            safety_violations_prevented_comparison=safety_comp,
            reassignment_count_comparison=reassign_comp,
            summary_verdict=verdict,
        ).model_dump()

