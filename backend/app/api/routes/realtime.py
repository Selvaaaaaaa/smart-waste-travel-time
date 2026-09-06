"""Real-Time fused operational state, depots, and audit API routes."""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, Depends
from app.schemas.telemetry import (
    RealtimeOperationalState,
    DepotInfo,
    AuditEvent,
    AuthUser,
)
from app.telemetry.service import telemetry_service
from app.telemetry.depots import depot_service
from app.telemetry.audit import audit_service
from app.telemetry.auth import get_current_user

router = APIRouter(prefix="/realtime", tags=["Real-Time Operations & Fusion"])


@router.get("/fleet", response_model=RealtimeOperationalState)
def get_fused_fleet_state(
    weather: str = Query("CLEAR"),
    traffic: str = Query("NORMAL"),
):
    """Return live fused operational state combining vehicle GPS, bin fill, route deviations, and ETA."""
    return telemetry_service.fusion.get_fused_operational_state(weather=weather, traffic=traffic)


@router.get("/depots", response_model=List[DepotInfo])
def get_depots():
    """Return all registered municipal dispatch depots and assigned fleet counts."""
    return depot_service.get_all_depots()


@router.get("/audit", response_model=List[AuditEvent])
def get_audit_log(
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
):
    """Return operational and security audit log events for municipal oversight."""
    return audit_service.get_events(limit=limit, action=action, entity_type=entity_type)
