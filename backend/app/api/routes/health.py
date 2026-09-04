from fastapi import APIRouter
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


from app.core.config import settings


@router.get("/health", response_model=HealthResponse, summary="System Health & Phase Status")
def get_health() -> HealthResponse:
    """Return backend operational status, service name, and active project phase."""
    return HealthResponse(
        status="ok",
        service="smart-waste-travel-time-api",
        phase=settings.PHASE,
    )
