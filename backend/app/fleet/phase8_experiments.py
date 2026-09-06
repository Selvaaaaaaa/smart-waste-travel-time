"""Phase 8 Controlled Benchmark Suite: 10 Scenarios x 5 Deterministic Seeds = 50 Benchmark Runs.

Scenarios:
1. NORMAL_OPERATIONS
2. HEAVY_TRAFFIC
3. HEAVY_RAIN
4. ROAD_CLOSURE
5. MAJOR_EVENT
6. HIGH_WASTE_VOLUME
7. VEHICLE_BREAKDOWN
8. EMERGENCY_REQUEST
9. WORKLOAD_IMBALANCE
10. COMBINED_STRESS

Deterministic Seeds: 42, 43, 44, 45, 46
"""
import time
import numpy as np
from typing import Dict, List, Any, Optional
from app.fleet.end_to_end_simulator import EndToEndFleetSimulator
from app.schemas.fleet import (
    Phase8BenchmarkRunResult,
    ScenarioStatisticalSummary,
    Phase8ExperimentSummaryResponse,
    FailureDiagnosticItem,
)

PHASE8_SCENARIOS = [
    "NORMAL_OPERATIONS",
    "HEAVY_TRAFFIC",
    "HEAVY_RAIN",
    "ROAD_CLOSURE",
    "MAJOR_EVENT",
    "HIGH_WASTE_VOLUME",
    "VEHICLE_BREAKDOWN",
    "EMERGENCY_REQUEST",
    "WORKLOAD_IMBALANCE",
    "COMBINED_STRESS",
]

PHASE8_SEEDS = [42, 43, 44, 45, 46]


class Phase8ExperimentRunner:
    """Executes the 50 empirical benchmark runs across 10 scenarios and computes statistical summaries."""

    def __init__(self):
        self._cached_results: Optional[Phase8ExperimentSummaryResponse] = None

    def run_benchmark_suite(self, force_fresh: bool = False) -> Phase8ExperimentSummaryResponse:
        """Execute all 10 scenarios x 5 seeds = 50 runs and compute statistical aggregations."""
        if self._cached_results and not force_fresh:
            return self._cached_results

        t_start = time.perf_counter()
        detailed_runs: List[Phase8BenchmarkRunResult] = []
        failure_log: List[FailureDiagnosticItem] = []
        scenario_grouped_runs: Dict[str, List[Phase8BenchmarkRunResult]] = {sc: [] for sc in PHASE8_SCENARIOS}

        failure_counts: Dict[str, int] = {
            "PAYLOAD_CAPACITY_EXCEEDED": 0,
            "DRIVER_SHIFT_EXCEEDED": 0,
            "ROAD_SEGMENT_IMPASSABLE": 0,
            "VEHICLE_UNAVAILABLE": 0,
            "VEHICLE_BREAKDOWN": 0,
            "NO_FEASIBLE_VEHICLE": 0,
            "NO_FEASIBLE_INSERTION": 0,
            "EMERGENCY_REQUEST_DELAY": 0,
            "WORKLOAD_IMBALANCE": 0,
            "ETA_DEGRADATION": 0,
            "ROUTE_OPTIMIZATION_FAILURE": 0,
        }

        total_rejected = 0
        total_unsafe_prevented = 0
        total_payload_prev = 0
        total_shift_prev = 0
        total_blocked_prev = 0

        for sc in PHASE8_SCENARIOS:
            for seed in PHASE8_SEEDS:
                sim = EndToEndFleetSimulator(seed=seed)
                res = sim.run_simulation(scenario_name=sc)
                run_metrics = res.metrics
                detailed_runs.append(run_metrics)
                scenario_grouped_runs[sc].append(run_metrics)

                total_rejected += run_metrics.unsafe_candidates_rejected
                total_unsafe_prevented += run_metrics.unsafe_assignments_prevented
                total_payload_prev += run_metrics.payload_violations_prevented
                total_shift_prev += run_metrics.shift_violations_prevented
                total_blocked_prev += run_metrics.blocked_road_violations_prevented

                if run_metrics.primary_failure_category:
                    cat = run_metrics.primary_failure_category
                    if cat in failure_counts:
                        failure_counts[cat] += 1
                    else:
                        failure_counts["ROUTE_OPTIMIZATION_FAILURE"] += 1

                    failure_log.append(
                        FailureDiagnosticItem(
                            scenario=sc,
                            seed=seed,
                            task_id=f"RUN-{sc}-S{seed}",
                            vehicle_id=None,
                            failure_category=cat,
                            failure_reason=f"Primary operational disruption triggered: {cat}",
                            recovery_action="DYNAMIC_FLEET_REBALANCING_OR_DEFERRAL",
                            final_status="MITIGATED" if run_metrics.safe_assignment_rate == 1.0 else "UNSAFE",
                        )
                    )

        # Compute scenario-wise statistical summaries
        scenario_stats: Dict[str, ScenarioStatisticalSummary] = {}
        all_baseline_scores = []
        all_opt_scores = []

        for sc, runs in scenario_grouped_runs.items():
            etas = [r.avg_eta_min for r in runs]
            dists = [r.avg_distance_km for r in runs]
            scores = [r.optimized_allocation_score for r in runs]
            wls = [r.workload_balance_metric for r in runs]
            rec_times = [r.avg_recovery_time_min for r in runs if r.avg_recovery_time_min > 0]
            if not rec_times:
                rec_times = [0.0]

            b_scores = [r.baseline_allocation_score for r in runs]
            all_baseline_scores.extend(b_scores)
            all_opt_scores.extend(scores)

            mean_b = float(np.mean(b_scores))
            mean_o = float(np.mean(scores))
            pct_imp = round(((mean_b - mean_o) / max(0.0001, mean_b)) * 100.0, 2)

            scenario_stats[sc] = ScenarioStatisticalSummary(
                scenario_name=sc,
                num_runs=len(runs),
                eta_mean=round(float(np.mean(etas)), 2),
                eta_median=round(float(np.median(etas)), 2),
                eta_min=round(float(np.min(etas)), 2),
                eta_max=round(float(np.max(etas)), 2),
                eta_std=round(float(np.std(etas)), 2),
                distance_mean=round(float(np.mean(dists)), 2),
                distance_median=round(float(np.median(dists)), 2),
                distance_min=round(float(np.min(dists)), 2),
                distance_max=round(float(np.max(dists)), 2),
                distance_std=round(float(np.std(dists)), 2),
                score_mean=round(mean_o, 4),
                score_median=round(float(np.median(scores)), 4),
                score_min=round(float(np.min(scores)), 4),
                score_max=round(float(np.max(scores)), 4),
                score_std=round(float(np.std(scores)), 4),
                workload_balance_mean=round(float(np.mean(wls)), 4),
                workload_balance_median=round(float(np.median(wls)), 4),
                workload_balance_min=round(float(np.min(wls)), 4),
                workload_balance_max=round(float(np.max(wls)), 4),
                workload_balance_std=round(float(np.std(wls)), 4),
                recovery_time_mean=round(float(np.mean(rec_times)), 2),
                recovery_time_std=round(float(np.std(rec_times)), 2),
                pct_improvement_over_baseline=pct_imp,
            )

        # Fleet-wide aggregate rates
        overall_assign_success = float(np.mean([r.assignment_success_rate for r in detailed_runs])) * 100.0
        overall_safe_rate = float(np.mean([r.safe_assignment_rate for r in detailed_runs])) * 100.0
        overall_emg_rate = float(np.mean([r.emergency_fulfillment_rate for r in detailed_runs])) * 100.0
        overall_rec_rate = float(np.mean([r.breakdown_recovery_rate for r in detailed_runs])) * 100.0
        overall_mean_wl = float(np.mean([r.workload_balance_metric for r in detailed_runs]))
        overall_mean_util = float(np.mean([r.vehicle_utilization_mean_pct for r in detailed_runs]))

        overall_base_mean = float(np.mean(all_baseline_scores))
        overall_opt_mean = float(np.mean(all_opt_scores))
        overall_imp_pct = round(((overall_base_mean - overall_opt_mean) / max(0.0001, overall_base_mean)) * 100.0, 2)

        exec_sec = round(time.perf_counter() - t_start, 3)

        summary_response = Phase8ExperimentSummaryResponse(
            total_runs=len(detailed_runs),
            scenarios_evaluated=PHASE8_SCENARIOS,
            seeds_evaluated=PHASE8_SEEDS,
            overall_assignment_success_rate_pct=round(overall_assign_success, 2),
            overall_safe_assignment_rate_pct=round(overall_safe_rate, 2),
            overall_emergency_fulfillment_rate_pct=round(overall_emg_rate, 2),
            overall_breakdown_recovery_rate_pct=round(overall_rec_rate, 2),
            overall_mean_workload_balance=round(overall_mean_wl, 4),
            overall_mean_utilization_pct=round(overall_mean_util, 2),
            total_unsafe_candidates_rejected=total_rejected,
            total_unsafe_assignments_prevented=total_unsafe_prevented,
            total_payload_violations_prevented=total_payload_prev,
            total_shift_violations_prevented=total_shift_prev,
            total_blocked_road_violations_prevented=total_blocked_prev,
            mean_baseline_score=round(overall_base_mean, 4),
            mean_optimized_score=round(overall_opt_mean, 4),
            overall_optimization_improvement_pct=overall_imp_pct,
            scenario_statistics=scenario_stats,
            failure_distribution=failure_counts,
            failure_diagnostic_log=failure_log,
            detailed_runs=detailed_runs,
            benchmark_execution_time_seconds=exec_sec,
        )

        self._cached_results = summary_response
        return summary_response


# Global singleton runner
phase8_experiment_runner = Phase8ExperimentRunner()
