from app.services.safety_service import SafetyService
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.route import Route


def test_vehicle_capacity_validation_within_limit(db_session):
    vehicle = db_session.query(Vehicle).filter(Vehicle.capacity_tons >= 10.0, Vehicle.status == "AVAILABLE").first()
    assert vehicle is not None

    result = SafetyService.validate_vehicle_capacity(vehicle.id, assigned_waste_tons=6.5, db=db_session)
    assert result.is_valid is True


def test_vehicle_capacity_validation_overload_violation(db_session):
    vehicle = db_session.query(Vehicle).filter(Vehicle.capacity_tons <= 10.0).first()
    assert vehicle is not None

    # Overload by assigning 25 tons to a <=10 ton vehicle
    result = SafetyService.validate_vehicle_capacity(vehicle.id, assigned_waste_tons=25.0, db=db_session)
    assert result.is_valid is False
    assert result.violation_type == "PAYLOAD_CAPACITY_EXCEEDED"
    assert "CRITICAL SAFETY VIOLATION" in result.message


def test_vehicle_capacity_negative_payload(db_session):
    vehicle = db_session.query(Vehicle).first()
    result = SafetyService.validate_vehicle_capacity(vehicle.id, assigned_waste_tons=-3.0, db=db_session)
    assert result.is_valid is False
    assert result.violation_type == "NEGATIVE_PAYLOAD"


def test_driver_workload_validation_within_limit(db_session):
    driver = db_session.query(Driver).filter(Driver.current_work_minutes <= 200, Driver.status == "AVAILABLE").first()
    if not driver:
        driver = db_session.query(Driver).filter(Driver.active == True).first()
        driver.current_work_minutes = 100
        driver.status = "AVAILABLE"
        db_session.commit()

    result = SafetyService.validate_driver_workload(driver.id, additional_minutes=60, db=db_session)
    assert result.is_valid is True


def test_driver_workload_validation_fatigue_limit_exceeded(db_session):
    driver = db_session.query(Driver).first()
    driver.current_work_minutes = 450
    driver.max_work_minutes_per_shift = 480
    db_session.commit()

    # Adding 60 min -> 510 min > 480 min limit
    result = SafetyService.validate_driver_workload(driver.id, additional_minutes=60, db=db_session)
    assert result.is_valid is False
    assert result.violation_type == "WORKLOAD_LIMIT_EXCEEDED"
    assert "CRITICAL LABOR SAFETY VIOLATION" in result.message


def test_route_assignment_validation(db_session):
    vehicle = db_session.query(Vehicle).filter(Vehicle.active == True, Vehicle.status == "AVAILABLE").first()
    driver = db_session.query(Driver).filter(Driver.active == True, Driver.status == "AVAILABLE").first()
    route = db_session.query(Route).first()

    result = SafetyService.validate_route_assignment(route.id, vehicle.id, driver.id, db=db_session)
    assert result.is_valid is True
