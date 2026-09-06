"""Phase 7 Multi-Vehicle Fleet Coordination & Dynamic Task Allocation Package."""
from app.fleet.fleet_state import FleetStateManager, fleet_state_manager
from app.fleet.fleet_scoring import calculate_allocation_score, evaluate_vehicle_safety_gate
from app.fleet.task_insertion import DynamicTaskInserter
from app.fleet.task_allocator import TaskAllocator
from app.fleet.fleet_rebalancer import FleetRebalancer
from app.fleet.fleet_optimizer import FleetOptimizer
from app.fleet.fleet_experiments import FleetExperimentRunner
from app.fleet.fleet_service import FleetService, fleet_service

__all__ = [
    "FleetStateManager",
    "fleet_state_manager",
    "calculate_allocation_score",
    "evaluate_vehicle_safety_gate",
    "DynamicTaskInserter",
    "TaskAllocator",
    "FleetRebalancer",
    "FleetOptimizer",
    "FleetExperimentRunner",
    "FleetService",
    "fleet_service",
]
