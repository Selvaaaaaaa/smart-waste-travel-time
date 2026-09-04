from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.db_service import DatabaseQueryService
from app.schemas.entities import WeatherListResponse, WeatherResponse

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", response_model=WeatherListResponse, summary="List weather observations")
def get_weather(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> WeatherListResponse:
    items, total, total_pages = DatabaseQueryService.get_weather(db, page, page_size)
    return WeatherListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=[WeatherResponse.model_validate(w) for w in items],
        is_demo=True,
    )
