from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.db_service import DatabaseQueryService
from app.schemas.entities import ObservationListResponse, ObservationResponse

router = APIRouter(prefix="/observations", tags=["Observations"])


@router.get("", response_model=ObservationListResponse, summary="List contextual travel time observations")
def get_observations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> ObservationListResponse:
    items, total, total_pages = DatabaseQueryService.get_observations(db, page, page_size)
    return ObservationListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=[ObservationResponse.model_validate(o) for o in items],
        is_demo=True,
    )
