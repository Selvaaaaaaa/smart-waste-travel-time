from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.db_service import DatabaseQueryService
from app.schemas.entities import VehicleListResponse, VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.get("", response_model=VehicleListResponse, summary="List fleet vehicles")
def get_vehicles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status (AVAILABLE, IN_SERVICE, MAINTENANCE)"),
    db: Session = Depends(get_db),
) -> VehicleListResponse:
    items, total, total_pages = DatabaseQueryService.get_vehicles(db, page, page_size, status)
    return VehicleListResponse(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
        items=[VehicleResponse.model_validate(v) for v in items],
        is_demo=True,
    )
