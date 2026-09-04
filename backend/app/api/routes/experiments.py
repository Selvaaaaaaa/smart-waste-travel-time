import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.db_service import DatabaseQueryService
from app.services.experiment_service import ExperimentService
from app.schemas.entities import ExperimentListResponse, ExperimentResponse, ExperimentResultResponse
from app.schemas.experiments import (
    ExperimentRunRequest,
    ExperimentBenchmarkResponse,
    FailureAnalysisResponse,
    TopWorstErrorsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.post("/run", summary="Run Controlled Experiment Benchmark")
def run_experiment(
    req: ExperimentRunRequest,
    db: Session = Depends(get_db),
):
    """
    Execute controlled deterministic experiment runs across scenarios.
    Computes Baseline vs Context-Aware error distributions and captures failure cases.
    """
    try:
        if req.scenario_key.upper() == "ALL":
            return ExperimentService.run_full_suite_benchmark(db=db, repetitions=req.repetitions)
        else:
            return ExperimentService.run_scenario_experiment(
                scenario_key=req.scenario_key,
                db=db,
                repetitions=req.repetitions,
                persist_to_db=True,
            )
    except Exception as e:
        logger.exception("Experiment execution failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment execution error: {str(e)}",
        )


@router.get("/results", summary="Get Aggregated Benchmark Results")
def get_benchmark_results(
    repetitions: int = Query(5, ge=1, le=20, description="Repetition count for benchmark"),
    db: Session = Depends(get_db),
):
    """Retrieve full suite benchmark results with scenario breakdowns and failure analysis."""
    try:
        return ExperimentService.run_full_suite_benchmark(db=db, repetitions=repetitions)
    except Exception as e:
        logger.exception("Failed to retrieve benchmark results: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating benchmark results: {str(e)}",
        )


@router.get("/failures", summary="Get Detected Failure Cases")
def get_failure_cases(
    repetitions: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Retrieve categorized failure cases from multi-scenario evaluation."""
    benchmark = ExperimentService.run_full_suite_benchmark(db=db, repetitions=repetitions)
    return benchmark["failure_analysis"]


@router.get("/comparison", summary="Get Model Win/Loss Comparison Summary")
def get_model_comparison(
    repetitions: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Return scenario-by-scenario winner analysis and improvement metrics."""
    benchmark = ExperimentService.run_full_suite_benchmark(db=db, repetitions=repetitions)
    table = []
    for sc in benchmark["scenario_breakdown"]:
        table.append({
            "scenario": sc["scenario_name"],
            "scenario_key": sc["scenario_key"],
            "baseline_mae": sc["metrics"]["baseline"]["mae"],
            "context_mae": sc["metrics"]["context_aware"]["mae"],
            "hybrid_mae": sc["metrics"]["hybrid"]["mae"],
            "baseline_rmse": sc["metrics"]["baseline"]["rmse"],
            "context_rmse": sc["metrics"]["context_aware"]["rmse"],
            "hybrid_rmse": sc["metrics"]["hybrid"]["rmse"],
            "mae_improvement_pct": sc["metrics"]["mae_improvement_pct"],
            "winner": sc["winner"],
            "selection_rates": sc.get("selection_rates", {}),
            "safety_status": "SAFE" if sc["unsafe_runs"] == 0 else "UNSAFE_REJECTED",
        })

    return {
        "global_metrics": benchmark["global_metrics"],
        "comparison_table": table,
        "global_winner": benchmark.get("global_winner"),
        "safe_runs": benchmark["safe_runs_count"],
        "unsafe_runs": benchmark["unsafe_runs_count"],
        "total_runs": benchmark["total_experiment_runs"],
    }


@router.get("/{experiment_id}", summary="Get Specific Experiment by ID")
def get_experiment_by_id(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve single experiment details and stored model results."""
    from app.models.experiment import Experiment
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experiment with ID {experiment_id} not found.",
        )

    res_list = [ExperimentResultResponse.model_validate(r) for r in exp.results]
    return {
        "id": exp.id,
        "experiment_name": exp.experiment_name,
        "description": exp.description,
        "scenario_id": exp.scenario_id,
        "started_at": exp.started_at,
        "completed_at": exp.completed_at,
        "status": exp.status,
        "results": res_list,
        "created_at": exp.created_at,
    }


@router.get("", response_model=ExperimentListResponse, summary="List simulation experiments from database")
def get_experiments(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ExperimentListResponse:
    """Retrieve experiments with pagination from database."""
    items, total, total_pages = DatabaseQueryService.get_experiments(db, page, page_size)

    exp_responses = []
    for exp in items:
        res_list = [ExperimentResultResponse.model_validate(r) for r in exp.results]
        exp_dict = {
            "id": exp.id,
            "experiment_name": exp.experiment_name,
            "description": exp.description,
            "scenario_id": exp.scenario_id,
            "started_at": exp.started_at,
            "completed_at": exp.completed_at,
            "status": exp.status,
            "results": res_list,
            "created_at": exp.created_at,
        }
        exp_responses.append(ExperimentResponse.model_validate(exp_dict))

    return ExperimentListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=exp_responses,
        is_demo=False,
    )
