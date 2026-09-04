from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.db_service import DatabaseQueryService
from app.schemas.entities import RoadRestrictionListResponse, RoadRestrictionResponse

router = APIRouter(prefix="/road-restrictions", tags=["Road Restrictions"])


@router.get("", response_model=RoadRestrictionListResponse, summary="List road restrictions & lane closures")
def get_road_restrictions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> RoadRestrictionListResponse:
    items, total, total_pages = DatabaseQueryService.get_road_restrictions(db, page, page_size)
    return RoadRestrictionListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=[RoadRestrictionResponse.model_validate(r) for r in items],
        is_demo=True,
    )
