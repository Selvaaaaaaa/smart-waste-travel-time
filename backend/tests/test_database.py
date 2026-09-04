from datetime import date, datetime
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.route import Route
from app.models.route_stop import RouteStop
from app.models.waste_collection import WasteCollection
from app.models.scenario import Scenario
from app.models.experiment import Experiment
from app.models.experiment_result import ExperimentResult


def test_vehicle_creation_and_query(db_session):
    vehicle = Vehicle(
        vehicle_code="V-TEST-99",
        vehicle_type="COMPACTOR_TEST",
        capacity_tons=11.5,
        status="AVAILABLE",
        active=True,
    )
    db_session.add(vehicle)
    db_session.commit()

    queried = db_session.query(Vehicle).filter_by(vehicle_code="V-TEST-99").first()
    assert queried is not None
    assert queried.capacity_tons == 11.5
    assert queried.status == "AVAILABLE"


def test_driver_creation_and_workload(db_session):
    driver = Driver(
        employee_code="EMP-TEST-99",
        name="Test Driver",
        max_work_minutes_per_shift=480,
        current_work_minutes=120,
        status="AVAILABLE",
        active=True,
    )
    db_session.add(driver)
    db_session.commit()

    queried = db_session.query(Driver).filter_by(employee_code="EMP-TEST-99").first()
    assert queried is not None
    assert queried.max_work_minutes_per_shift == 480
    assert queried.current_work_minutes == 120


def test_route_and_stops_relationship(db_session):
    route = Route(
        route_code="R-TEST-99",
        route_date=date.today(),
        total_distance_km=25.0,
        total_waste_tons=5.0,
        baseline_eta_minutes=60.0,
        status="SCHEDULED",
    )
    db_session.add(route)
    db_session.flush()

    stop1 = RouteStop(
        route_id=route.id,
        stop_sequence=1,
        latitude=40.7128,
        longitude=-74.0060,
        waste_tons=1.5,
        service_minutes=5.0,
        completed=False,
    )
    stop2 = RouteStop(
        route_id=route.id,
        stop_sequence=2,
        latitude=40.7180,
        longitude=-73.9980,
        waste_tons=3.5,
        service_minutes=8.0,
        completed=False,
    )
    db_session.add_all([stop1, stop2])
    db_session.commit()

    queried_route = db_session.query(Route).filter_by(route_code="R-TEST-99").first()
    assert len(queried_route.stops) == 2
    assert queried_route.stops[0].stop_sequence == 1
    assert queried_route.stops[1].stop_sequence == 2


def test_waste_collection_relationship(db_session):
    route = db_session.query(Route).first()
    wc = WasteCollection(
        route_id=route.id,
        collection_date=date.today(),
        waste_tons=2.4,
        waste_type="RECYCLABLE",
    )
    db_session.add(wc)
    db_session.commit()

    assert wc.id is not None
    assert wc.route.id == route.id


def test_scenario_and_experiment_relationship(db_session):
    scenario = db_session.query(Scenario).first()
    assert scenario is not None

    exp = Experiment(
        experiment_name="Integration Test Experiment",
        scenario_id=scenario.id,
        status="RUNNING",
    )
    db_session.add(exp)
    db_session.flush()

    res = ExperimentResult(
        experiment_id=exp.id,
        model_type="BASELINE",
        mae=5.0,
        rmse=7.0,
        mean_error=5.2,
        median_error=4.9,
        within_tolerance_percent=90.0,
        route_completion_minutes=50.0,
    )
    db_session.add(res)
    db_session.commit()

    queried_exp = db_session.query(Experiment).filter_by(id=exp.id).first()
    assert len(queried_exp.results) == 1
    assert queried_exp.scenario.id == scenario.id
