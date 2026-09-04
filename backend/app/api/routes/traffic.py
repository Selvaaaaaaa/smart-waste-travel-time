from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.db_service import DatabaseQueryService
from app.schemas.entities import TrafficListResponse, TrafficResponse

router = APIRouter(prefix="/traffic", tags=["Traffic"])


@router.get("", response_model=TrafficListResponse, summary="List traffic condition records")
def get_traffic(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> TrafficListResponse:
    items, total, total_pages = DatabaseQueryService.get_traffic(db, page, page_size)
    return TrafficListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=[TrafficResponse.model_validate(t) for t in items],
        is_demo=True,
    )
