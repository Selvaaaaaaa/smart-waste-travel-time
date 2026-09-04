import logging
import datetime
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult
from app.models.scenario import Scenario
from app.models.route import Route
from app.services.scenario_engine import ScenarioEngine, STANDARD_SCENARIOS
from app.services.failure_analysis import analyze_failures, get_top_worst_errors
from app.ml.hybrid import predict_hybrid_eta
from app.ml.evaluate import calculate_metrics

logger = logging.getLogger(__name__)

# Standard controlled repetition seeds for scientific reproducibility
STANDARD_SEEDS = [42, 43, 44, 45, 46, 47, 48, 49, 50, 51]


class ExperimentService:
    """
    Rigorously executes repeated scenario experiments, compares Baseline vs
    Context-Aware vs Adaptive Hybrid models, and captures failure cases.
    """

    @staticmethod
    def run_scenario_experiment(
        scenario_key: str,
        db: Session,
        repetitions: int = 5,
        custom_params: Optional[Dict[str, Any]] = None,
        persist_to_db: bool = True,
        include_hybrid: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute an experiment for a single scenario with controlled deterministic repetitions.
        Evaluates Baseline, Context-Aware, and Adaptive Hybrid models concurrently.
        """
        scenario_key = scenario_key.upper()
        if scenario_key not in STANDARD_SCENARIOS and scenario_key != "CUSTOM":
            raise ValueError(f"Unknown scenario key: {scenario_key}")

        seeds = STANDARD_SEEDS[:max(repetitions, 1)]
        if len(seeds) < repetitions:
            seeds = [42 + i for i in range(repetitions)]

        # Fetch routes from DB for testing diverse topologies
        routes = db.query(Route).all()
        route_configs = []
        if routes:
            for r in routes:
                route_configs.append({
                    "route_id": r.route_code or f"R-{r.id}",
                    "distance_km": float(r.total_distance_km) if r.total_distance_km else 20.0,
                    "waste_volume_tons": float(r.total_waste_tons) if r.total_waste_tons else 5.0,
                    "assigned_vehicle_id": r.vehicle_id,
                    "assigned_driver_id": r.driver_id,
                })
        else:
            route_configs = [
                {"route_id": "R-101", "distance_km": 14.5, "waste_volume_tons": 4.2},
                {"route_id": "R-102", "distance_km": 22.0, "waste_volume_tons": 5.8},
                {"route_id": "R-103", "distance_km": 28.5, "waste_volume_tons": 6.5},
                {"route_id": "R-104", "distance_km": 35.0, "waste_volume_tons": 7.2},
                {"route_id": "R-105", "distance_km": 42.0, "waste_volume_tons": 8.0},
            ]

        runs = []
        safe_runs_count = 0
        unsafe_runs_count = 0
        capacity_violations = 0
        workload_violations = 0
        baseline_selected_count = 0
        context_selected_count = 0

        for seed_idx, seed in enumerate(seeds):
            engine = ScenarioEngine(random_seed=seed)
            # Cycle through available route configurations
            rc = route_configs[seed_idx % len(route_configs)]

            run_params = {
                "scenario_key": scenario_key,
                "distance_km": rc["distance_km"],
                "waste_volume_tons": rc["waste_volume_tons"],
            }
            if custom_params:
                run_params.update({k: v for k, v in custom_params.items() if v is not None})

            sim_res = engine.run_scenario(
                scenario_key_or_params=run_params,
                db=db,
                vehicle_id=rc.get("assigned_vehicle_id"),
                driver_id=rc.get("assigned_driver_id"),
                persist_predictions=False,
            )

            is_safe = sim_res.get("is_safe", True)
            if is_safe:
                safe_runs_count += 1
            else:
                unsafe_runs_count += 1
                v_type = sim_res.get("constraint_violation", {}).get("type", "")
                if "CAPACITY" in v_type or "PAYLOAD" in v_type:
                    capacity_violations += 1
                elif "WORKLOAD" in v_type or "FATIGUE" in v_type or "SHIFT" in v_type:
                    workload_violations += 1

            # Adaptive Hybrid Prediction (Only evaluated if safe)
            hybrid_eta = None
            selected_model = None
            selection_reason = None
            prediction_spread = None
            hybrid_error = None

            if is_safe and include_hybrid:
                hybrid_out = predict_hybrid_eta(sim_res.get("parameters", run_params))
                selected_model = hybrid_out["selected_model"]
                selection_reason = hybrid_out["selection_reason"]
                hybrid_eta = hybrid_out["predicted_eta_minutes"]
                prediction_spread = hybrid_out.get("prediction_spread_minutes")

                if selected_model == "BASELINE":
                    baseline_selected_count += 1
                else:
                    context_selected_count += 1

                actual_time = sim_res.get("simulated_actual_minutes")
                if actual_time is not None and hybrid_eta is not None:
                    hybrid_error = round(abs(hybrid_eta - actual_time), 2)

            run_record = {
                "scenario_key": scenario_key,
                "scenario_name": sim_res.get("scenario_name", scenario_key),
                "seed": seed,
                "route_id": rc["route_id"],
                "distance_km": rc["distance_km"],
                "is_safe": is_safe,
                "status": sim_res.get("status", "COMPLETED"),
                "parameters": sim_res.get("parameters", {}),
                "baseline_eta_minutes": sim_res.get("baseline_eta_minutes"),
                "context_aware_eta_minutes": sim_res.get("context_aware_eta_minutes"),
                "hybrid_eta_minutes": hybrid_eta,
                "selected_model": selected_model,
                "selection_reason": selection_reason,
                "prediction_spread_minutes": prediction_spread,
                "actual_travel_minutes": sim_res.get("simulated_actual_minutes"),
                "baseline_error_minutes": sim_res.get("baseline_error_minutes"),
                "context_aware_error_minutes": sim_res.get("context_aware_error_minutes"),
                "hybrid_error_minutes": hybrid_error,
                "improvement_pct": sim_res.get("improvement_pct"),
                "constraint_violation": sim_res.get("constraint_violation"),
                "safety_message": sim_res.get("safety_message"),
            }
            runs.append(run_record)

        # Separate safe runs for metric calculation (Unsafe runs must NOT be counted as efficient)
        valid_runs = [r for r in runs if r["is_safe"] and r["actual_travel_minutes"] is not None]

        if valid_runs:
            y_actual = [r["actual_travel_minutes"] for r in valid_runs]
            y_baseline = [r["baseline_eta_minutes"] for r in valid_runs]
            y_context = [r["context_aware_eta_minutes"] for r in valid_runs]
            y_hybrid = [r["hybrid_eta_minutes"] for r in valid_runs]

            b_metrics = calculate_metrics(y_actual, y_baseline, tolerance_minutes=10.0)
            c_metrics = calculate_metrics(y_actual, y_context, tolerance_minutes=10.0)
            h_metrics = calculate_metrics(y_actual, y_hybrid, tolerance_minutes=10.0)

            # ±15 min tolerance metrics
            b_metrics_15 = calculate_metrics(y_actual, y_baseline, tolerance_minutes=15.0)
            c_metrics_15 = calculate_metrics(y_actual, y_context, tolerance_minutes=15.0)
            h_metrics_15 = calculate_metrics(y_actual, y_hybrid, tolerance_minutes=15.0)

            b_metrics["within_15min_pct"] = b_metrics_15["within_tolerance_pct"]
            c_metrics["within_15min_pct"] = c_metrics_15["within_tolerance_pct"]
            h_metrics["within_15min_pct"] = h_metrics_15["within_tolerance_pct"]

            # Compute Improvements
            b_mae = b_metrics["mae"]
            c_mae = c_metrics["mae"]
            h_mae = h_metrics["mae"]

            b_rmse = b_metrics["rmse"]
            c_rmse = c_metrics["rmse"]
            h_rmse = h_metrics["rmse"]

            # Improvements
            mae_impr_context = round(((b_mae - c_mae) / b_mae * 100.0), 2) if b_mae > 0 else 0.0
            mae_impr_hybrid = round(((b_mae - h_mae) / b_mae * 100.0), 2) if b_mae > 0 else 0.0
            hybrid_vs_context_mae_impr = round(((c_mae - h_mae) / c_mae * 100.0), 2) if c_mae > 0 else 0.0

            rmse_impr_context = round(((b_rmse - c_rmse) / b_rmse * 100.0), 2) if b_rmse > 0 else 0.0
            rmse_impr_hybrid = round(((b_rmse - h_rmse) / b_rmse * 100.0), 2) if b_rmse > 0 else 0.0

            # Determine Empirical Winner strictly from measured MAE
            min_mae = min(b_mae, c_mae, h_mae)
            if abs(b_mae - min_mae) <= 0.5 and abs(c_mae - min_mae) <= 0.5 and abs(h_mae - min_mae) <= 0.5:
                winner = "TIE"
            elif min_mae == h_mae and abs(h_mae - min_mae) <= 0.01:
                # If hybrid ties with best model, identify if it strictly matched baseline or context
                if h_mae == b_mae and h_mae < c_mae:
                    winner = "HYBRID (BASELINE)"
                elif h_mae == c_mae and h_mae < b_mae:
                    winner = "HYBRID (CONTEXT)"
                else:
                    winner = "HYBRID"
            elif min_mae == c_mae:
                winner = "CONTEXT_AWARE"
            else:
                winner = "BASELINE"
        else:
            b_metrics = {"mae": 0.0, "rmse": 0.0, "mean_error": 0.0, "median_absolute_error": 0.0, "within_tolerance_pct": 0.0, "within_15min_pct": 0.0}
            c_metrics = {"mae": 0.0, "rmse": 0.0, "mean_error": 0.0, "median_absolute_error": 0.0, "within_tolerance_pct": 0.0, "within_15min_pct": 0.0}
            h_metrics = {"mae": 0.0, "rmse": 0.0, "mean_error": 0.0, "median_absolute_error": 0.0, "within_tolerance_pct": 0.0, "within_15min_pct": 0.0}
            mae_impr_context = 0.0
            mae_impr_hybrid = 0.0
            hybrid_vs_context_mae_impr = 0.0
            rmse_impr_context = 0.0
            rmse_impr_hybrid = 0.0
            winner = "UNSAFE"

        # Calculate selection rates
        total_valid = len(valid_runs)
        baseline_selection_rate = round((baseline_selected_count / total_valid * 100.0), 2) if total_valid > 0 else 0.0
        context_selection_rate = round((context_selected_count / total_valid * 100.0), 2) if total_valid > 0 else 0.0

        # Failure Analysis
        failure_summary = analyze_failures(runs, tolerance_minutes=10.0)

        # Database persistence
        experiment_id = None
        if persist_to_db:
            try:
                sc_entity = db.query(Scenario).filter(Scenario.scenario_name.ilike(f"%{scenario_key}%")).first()
                sc_id = sc_entity.id if sc_entity else 1

                exp = Experiment(
                    experiment_name=f"Phase 5 Benchmark: {scenario_key} ({repetitions} Reps)",
                    description=f"Automated evaluation of Baseline vs Context-Aware vs Adaptive Hybrid across {repetitions} seeds.",
                    scenario_id=sc_id,
                    started_at=datetime.datetime.utcnow(),
                    completed_at=datetime.datetime.utcnow(),
                    status="COMPLETED" if winner != "UNSAFE" else "UNSAFE_REJECTED",
                )
                db.add(exp)
                db.flush()
                experiment_id = exp.id

                if valid_runs:
                    res_base = ExperimentResult(
                        experiment_id=exp.id,
                        model_type="BASELINE",
                        mae=b_metrics["mae"],
                        rmse=b_metrics["rmse"],
                        mean_error=b_metrics["mean_error"],
                        median_error=b_metrics["median_absolute_error"],
                        within_tolerance_percent=b_metrics["within_tolerance_pct"],
                        route_completion_minutes=round(float(np.mean([r["baseline_eta_minutes"] for r in valid_runs])), 2),
                    )
                    res_context = ExperimentResult(
                        experiment_id=exp.id,
                        model_type="CONTEXT_AWARE",
                        mae=c_metrics["mae"],
                        rmse=c_metrics["rmse"],
                        mean_error=c_metrics["mean_error"],
                        median_error=c_metrics["median_absolute_error"],
                        within_tolerance_percent=c_metrics["within_tolerance_pct"],
                        route_completion_minutes=round(float(np.mean([r["context_aware_eta_minutes"] for r in valid_runs])), 2),
                    )
                    res_hybrid = ExperimentResult(
                        experiment_id=exp.id,
                        model_type="HYBRID",
                        mae=h_metrics["mae"],
                        rmse=h_metrics["rmse"],
                        mean_error=h_metrics["mean_error"],
                        median_error=h_metrics["median_absolute_error"],
                        within_tolerance_percent=h_metrics["within_tolerance_pct"],
                        route_completion_minutes=round(float(np.mean([r["hybrid_eta_minutes"] for r in valid_runs])), 2),
                    )
                    db.add(res_base)
                    db.add(res_context)
                    db.add(res_hybrid)
                db.commit()
            except Exception as e:
                logger.error("Failed to persist experiment: %s", e)
                db.rollback()

        return {
            "experiment_id": experiment_id,
            "scenario_key": scenario_key,
            "scenario_name": STANDARD_SCENARIOS.get(scenario_key, {}).get("name", scenario_key),
            "repetitions": repetitions,
            "total_runs": len(runs),
            "safe_runs": safe_runs_count,
            "unsafe_runs": unsafe_runs_count,
            "winner": winner,
            "selection_rates": {
                "baseline_selected_pct": baseline_selection_rate,
                "context_aware_selected_pct": context_selection_rate,
            },
            "metrics": {
                "baseline": b_metrics,
                "context_aware": c_metrics,
                "hybrid": h_metrics,
                "mae_improvement_pct": mae_impr_hybrid,
                "rmse_improvement_pct": rmse_impr_hybrid,
                "context_mae_improvement_pct": mae_impr_context,
                "hybrid_vs_context_mae_impr_pct": hybrid_vs_context_mae_impr,
            },
            "safety_summary": {
                "total_assignments": len(runs),
                "safe_assignments": safe_runs_count,
                "unsafe_assignments": unsafe_runs_count,
                "capacity_violations": capacity_violations,
                "driver_workload_violations": workload_violations,
                "blocked_assignments": unsafe_runs_count,
            },
            "failure_summary": failure_summary,
            "runs": runs,
        }

    @staticmethod
    def run_full_suite_benchmark(
        db: Session,
        repetitions: int = 5,
        include_hybrid: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute comprehensive benchmark across all 6 standard scenarios for
        Baseline, Context-Aware, and Adaptive Hybrid models.
        """
        scenarios = ["NORMAL", "HEAVY_RAIN", "MAJOR_EVENT", "ROAD_CLOSURE", "HIGH_WASTE", "COMBINED_STRESS"]
        scenario_results = []
        all_runs = []

        total_safe_runs = 0
        total_unsafe_runs = 0

        for sc in scenarios:
            res = ExperimentService.run_scenario_experiment(
                scenario_key=sc,
                db=db,
                repetitions=repetitions,
                persist_to_db=True,
                include_hybrid=include_hybrid,
            )
            scenario_results.append(res)
            all_runs.extend(res.get("runs", []))
            total_safe_runs += res.get("safe_runs", 0)
            total_unsafe_runs += res.get("unsafe_runs", 0)

        # Global aggregate evaluation
        valid_all_runs = [r for r in all_runs if r["is_safe"] and r["actual_travel_minutes"] is not None]
        if valid_all_runs:
            y_actual = [r["actual_travel_minutes"] for r in valid_all_runs]
            y_base = [r["baseline_eta_minutes"] for r in valid_all_runs]
            y_ctx = [r["context_aware_eta_minutes"] for r in valid_all_runs]
            y_hyb = [r["hybrid_eta_minutes"] for r in valid_all_runs]

            global_b_metrics = calculate_metrics(y_actual, y_base, tolerance_minutes=10.0)
            global_c_metrics = calculate_metrics(y_actual, y_ctx, tolerance_minutes=10.0)
            global_h_metrics = calculate_metrics(y_actual, y_hyb, tolerance_minutes=10.0)

            global_b_metrics["within_15min_pct"] = calculate_metrics(y_actual, y_base, tolerance_minutes=15.0)["within_tolerance_pct"]
            global_c_metrics["within_15min_pct"] = calculate_metrics(y_actual, y_ctx, tolerance_minutes=15.0)["within_tolerance_pct"]
            global_h_metrics["within_15min_pct"] = calculate_metrics(y_actual, y_hyb, tolerance_minutes=15.0)["within_tolerance_pct"]

            b_mae = global_b_metrics["mae"]
            c_mae = global_c_metrics["mae"]
            h_mae = global_h_metrics["mae"]

            global_hybrid_vs_base_mae_impr = round(((b_mae - h_mae) / b_mae * 100.0), 2) if b_mae > 0 else 0.0
            global_hybrid_vs_ctx_mae_impr = round(((c_mae - h_mae) / c_mae * 100.0), 2) if c_mae > 0 else 0.0
            global_ctx_vs_base_mae_impr = round(((b_mae - c_mae) / b_mae * 100.0), 2) if b_mae > 0 else 0.0

            global_hybrid_vs_base_rmse_impr = round(((global_b_metrics["rmse"] - global_h_metrics["rmse"]) / global_b_metrics["rmse"] * 100.0), 2) if global_b_metrics["rmse"] > 0 else 0.0
        else:
            global_b_metrics = {"mae": 0.0, "rmse": 0.0, "mean_error": 0.0, "median_absolute_error": 0.0, "within_tolerance_pct": 0.0, "within_15min_pct": 0.0}
            global_c_metrics = {"mae": 0.0, "rmse": 0.0, "mean_error": 0.0, "median_absolute_error": 0.0, "within_tolerance_pct": 0.0, "within_15min_pct": 0.0}
            global_h_metrics = {"mae": 0.0, "rmse": 0.0, "mean_error": 0.0, "median_absolute_error": 0.0, "within_tolerance_pct": 0.0, "within_15min_pct": 0.0}
            global_hybrid_vs_base_mae_impr = 0.0
            global_hybrid_vs_ctx_mae_impr = 0.0
            global_ctx_vs_base_mae_impr = 0.0
            global_hybrid_vs_base_rmse_impr = 0.0

        failure_analysis = analyze_failures(all_runs, tolerance_minutes=10.0)
        worst_errors = get_top_worst_errors(all_runs, top_n=10)

        # Global Winner
        g_min_mae = min(global_b_metrics["mae"], global_c_metrics["mae"], global_h_metrics["mae"])
        if g_min_mae == global_h_metrics["mae"]:
            global_winner = "ADAPTIVE_HYBRID"
        elif g_min_mae == global_c_metrics["mae"]:
            global_winner = "CONTEXT_AWARE"
        else:
            global_winner = "BASELINE"

        return {
            "total_scenarios": len(scenarios),
            "total_experiment_runs": len(all_runs),
            "safe_runs_count": total_safe_runs,
            "unsafe_runs_count": total_unsafe_runs,
            "global_winner": global_winner,
            "global_metrics": {
                "baseline": global_b_metrics,
                "context_aware": global_c_metrics,
                "hybrid": global_h_metrics,
                "hybrid_vs_baseline_mae_impr_pct": global_hybrid_vs_base_mae_impr,
                "hybrid_vs_context_mae_impr_pct": global_hybrid_vs_ctx_mae_impr,
                "context_vs_baseline_mae_impr_pct": global_ctx_vs_base_mae_impr,
                "hybrid_vs_baseline_rmse_impr_pct": global_hybrid_vs_base_rmse_impr,
            },
            "scenario_breakdown": scenario_results,
            "failure_analysis": failure_analysis,
            "top_worst_errors": worst_errors,
            "synthetic_disclaimer": "Synthetic Dataset — Research Prototype. Models evaluated on simulated multi-variable stress testing.",
        }
