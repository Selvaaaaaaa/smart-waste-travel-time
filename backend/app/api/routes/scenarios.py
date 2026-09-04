from typing import Dict, Any, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.scenarios import ScenarioOptionsResponse
from app.schemas.entities import ScenarioListResponse, ScenarioResponse
from app.schemas.ml import ScenarioRunRequest, ScenarioRunResponse
from app.services.scenario_service import ScenarioService
from app.services.db_service import DatabaseQueryService
from app.services.scenario_engine import ScenarioEngine, STANDARD_SCENARIOS

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.get("/options", response_model=ScenarioOptionsResponse, summary="Simulation Scenario Options")
def get_scenario_options() -> ScenarioOptionsResponse:
    """Retrieve available environmental, traffic, event, and workload simulation parameters."""
    return ScenarioService.get_scenario_options()


@router.get("/presets", summary="Get standard predefined operational scenarios")
def get_scenario_presets() -> List[Dict[str, Any]]:
    """Return dictionary of the 6 standard operational stress scenarios."""
    presets = []
    for key, sc in STANDARD_SCENARIOS.items():
        presets.append({
            "key": key,
            **sc
        })
    return presets


@router.post("/run", response_model=ScenarioRunResponse, summary="Execute Scenario Simulation")
def run_scenario_endpoint(
    req: ScenarioRunRequest,
    db: Session = Depends(get_db),
) -> ScenarioRunResponse:
    """
    Execute simulation under defined environmental, traffic, event, and waste volume stressors.
    Integrates safety validation, deterministic baseline ETA, and context-aware ML prediction.
    """
    engine = ScenarioEngine(random_seed=42)
    try:
        res = engine.run_scenario(
            scenario_key_or_params=req.model_dump(exclude_unset=True),
            db=db,
            route_id=req.route_id,
            vehicle_id=req.vehicle_id,
            driver_id=req.driver_id,
            persist_predictions=True,
        )
        return ScenarioRunResponse(**res)
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(re),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario execution failed: {str(e)}",
        )


@router.get("", response_model=ScenarioListResponse, summary="List predefined simulation scenarios")
def get_scenarios(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ScenarioListResponse:
    """Retrieve scenarios with pagination from database."""
    items, total, total_pages = DatabaseQueryService.get_scenarios(db, page, page_size)
    return ScenarioListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=[ScenarioResponse.model_validate(s) for s in items],
        is_demo=False,
    )
