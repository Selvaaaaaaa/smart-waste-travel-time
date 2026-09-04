from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.db_service import DatabaseQueryService
from app.schemas.entities import EventListResponse, EventResponse

router = APIRouter(prefix="/events", tags=["Events"])


@router.get("", response_model=EventListResponse, summary="List municipal events & street impact")
def get_events(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> EventListResponse:
    items, total, total_pages = DatabaseQueryService.get_events(db, page, page_size)
    return EventListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=[EventResponse.model_validate(e) for e in items],
        is_demo=True,
    )
