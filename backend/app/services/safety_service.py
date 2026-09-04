from typing import Tuple, Optional
from sqlalchemy.orm import Session
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.route import Route


class SafetyConstraintViolation(Exception):
    """Exception raised when a logistical operation violates physical or labor safety bounds."""
    def __init__(self, message: str, violation_type: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.violation_type = violation_type
        self.details = details or {}


class SafetyValidationResult:
    def __init__(self, is_valid: bool, message: str = "Safety validation passed", violation_type: Optional[str] = None):
        self.is_valid = is_valid
        self.message = message
        self.violation_type = violation_type

    def __bool__(self):
        return self.is_valid


class SafetyService:
    """
    Safety constraint enforcement service.
    Validates physical payload capacities, driver fatigue limits, and operational assignments.
    """

    @staticmethod
    def validate_vehicle_capacity(vehicle_id: int, assigned_waste_tons: float, db: Session) -> SafetyValidationResult:
        """
        Validate that assigned total waste tonnage does not exceed vehicle rated gross capacity.
        Overloading vehicles violates municipal transport safety laws.
        """
        if assigned_waste_tons < 0:
            return SafetyValidationResult(
                is_valid=False,
                message=f"Assigned waste tonnage cannot be negative ({assigned_waste_tons} tons).",
                violation_type="NEGATIVE_PAYLOAD",
            )

        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            return SafetyValidationResult(
                is_valid=False,
                message=f"Vehicle with ID {vehicle_id} does not exist.",
                violation_type="VEHICLE_NOT_FOUND",
            )

        if not vehicle.active or vehicle.status in ["MAINTENANCE", "UNAVAILABLE"]:
            return SafetyValidationResult(
                is_valid=False,
                message=f"Vehicle {vehicle.vehicle_code} is inactive or under maintenance (status: {vehicle.status}).",
                violation_type="VEHICLE_UNAVAILABLE",
            )

        if assigned_waste_tons > vehicle.capacity_tons:
            return SafetyValidationResult(
                is_valid=False,
                message=(
                    f"CRITICAL SAFETY VIOLATION: Assigned waste payload ({assigned_waste_tons:.2f} tons) "
                    f"exceeds maximum rated capacity ({vehicle.capacity_tons:.2f} tons) for vehicle {vehicle.vehicle_code}."
                ),
                violation_type="PAYLOAD_CAPACITY_EXCEEDED",
            )

        return SafetyValidationResult(is_valid=True)

    @staticmethod
    def validate_driver_workload(driver_id: int, additional_minutes: int, db: Session) -> SafetyValidationResult:
        """
        Validate that additional route time does not breach driver consecutive shift fatigue bounds.
        """
        if additional_minutes < 0:
            return SafetyValidationResult(
                is_valid=False,
                message=f"Additional work duration cannot be negative ({additional_minutes} min).",
                violation_type="NEGATIVE_DURATION",
            )

        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver:
            return SafetyValidationResult(
                is_valid=False,
                message=f"Driver with ID {driver_id} does not exist.",
                violation_type="DRIVER_NOT_FOUND",
            )

        if not driver.active or driver.status == "OFF_DUTY":
            return SafetyValidationResult(
                is_valid=False,
                message=f"Driver {driver.name} ({driver.employee_code}) is off-duty or inactive.",
                violation_type="DRIVER_OFF_DUTY",
            )

        projected_minutes = driver.current_work_minutes + additional_minutes
        if projected_minutes > driver.max_work_minutes_per_shift:
            return SafetyValidationResult(
                is_valid=False,
                message=(
                    f"CRITICAL LABOR SAFETY VIOLATION: Projected shift duration ({projected_minutes} min) "
                    f"exceeds maximum allowed shift limit ({driver.max_work_minutes_per_shift} min) for driver {driver.name}."
                ),
                violation_type="WORKLOAD_LIMIT_EXCEEDED",
            )

        return SafetyValidationResult(is_valid=True)

    @staticmethod
    def validate_route_assignment(
        route_id: Optional[int],
        vehicle_id: int,
        driver_id: int,
        db: Session,
    ) -> SafetyValidationResult:
        """
        Validate concurrent assignment of vehicle and driver for a specific route.
        """
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle or not vehicle.active:
            return SafetyValidationResult(
                is_valid=False,
                message=f"Cannot assign inactive or non-existent vehicle ID {vehicle_id}.",
                violation_type="INVALID_VEHICLE",
            )

        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if not driver or not driver.active:
            return SafetyValidationResult(
                is_valid=False,
                message=f"Cannot assign inactive or non-existent driver ID {driver_id}.",
                violation_type="INVALID_DRIVER",
            )

        # Check route waste vs vehicle capacity if route exists
        if route_id:
            route = db.query(Route).filter(Route.id == route_id).first()
            if route and route.total_waste_tons > 0:
                cap_res = SafetyService.validate_vehicle_capacity(vehicle_id, route.total_waste_tons, db)
                if not cap_res.is_valid:
                    return cap_res

            if route and route.baseline_eta_minutes > 0:
                work_res = SafetyService.validate_driver_workload(driver_id, int(route.baseline_eta_minutes), db)
                if not work_res.is_valid:
                    return work_res

        return SafetyValidationResult(is_valid=True)
