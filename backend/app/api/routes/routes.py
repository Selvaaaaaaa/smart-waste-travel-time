from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.routes import RouteListResponse
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])


@router.get("", response_model=RouteListResponse, summary="Collection Routes List")
def get_routes(
    status: Optional[str] = Query(None, description="Filter by route status (On Schedule, Delayed, At Risk)"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    search: Optional[str] = Query(None, description="Search by route ID, driver name, or vehicle"),
    db: Session = Depends(get_db),
) -> RouteListResponse:
    """Retrieve collection routes list from PostgreSQL with synthetic operational details."""
    return RouteService.get_routes(db=db, status=status, vehicle_id=vehicle_id, query=search)
