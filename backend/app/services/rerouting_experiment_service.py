"""Phase 6 Empirical Experiment Service: Static Baseline vs Dynamic Rerouting Engine.

Runs evaluations across 7 scenarios and 5 random seeds (42, 43, 44, 45, 46) to quantify:
- Travel time savings (min & %)
- Distance trade-offs
- Safety violations prevented (capacity & fatigue)
- Disruption adaptation efficiency

Research Disclaimer:
This is a deterministic simulation and research prototype.
It does not represent live municipal routing or live GPS data.
"""
import random
import numpy as np
from typing import Dict, List, Any
from app.routing.graph import get_default_network_graph
from app.routing.rerouting import DynamicReroutingEngine


SCENARIOS = [
    "NORMAL",
    "HEAVY_RAIN",
    "MAJOR_EVENT",
    "ROAD_CLOSURE",
    "HIGH_WASTE",
    "COMBINED_DISRUPTION",
    "ACCIDENT_BLOCKAGE",
]

SEEDS = [42, 43, 44, 45, 46]


class ReroutingExperimentService:
    """Executes deterministic benchmark comparisons of Static Baseline vs Dynamic Rerouting."""

    def run_single_simulation(self, scenario_name: str, seed: int) -> Dict[str, Any]:
        random.seed(seed)
        np.random.seed(seed)

        # Build fresh network graph
        graph = get_default_network_graph()
        engine = DynamicReroutingEngine(graph)

        origin = "DEPOT_CENTRAL"
        stops = ["COLLECTION_ZONE_A", "COLLECTION_ZONE_B", "COLLECTION_ZONE_C"]
        destination = "LANDFILL_MAIN"
        vehicle_capacity = 8000.0  # kg
        initial_payload = 1000.0  # kg
        max_shift_hours = 4.0  # 240 min limit

        # Initial planned static path
        static_waypoints = [origin] + stops + [destination]
        planned_path = engine.candidate_generator.generate_path_for_waypoints(static_waypoints, weight_mode="time") or static_waypoints

        # Apply Scenario Environmental Disruptions
        env_context: Dict[str, Any] = {
            "weather_condition": "CLEAR",
            "rainfall_mm": 0.0,
            "visibility_km": 10.0,
            "traffic_level": "LOW",
            "congestion_index": 15.0,
            "event_level": "NONE",
            "road_restriction_type": "NONE",
        }
        extra_waste_kg = 0.0
        blocked_segment = None

        if scenario_name == "NORMAL":
            pass  # Nominal baseline conditions

        elif scenario_name == "HEAVY_RAIN":
            env_context.update({"weather_condition": "HEAVY_RAIN", "rainfall_mm": 35.0, "visibility_km": 4.0})
            for u, v in graph.edges:
                graph.set_edge_weather_penalty(u, v, factor=1.75, bidirectional=False)

        elif scenario_name == "MAJOR_EVENT":
            env_context.update({"event_level": "CITY_FESTIVAL", "traffic_level": "HIGH", "congestion_index": 65.0})
            graph.set_edge_congestion("COLLECTION_ZONE_B", "COLLECTION_ZONE_C", factor=3.5)
            graph.set_edge_congestion("INTERSECTION_CENTRAL_2", "COLLECTION_ZONE_C", factor=3.0)

        elif scenario_name == "ROAD_CLOSURE":
            env_context.update({"road_restriction_type": "EMERGENCY_REPAIR", "traffic_level": "HIGH"})
            blocked_segment = ("COLLECTION_ZONE_B", "COLLECTION_ZONE_C")
            graph.set_edge_blocked(blocked_segment[0], blocked_segment[1], is_blocked=True)

        elif scenario_name == "HIGH_WASTE":
            extra_waste_kg = 3500.0  # Pushes static path near/over limit
            env_context.update({"waste_volume_tons": 7.5})

        elif scenario_name == "COMBINED_DISRUPTION":
            env_context.update({
                "weather_condition": "HEAVY_RAIN",
                "rainfall_mm": 40.0,
                "event_level": "STADIUM_CONCERT",
                "road_restriction_type": "PARTIAL_CLOSURE",
                "traffic_level": "SEVERE",
                "congestion_index": 85.0,
            })
            for u, v in graph.edges:
                graph.set_edge_weather_penalty(u, v, factor=1.8, bidirectional=False)
            blocked_segment = ("COLLECTION_ZONE_C", "COLLECTION_ZONE_D")
            graph.set_edge_blocked(blocked_segment[0], blocked_segment[1], is_blocked=True)
            graph.set_edge_congestion("COLLECTION_ZONE_B", "INTERSECTION_CENTRAL_2", factor=3.2)
            extra_waste_kg = 1500.0

        elif scenario_name == "ACCIDENT_BLOCKAGE":
            blocked_segment = ("INTERSECTION_CENTRAL_1", "COLLECTION_ZONE_B")
            graph.set_edge_blocked(blocked_segment[0], blocked_segment[1], is_blocked=True)
            graph.set_edge_congestion("COLLECTION_ZONE_A", "COLLECTION_ZONE_B", factor=3.8)

        # -------------------------------------------------------------
        # 1. EVALUATE STATIC BASELINE (No rerouting during disruption)
        # -------------------------------------------------------------
        static_distance = graph.compute_path_distance(planned_path)
        static_time = 0.0
        static_safe = True
        static_violations = 0

        # Traverse planned path step-by-step
        for i in range(len(planned_path) - 1):
            u, v = planned_path[i], planned_path[i + 1]
            e = graph.get_edge(u, v)
            if e and e.get("is_blocked", False):
                # Static vehicle gets delayed waiting / attempting detour with massive penalty
                static_time += 45.0  # 45 min stuck delay
                static_violations += 1
                static_safe = False
            else:
                cost = graph.compute_edge_cost(u, v, weight_mode="time")
                static_time += cost if cost != float("inf") else 20.0

        total_static_waste = initial_payload + (len(stops) * 1200.0) + extra_waste_kg
        if total_static_waste > vehicle_capacity:
            static_safe = False
            static_violations += 1

        if static_time > (max_shift_hours * 60.0):
            static_safe = False
            static_violations += 1

        # Add base noise according to seed
        noise = (seed % 5 - 2) * 0.5
        static_time = max(10.0, static_time + noise)

        # -------------------------------------------------------------
        # 2. EVALUATE DYNAMIC REROUTING ENGINE (Adaptive Hybrid + Safety)
        # -------------------------------------------------------------
        # Start at origin
        reroute_result = engine.evaluate_and_reroute(
            current_node=origin,
            remaining_stops=stops,
            destination_node=destination,
            current_path=planned_path,
            current_payload_kg=initial_payload + extra_waste_kg,
            vehicle_capacity_kg=vehicle_capacity,
            expected_remaining_waste_kg=len(stops) * 1200.0,
            elapsed_time_minutes=0.0,
            max_shift_hours=max_shift_hours,
            trigger_type=f"SCENARIO_{scenario_name}",
            base_context=env_context,
        )

        selected = reroute_result["selected_candidate"]
        if selected:
            dyn_path = selected["path"]
            dyn_dist = selected["total_distance_km"]
            dyn_time = 0.0
            for i in range(len(dyn_path) - 1):
                u, v = dyn_path[i], dyn_path[i + 1]
                c = graph.compute_edge_cost(u, v, weight_mode="time")
                dyn_time += c if c != float("inf") else 15.0
            dyn_time = max(8.0, dyn_time + noise * 0.3)
            dyn_safe = selected["safety_valid"]
        else:
            dyn_path = planned_path
            dyn_dist = static_distance
            dyn_time = static_time
            dyn_safe = static_safe

        # Calculate comparative metrics
        time_saved = max(0.0, round(static_time - dyn_time, 2))
        pct_saved = round((time_saved / max(static_time, 1.0)) * 100, 2)
        dist_diff = round(dyn_dist - static_distance, 2)
        violations_prevented = static_violations if dyn_safe else 0

        return {
            "scenario_name": scenario_name,
            "seed": seed,
            "static_baseline_travel_time_min": round(static_time, 2),
            "static_baseline_distance_km": round(static_distance, 2),
            "static_baseline_success": static_safe,
            "dynamic_rerouted_travel_time_min": round(dyn_time, 2),
            "dynamic_rerouted_distance_km": round(dyn_dist, 2),
            "dynamic_rerouted_success": dyn_safe,
            "time_saved_minutes": time_saved,
            "pct_time_saved": pct_saved,
            "distance_penalty_km": dist_diff,
            "reroute_count": 1 if reroute_result["reroute_executed"] else 0,
            "safety_violations_prevented": violations_prevented,
            "decision_rationale": reroute_result["decision_rationale"],
        }

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Execute 7 scenarios * 5 seeds = 35 total simulation runs and aggregate results."""
        all_results: List[Dict[str, Any]] = []
        scenario_groups: Dict[str, List[Dict[str, Any]]] = {s: [] for s in SCENARIOS}

        for scen in SCENARIOS:
            for seed in SEEDS:
                res = self.run_single_simulation(scen, seed)
                all_results.append(res)
                scenario_groups[scen].append(res)

        # Compute scenario aggregated averages
        scenario_breakdown: Dict[str, Dict[str, Any]] = {}
        for scen, items in scenario_groups.items():
            mean_static_time = np.mean([x["static_baseline_travel_time_min"] for x in items])
            mean_dyn_time = np.mean([x["dynamic_rerouted_travel_time_min"] for x in items])
            mean_saved = np.mean([x["time_saved_minutes"] for x in items])
            mean_pct = np.mean([x["pct_time_saved"] for x in items])
            mean_dist_diff = np.mean([x["distance_penalty_km"] for x in items])
            static_safety_rate = np.mean([100.0 if x["static_baseline_success"] else 0.0 for x in items])
            dyn_safety_rate = np.mean([100.0 if x["dynamic_rerouted_success"] else 0.0 for x in items])
            total_violations_prev = sum([x["safety_violations_prevented"] for x in items])

            scenario_breakdown[scen] = {
                "mean_static_time_min": round(float(mean_static_time), 2),
                "mean_dynamic_time_min": round(float(mean_dyn_time), 2),
                "mean_time_saved_min": round(float(mean_saved), 2),
                "mean_pct_time_saved": round(float(mean_pct), 2),
                "mean_distance_penalty_km": round(float(mean_dist_diff), 2),
                "static_safety_rate_pct": round(float(static_safety_rate), 1),
                "dynamic_safety_rate_pct": round(float(dyn_safety_rate), 1),
                "total_violations_prevented": total_violations_prev,
            }

        overall_time_saved = float(np.mean([x["time_saved_minutes"] for x in all_results]))
        overall_pct_saved = float(np.mean([x["pct_time_saved"] for x in all_results]))
        overall_static_safe = float(np.mean([100.0 if x["static_baseline_success"] else 0.0 for x in all_results]))
        overall_dyn_safe = float(np.mean([100.0 if x["dynamic_rerouted_success"] else 0.0 for x in all_results]))

        return {
            "total_runs": len(all_results),
            "scenarios_evaluated": SCENARIOS,
            "mean_time_saved_min": round(overall_time_saved, 2),
            "mean_pct_time_saved": round(overall_pct_saved, 2),
            "overall_safety_rate_static_pct": round(overall_static_safe, 1),
            "overall_safety_rate_dynamic_pct": round(overall_dyn_safe, 1),
            "disruption_adaptation_effectiveness_pct": round(
                float(np.mean([
                    x["pct_time_saved"]
                    for x in all_results
                    if x["scenario_name"] in ["ROAD_CLOSURE", "COMBINED_DISRUPTION", "ACCIDENT_BLOCKAGE", "MAJOR_EVENT"]
                ])),
                2,
            ),
            "scenario_breakdown": scenario_breakdown,
            "detailed_runs": all_results,
            "disclaimer": (
                "SIMULATION DISCLAIMER: This is a deterministic simulation and research prototype. "
                "It does not represent live municipal routing or live GPS data."
            ),
        }
