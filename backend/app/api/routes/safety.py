from typing import Optional
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.safety_service import SafetyService
from app.schemas.entities import SafetyCheckResponse

router = APIRouter(prefix="/safety", tags=["Safety Constraints"])


@router.post("/validate-capacity", response_model=SafetyCheckResponse, summary="Validate vehicle payload capacity")
def validate_capacity(
    vehicle_id: int = Body(..., embed=True),
    assigned_waste_tons: float = Body(..., embed=True),
    db: Session = Depends(get_db),
) -> SafetyCheckResponse:
    res = SafetyService.validate_vehicle_capacity(vehicle_id, assigned_waste_tons, db)
    return SafetyCheckResponse(
        is_valid=res.is_valid,
        message=res.message,
        violation_type=res.violation_type,
    )


@router.post("/validate-workload", response_model=SafetyCheckResponse, summary="Validate driver workload limit")
def validate_workload(
    driver_id: int = Body(..., embed=True),
    additional_minutes: int = Body(..., embed=True),
    db: Session = Depends(get_db),
) -> SafetyCheckResponse:
    res = SafetyService.validate_driver_workload(driver_id, additional_minutes, db)
    return SafetyCheckResponse(
        is_valid=res.is_valid,
        message=res.message,
        violation_type=res.violation_type,
    )


@router.post("/validate-assignment", response_model=SafetyCheckResponse, summary="Validate vehicle and driver route assignment")
def validate_assignment(
    vehicle_id: int = Body(..., embed=True),
    driver_id: int = Body(..., embed=True),
    route_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
) -> SafetyCheckResponse:
    res = SafetyService.validate_route_assignment(route_id, vehicle_id, driver_id, db)
    return SafetyCheckResponse(
        is_valid=res.is_valid,
        message=res.message,
        violation_type=res.violation_type,
    )
