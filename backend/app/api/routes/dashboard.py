from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary, summary="Dashboard KPI & Analytics Summary")
def get_dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    """Retrieve operational KPIs, conditions, and analytics metrics from database."""
    return DashboardService.get_dashboard_summary(db)
